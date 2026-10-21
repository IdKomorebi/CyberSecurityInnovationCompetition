# -*- coding: utf-8 -*-
"""闭式读出估计器：遮挡预训练主干 + 逐组合闭式岭回归读出。

来源：GNN_Aggresvation 122/125 号的估计器（重建预训练主干、逐集合闭式岭读出、三道数值防护）。
本系统做了两处精简，隔离实验（社区统计 3808 个组合、NEM 与 PJM 各 1200 个组合，真值为逐个重新训练）表明精度不降、耗时降三个数量级：
  1. 单个种子的主干（原为 3 个种子预测平均）；
  2. 岭参数 λ 在训练行内部用 64 个随机组合一次选定（原为每个组合 5 折交叉验证选 λ）。
做法：
  主干 g(x⊙m, m)：3 层 256 维全连接网络，训练时随机遮挡字段，输出 = 保护对象 + 全部候选列；
        损失 = 保护对象的均方误差 + 被遮住候选列的重建误差（防止只预测保护对象时隐层塌缩到一两个方向）。
  读出：对组合 S，特征 = [x⊙m_S, (x⊙m_S)², φ(x⊙m_S, m_S)]，φ 为主干最后一层激活；在训练行上做岭回归，在留出行上算决定系数。
  三道数值防护：特征标准差下限 1e-3；留出行特征截断到训练行取值范围；预测截断到训练行保护对象的取值范围。
接口与 fast.Fast 的 estimate / estimate_sel 相同，返回各输出分量的决定系数。"""
import numpy as np, torch, torch.nn as nn


class Backbone(nn.Module):
    def __init__(self, p, out, h=256):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(2 * p, h), nn.ReLU(), nn.Dropout(.1), nn.Linear(h, h), nn.ReLU(), nn.Dropout(.1),
                                 nn.Linear(h, h), nn.ReLU(), nn.Dropout(.1), nn.Linear(h, out))

    def forward(self, x, m):
        return self.net(torch.cat([x * m, m], 1))

    @torch.no_grad()
    def phi(self, X, M):
        """X (行数, p)，M (B, p) → 最后一层激活 (B, 行数, 256)。"""
        B, k = M.shape[0], X.shape[0]
        h = torch.cat([X.unsqueeze(0) * M.unsqueeze(1), M.unsqueeze(1).expand(-1, k, -1)], 2).reshape(B * k, -1)
        for i, layer in enumerate(self.net):
            h = layer(h)
            if i == 7:
                break
        return h.reshape(B, k, -1)


class Readout:
    """字段按“项”组织：groups[i] 是第 i 个候选字段占用的列；公开基底 Xb 始终可见。"""
    ALPHAS = (0.1, 1.0, 10.0, 100.0, 1000.0)

    def __init__(self, Xb, Xc, Y, groups, tr, te, device="cuda:0", seed=0, epochs=400, patience=60, batch=256, state=None):
        self.dev, self.n, self.groups = device, len(groups), [list(g) for g in groups]
        X = np.hstack([Xc, Xb]).astype(np.float32); nb = Xb.shape[1]; p = X.shape[1]; C = Y.shape[1]
        std = lambda a: (a - a[tr].mean(0)) / (a[tr].std(0) + 1e-8)
        Xs, Ys = std(X), std(Y.astype(np.float32))
        T = lambda a: torch.tensor(a, dtype=torch.float32, device=device)
        self.Xtr, self.Xte, self.Ytr, self.Yte = T(Xs[tr]), T(Xs[te]), T(Ys[tr]), T(Ys[te])
        self.E = torch.zeros(self.n, p, device=device)                         # 字段 → 列
        for g, cols in enumerate(self.groups):
            self.E[g, cols] = 1
        self.base = torch.zeros(p, device=device); self.base[Xc.shape[1]:] = 1   # 公开基底列始终可见
        self.net = Backbone(p, C + p).to(device)
        if state is not None:
            self.net.load_state_dict(state["net"]); self.alpha = state["alpha"]
        else:
            self._train(seed, epochs, patience, batch, C); self.alpha = self._pick_alpha()
        self.net.eval(); self.sst = ((self.Yte - self.Yte.mean(0)) ** 2).sum(0)
        self.chunk = int(max(1, min(32, 1.2e8 // ((len(self.Xtr) + len(self.Xte)) * (2 * p + 256)))))   # 每批组合数：按行数与特征维度控制显存

    def state(self):
        return dict(net=self.net.state_dict(), alpha=self.alpha)

    def _mask(self, b, rng):
        """先抽可见字段数 k ~ U{1..n}，再均匀抽 k 个字段。"""
        sel = np.zeros((b, self.n), np.float32)
        for i, k in enumerate(rng.randint(1, self.n + 1, b)):
            sel[i, rng.choice(self.n, k, replace=False)] = 1
        return torch.tensor(sel, device=self.dev) @ self.E + self.base

    def _train(self, seed, epochs, patience, bs, C):
        torch.manual_seed(seed); md = self.net; opt = torch.optim.Adam(md.parameters(), lr=1e-3, weight_decay=5e-4)
        k = len(self.Xtr); pr = np.random.RandomState(7).permutation(k); nv = round(k * .15); fit, val = pr[nv:], pr[:nv]
        rng, vr = np.random.RandomState(1234 + seed), np.random.RandomState(999); vms = [self._mask(len(val), vr) for _ in range(8)]
        best, bst, pat = 1e9, None, 0
        for ep in range(epochs):
            md.train(); o = fit[np.random.RandomState(seed * 1000 + ep).permutation(len(fit))]
            for b in range(0, len(o), bs):
                ix = torch.tensor(o[b:b + bs], device=self.dev); m = self._mask(len(ix), rng); out = md(self.Xtr[ix], m); h = 1 - m
                loss = ((out[:, :C] - self.Ytr[ix]) ** 2).mean() + (((out[:, C:] - self.Xtr[ix]) ** 2) * h).sum() / h.sum().clamp_min(1)
                opt.zero_grad(); loss.backward(); opt.step()
            md.eval()
            with torch.no_grad():
                v = float(np.mean([((md(self.Xtr[val], mm)[:, :C] - self.Ytr[val]) ** 2).mean().item() for mm in vms]))
            if v < best - 1e-6:
                best, bst, pat = v, {kk: x.clone() for kk, x in md.state_dict().items()}, 0
            else:
                pat += 1
                if pat >= patience:
                    break
        md.load_state_dict(bst)

    @torch.no_grad()
    def _feats(self, X, M):
        xm = X.unsqueeze(0) * M.unsqueeze(1)
        return torch.cat([xm, xm ** 2, self.net.phi(X, M)], 2)

    @torch.no_grad()
    def _pick_alpha(self):
        """在训练行内部留出 20%，用 64 个 1 至 4 个字段的随机组合（与查询规模相近）选一个全局 λ（不使用留出行）。"""
        self.net.eval(); rng = np.random.RandomState(1); sel = np.zeros((64, self.n), np.float32)
        for i in range(64):
            sel[i, rng.choice(self.n, rng.randint(1, min(4, self.n) + 1), replace=False)] = 1
        M = torch.tensor(sel, device=self.dev) @ self.E + self.base; k = len(self.Xtr)
        pr = torch.randperm(k, generator=torch.Generator().manual_seed(0)).to(self.dev); nv = int(k * .2); vi, fi = pr[:nv], pr[nv:]
        score = []
        for al in self.ALPHAS:
            s = 0.0
            ch = int(max(1, min(16, 1.2e8 // (k * (self.Xtr.shape[1] * 2 + 256)))))
            for lo in range(0, 64, ch):
                F = self._feats(self.Xtr, M[lo:lo + ch]); mu = F.mean(1, keepdim=True); sd = F.std(1, keepdim=True).clamp_min(1e-3); T = (F - mu) / sd
                Tf, Tv = T[:, fi], T[:, vi]; d = T.shape[2]; ym = self.Ytr[fi].mean(0)
                beta = torch.linalg.solve(Tf.transpose(1, 2) @ Tf + al * len(fi) / 1000 * torch.eye(d, device=self.dev), Tf.transpose(1, 2) @ (self.Ytr[fi] - ym))
                r2 = 1 - ((Tv @ beta + ym - self.Ytr[vi].unsqueeze(0)) ** 2).sum(1) / ((self.Ytr[vi] - self.Ytr[vi].mean(0)) ** 2).sum(0)
                s += float(r2.mean())
            score.append(s)
        return self.ALPHAS[int(np.argmax(score))]

    @torch.no_grad()
    def _r2(self, M):
        Ftr, Fte = self._feats(self.Xtr, M), self._feats(self.Xte, M)
        mu = Ftr.mean(1, keepdim=True); sd = Ftr.std(1, keepdim=True).clamp_min(1e-3)                       # 防护一
        T, E = (Ftr - mu) / sd, (Fte - mu) / sd
        E = torch.minimum(torch.maximum(E, T.amin(1, keepdim=True)), T.amax(1, keepdim=True))              # 防护二
        k, d = T.shape[1], T.shape[2]; ym = self.Ytr.mean(0)
        beta = torch.linalg.solve(T.transpose(1, 2) @ T + self.alpha * k / 1000 * torch.eye(d, device=self.dev), T.transpose(1, 2) @ (self.Ytr - ym))
        pred = torch.minimum(torch.maximum(E @ beta + ym, self.Ytr.amin(0)), self.Ytr.amax(0))             # 防护三
        return (1 - ((pred - self.Yte.unsqueeze(0)) ** 2).sum(1) / self.sst).clamp(min=0)

    @torch.no_grad()
    def estimate(self, subsets, chunk=None):
        """各字段组合的估计推断精度 [组合数, 输出分量数]。"""
        out = []; chunk = chunk or self.chunk
        for lo in range(0, len(subsets), chunk):
            part = subsets[lo:lo + chunk]; sel = torch.zeros(len(part), self.n, device=self.dev)
            for r, s in enumerate(part):
                sel[r, list(s)] = 1
            out.append(self._r2(sel @ self.E + self.base).cpu().numpy())
        return np.vstack(out) if out else np.zeros((0, self.Ytr.shape[1]))

    @torch.no_grad()
    def estimate_sel(self, sel, chunk=None):
        """sel [B, 候选字段数]（1 表示可见）的张量，返回估计推断精度的张量 [B, 输出分量数]。"""
        chunk = chunk or self.chunk
        return torch.cat([self._r2(sel[lo:lo + chunk].float() @ self.E + self.base) for lo in range(0, sel.shape[0], chunk)])
