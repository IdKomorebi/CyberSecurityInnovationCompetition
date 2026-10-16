# -*- coding: utf-8 -*-
"""快速估计模型与圈定范围。

一个网络训练时随机屏蔽字段（并把“哪些字段可见”作为输入），训练一次之后，任意字段组合的推断精度只需一次前向计算。
同一个网络第一层带稀疏门控，门控强度给出每个字段“有没有推断作用”的排序（做法见 01 号实验）。
估计值只用来筛选，接近判定线的组合要重新训练核对。
"""
import numpy as np, torch, torch.nn as nn


class MaskNet(nn.Module):
    def __init__(self, d, nb, c, hidden=(128, 64), depth=4):
        super().__init__(); h = hidden[0]
        self.omega = nn.Parameter(torch.empty(d, h)); nn.init.kaiming_normal_(self.omega, nonlinearity="relu")
        self.gamma = nn.Parameter(torch.ones(depth - 1, d)); self.free = nn.Linear(nb + d, h)
        self.rest = nn.Sequential(nn.ReLU(), nn.Linear(h, hidden[1]), nn.ReLU(), nn.Linear(hidden[1], c))

    def forward(self, xc, m, xb):
        return self.rest(xc * m @ (self.omega * self.gamma.prod(0).unsqueeze(1)) + self.free(torch.cat([xb, m], 1)))

    def gates(self):
        return (self.gamma.detach().prod(0).abs() * self.omega.detach().norm(dim=1)).cpu().numpy()


class Fast:
    """字段按“项”组织：groups[i] 是第 i 个候选字段占用的列。屏蔽以项为单位。"""
    def __init__(self, Xb, Xc, Y, groups, tr, te, device="cuda:0", lam=5e-4, epochs=300, batch=256, seed=0, n_decoy=30):
        torch.manual_seed(seed); rng = np.random.default_rng(seed); self.dev = device; self.n = len(groups)
        dec = np.column_stack([rng.permutation(Xc[:, rng.choice(Xc.shape[1])]) for _ in range(n_decoy)]) if n_decoy else np.zeros((len(Xc), 0))
        Xa = np.hstack([Xc, dec]); self.groups = list(groups) + [[Xc.shape[1] + j] for j in range(dec.shape[1])]; G = len(self.groups)
        std = lambda a, ref: (a - ref.mean(0)) / (ref.std(0) + 1e-8); T = lambda a: torch.tensor(a, dtype=torch.float32, device=device)
        self.xc, self.y = T(std(Xa, Xa[tr])), T(std(Y, Y[tr])); self.xb = T(std(Xb, Xb[tr])) if Xb.shape[1] else torch.zeros(len(Xc), 0, device=device)
        self.E = torch.zeros(G, Xa.shape[1], device=device)
        for g, cols in enumerate(self.groups):
            self.E[g, cols] = 1
        self.tr, self.te = torch.tensor(tr, device=device), torch.tensor(te, device=device)
        self.net = MaskNet(Xa.shape[1], Xb.shape[1], Y.shape[1]).to(device); opt = torch.optim.Adam(self.net.parameters(), lr=1e-3)
        for _ in range(epochs):
            o = self.tr[torch.randperm(len(self.tr), device=device)]
            for s in range(0, len(o), batch):
                idx = o[s:s + batch]; q = torch.rand(len(idx), 1, device=device) ** 3 * 0.95 + 0.02      # 多数样本只留很少几个字段
                m = (torch.rand(len(idx), G, device=device) < q).float() @ self.E
                loss = ((self.net(self.xc[idx], m, self.xb[idx]) - self.y[idx]) ** 2).mean() + lam * (self.net.omega.square().sum() + self.net.gamma.square().sum())
                opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        self.net.eval(); self.tot = ((self.y[self.te] - self.y[self.tr].mean(0)) ** 2).sum(0)

    def relevance(self, q=90):
        """各候选字段的门控强度，以及按假字段的 q 分位定出的门槛。"""
        g = self.net.gates(); per = np.array([g[c].max() for c in self.groups]); real, dec = per[:self.n], per[self.n:]
        th = np.percentile(dec, q) if len(dec) else 0.0; return real / (real.max() + 1e-12), th / (real.max() + 1e-12)

    @torch.no_grad()
    def estimate(self, subsets, chunk=256):
        """各字段组合的估计推断精度 [组合数, 输出分量数]。"""
        out = []; xt, xbt, yt = self.xc[self.te], self.xb[self.te], self.y[self.te]; nte = len(self.te)
        for lo in range(0, len(subsets), chunk):
            part = subsets[lo:lo + chunk]; sel = torch.zeros(len(part), len(self.groups), device=self.dev)
            for r, s in enumerate(part):
                sel[r, list(s)] = 1
            m = (sel @ self.E).repeat_interleave(nte, 0)
            p = self.net(xt.repeat(len(part), 1), m, xbt.repeat(len(part), 1)).view(len(part), nte, -1)
            out.append((1 - ((p - yt[None]) ** 2).sum(1) / self.tot).clamp(min=0).cpu().numpy())
        return np.vstack(out)

    @torch.no_grad()
    def estimate_sel(self, sel, chunk=48):
        """sel [B, 候选字段数]（1 表示可见）的张量，返回估计推断精度的张量 [B, 输出分量数]。"""
        B = sel.shape[0]; selg = torch.cat([sel.float(), torch.zeros(B, len(self.groups) - self.n, device=self.dev)], 1)
        xt, xbt, yt = self.xc[self.te], self.xb[self.te], self.y[self.te]; nte = len(self.te); out = []
        for lo in range(0, B, chunk):
            part = selg[lo:lo + chunk]; m = (part @ self.E).repeat_interleave(nte, 0)
            pr = self.net(xt.repeat(len(part), 1), m, xbt.repeat(len(part), 1)).view(len(part), nte, -1)
            out.append((1 - ((pr - yt[None]) ** 2).sum(1) / self.tot).clamp(min=0))
        return torch.cat(out)
