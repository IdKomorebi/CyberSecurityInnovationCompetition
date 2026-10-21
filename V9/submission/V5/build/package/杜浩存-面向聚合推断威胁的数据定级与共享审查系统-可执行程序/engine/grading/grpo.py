# -*- coding: utf-8 -*-
"""二次定级的联合评估：组相对策略优化（GRPO）。

每一步对同一个定级任务采样一组完整的等级方案，以组内相对优势更新策略，不需要另外训练价值网络。
综合效用 U = Σ 安全收益 + Σ 可用性成本 − 聚合推断惩罚，各项都是扣分，U ≤ 0，越接近 0 越好。
聚合推断惩罚按越线组合超出判定线的幅度计：刚过线的组合罚得轻，远超判定线的罚得重。
"""
import numpy as np, torch, torch.nn as nn

DEFAULT = dict(beta=2.5, lam=1.0, eta=1.0, sigma=0.5, rho=2.0, rho_w=2.0, steps=400, group=128)


def field_table(L1, Mmax, w, P):
    """每个字段取各等级时的安全收益与可用性成本，形状 [n, 4]。"""
    lv = np.arange(1, 5)[None, :]; d = lv - np.asarray(L1)[:, None]
    S = -P["beta"] * np.asarray(Mmax)[:, None] * np.exp(-P["lam"] * d); C = -P["eta"] * np.asarray(w)[:, None] * (np.exp(P["sigma"] * d) - 1)
    return S, C


def combo_weight(v, line, P):
    """一个越线组合的罚分：ρ × 超出判定线的幅度 / 0.1（至少按 0.02 计）。"""
    return P["rho"] * max(v - line, 0.02) / 0.1


def solve(L1, low, high, Mmax, w, cons, P, strict=False, seed=0, device="cpu", ent=0.2, lr=3e-3, whole=None):
    """cons: [(接收方等级 c, 组合字段元组, 罚分)]。返回等级方案与训练曲线。strict=True 时只接受没有越线组合的方案。"""
    torch.manual_seed(seed); n = len(L1); S, C = field_table(L1, Mmax, w, P)
    T = lambda a, dt=torch.float32: torch.tensor(np.asarray(a), dtype=dt, device=device)
    m = max([len(k) for _, k, _ in cons] + [1]); idx = np.full((len(cons), m), n, int)
    for r, (_, k, _) in enumerate(cons):
        idx[r, :len(k)] = sorted(k)
    St, Ct, it, ct, wt = T(S), T(C), T(idx, torch.long), T([c for c, _, _ in cons], torch.long), T([x for _, _, x in cons])
    cnt = np.zeros(n)
    for _, k, x in cons:
        for i in k:
            cnt[i] += x
    feat = T(np.stack([np.asarray(L1) / 4, np.asarray(low) / 4, np.asarray(Mmax), cnt / (cnt.max() + 1e-9), np.asarray(w)], 1))
    net = nn.Sequential(nn.Linear(5, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 4)).to(device); bias = nn.Parameter(torch.zeros(n, 4, device=device))
    opt = torch.optim.Adam(list(net.parameters()) + [bias], lr=lr); ar = torch.arange(n, device=device)
    lvl = torch.arange(1, 5, device=device)[None, :]; mask = (lvl >= T(low, torch.long)[:, None]) & (lvl <= T(high, torch.long)[:, None])

    def util(a):                                     # a [G, n]，取值 1..4
        u = (St[ar, a - 1] + Ct[ar, a - 1]).sum(1)
        if len(cons):
            pad = torch.cat([a, torch.zeros(len(a), 1, dtype=a.dtype, device=device)], 1); act = (pad[:, it].max(2).values <= ct[None, :]).float()
            u, na = u - (act * wt[None, :]).sum(1), act.sum(1)
        else:
            na = torch.zeros(len(a), device=device)
        if whole is not None:                        # 整体推断惩罚：各接收方合并全部可获取字段后的推断精度超出判定线的部分
            u = u - whole(a)
        return u, na

    steps, G = int(P.get("steps", 400)), int(P.get("group", 128)); best_u, best_a, curve = -1e18, None, []
    for step in range(steps):
        logits = (net(feat) + bias).masked_fill(~mask, -1e9); dist = torch.distributions.Categorical(logits=logits)
        a = dist.sample((G,)); u, act = util(a + 1)
        r = u - (1000.0 * act if strict else 0.0)                         # 严格模式下，有越线组合的方案一律判差
        adv = (r - r.mean()) / (r.std() + 1e-6)                           # 组内相对优势
        loss = -(adv[:, None] * dist.log_prob(a)).sum(1).mean() - ent * (1 - step / steps) * dist.entropy().mean()
        opt.zero_grad(); loss.backward(); opt.step()
        ok = (act == 0) if strict else torch.ones_like(act, dtype=torch.bool)
        if ok.any():
            j = int(torch.where(ok, u, torch.full_like(u, -1e18)).argmax())
            if float(u[j]) > best_u:
                best_u, best_a = float(u[j]), (a[j] + 1).tolist()
        if step % max(1, steps // 40) == 0:
            curve.append(dict(步=step, 组内平均=round(float(u.mean()), 3), 组内最好=round(float(u.max()), 3), 越线组合=round(float(act.mean()), 2)))
    with torch.no_grad():
        g = ((net(feat) + bias).masked_fill(~mask, -1e9).argmax(1) + 1)[None, :]; ug, ag = util(g)
    if (not strict or int(ag[0]) == 0) and float(ug[0]) > best_u:
        best_a = g[0].tolist()
    return best_a, curve
