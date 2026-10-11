# -*- coding: utf-8 -*-
"""稀疏门控（沿用电碳作品的分解式门控）及其随机屏蔽版本。"""
import numpy as np, torch, torch.nn as nn


def _std(a):
    m, s = a.mean(0, keepdims=True), a.std(0, keepdims=True) + 1e-8
    return (a - m) / s


def split(n, seed=42, ratio=0.8):
    o = np.random.default_rng(seed).permutation(n); k = int(n * ratio)
    return o[:k], o[k:]


class Gate(nn.Module):
    """候选字段过门控；公开字段和屏蔽标记不过门控。"""
    def __init__(self, n_cand, n_free, hidden=(64, 32, 16), depth=4):
        super().__init__()
        h = hidden[0]
        self.omega = nn.Parameter(torch.empty(n_cand, h)); nn.init.kaiming_normal_(self.omega, nonlinearity="relu")
        self.gamma = nn.Parameter(torch.ones(depth - 1, n_cand))
        self.free = nn.Linear(n_free, h) if n_free else None
        self.bias = nn.Parameter(torch.zeros(h))
        layers, d = [], h
        for w in hidden[1:]:
            layers += [nn.Linear(d, w), nn.ReLU()]; d = w
        self.rest = nn.Sequential(*layers, nn.Linear(d, 1))

    def forward(self, xc, xf=None):
        z = xc @ (self.omega * self.gamma.prod(0).unsqueeze(1)) + self.bias
        if self.free is not None:
            z = z + self.free(xf)
        return self.rest(torch.relu(z)).squeeze(1)

    def gates(self):
        g = self.gamma.detach().prod(0).abs() * self.omega.detach().norm(dim=1)
        return g.cpu().numpy()

    def penalty(self):
        return self.omega.square().sum() + self.gamma.square().sum()


def train_gate(Xc, Xb, y, lam, mask=False, seed=0, device="cuda:0", epochs=140, batch=128, lr=1e-3):
    """返回每个候选字段的门控强度（已除以最大值）与留出集 R²。mask=True 时随机屏蔽候选字段。"""
    torch.manual_seed(seed); np.random.seed(seed)
    tr, te = split(len(y))
    Xc, y = _std(Xc), _std(y[:, None])[:, 0]
    Xb = _std(Xb) if Xb is not None and Xb.shape[1] else None
    T = lambda a: torch.tensor(a, dtype=torch.float32, device=device)
    xc, yt = T(Xc), T(y); xb = T(Xb) if Xb is not None else None
    nc = Xc.shape[1]; nfree = (Xb.shape[1] if Xb is not None else 0) + (nc if mask else 0)
    net = Gate(nc, nfree).to(device); opt = torch.optim.Adam(net.parameters(), lr=lr)
    tr_t = torch.tensor(tr, device=device)

    def feed(idx, m=None):
        a = xc[idx]; parts = [xb[idx]] if xb is not None else []
        if mask:
            if m is None:
                m = torch.ones_like(a)
            a = a * m; parts.append(m)
        return net(a, torch.cat(parts, 1) if parts else None)

    for _ in range(epochs):
        net.train(); o = tr_t[torch.randperm(len(tr_t), device=device)]
        for s in range(0, len(o), batch):
            idx = o[s:s + batch]; m = None
            if mask:
                q = torch.rand(len(idx), 1, device=device) * 0.7 + 0.3      # 每条样本保留比例 0.3~1
                m = (torch.rand(len(idx), nc, device=device) < q).float()
            loss = ((feed(idx, m) - yt[idx]) ** 2).mean() + lam * net.penalty()
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    net.eval()
    with torch.no_grad():
        p = feed(torch.tensor(te, device=device)).cpu().numpy()
    r2 = 1 - ((y[te] - p) ** 2).sum() / ((y[te] - y[tr].mean()) ** 2).sum()
    g = net.gates(); return g / (g.max() + 1e-12), float(r2)


def plain_r2(X, y, seed=0, device="cuda:0", epochs=100, batch=128, lr=1e-3):
    """普通网络的留出集 R²（用于逐轮剥离的停止判断）。"""
    if X.shape[1] == 0:
        return 0.0
    torch.manual_seed(seed); tr, te = split(len(y))
    X, y = _std(X), _std(y[:, None])[:, 0]
    T = lambda a: torch.tensor(a, dtype=torch.float32, device=device)
    x, yt = T(X), T(y)
    net = nn.Sequential(nn.Linear(X.shape[1], 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1)).to(device)
    opt = torch.optim.Adam(net.parameters(), lr=lr); tr_t = torch.tensor(tr, device=device)
    for _ in range(epochs):
        o = tr_t[torch.randperm(len(tr_t), device=device)]
        for s in range(0, len(o), batch):
            idx = o[s:s + batch]; loss = ((net(x[idx]).squeeze(1) - yt[idx]) ** 2).mean()
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    with torch.no_grad():
        p = net(x[torch.tensor(te, device=device)]).squeeze(1).cpu().numpy()
    return float(max(0.0, 1 - ((y[te] - p) ** 2).sum() / ((y[te] - y[tr].mean()) ** 2).sum()))


def train_masked(Xc, Xb, y, lam, seed=0, device="cuda:0", epochs=140, batch=128, lr=1e-3, rounds=16, qpow=1.0):
    """随机屏蔽训练一次，返回两种“有没有作用”的度量：
    gate：门控强度；gain：在随机背景下把该字段从“屏蔽”改为“可见”，留出集误差下降的比例（均值）。"""
    torch.manual_seed(seed); np.random.seed(seed)
    tr, te = split(len(y)); Xc, y = _std(Xc), _std(y[:, None])[:, 0]
    Xb = _std(Xb) if Xb is not None and Xb.shape[1] else None
    T = lambda a: torch.tensor(a, dtype=torch.float32, device=device)
    xc, yt = T(Xc), T(y); xb = T(Xb) if Xb is not None else None
    nc = Xc.shape[1]; net = Gate(nc, (Xb.shape[1] if Xb is not None else 0) + nc).to(device)
    opt = torch.optim.Adam(net.parameters(), lr=lr); tr_t = torch.tensor(tr, device=device); te_t = torch.tensor(te, device=device)
    f = lambda idx, m: net(xc[idx] * m, torch.cat(([xb[idx]] if xb is not None else []) + [m], 1))
    for _ in range(epochs):
        net.train(); o = tr_t[torch.randperm(len(tr_t), device=device)]
        for s in range(0, len(o), batch):
            idx = o[s:s + batch]; q = torch.rand(len(idx), 1, device=device) ** qpow * 0.95 + 0.05 / qpow
            m = (torch.rand(len(idx), nc, device=device) < q).float()
            loss = ((f(idx, m) - yt[idx]) ** 2).mean() + lam * net.penalty()
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
    net.eval(); gain = np.zeros(nc); var = float(((yt[te_t] - yt[tr_t].mean()) ** 2).mean())
    g = torch.Generator(device=device).manual_seed(seed + 7)
    with torch.no_grad():
        for _ in range(rounds):
            q = torch.rand(len(te_t), 1, device=device, generator=g) * 0.6 + 0.1          # 背景较稀，冗余字段才显得出作用
            m = (torch.rand(len(te_t), nc, device=device, generator=g) < q).float()
            for i in range(nc):
                m0, m1 = m.clone(), m.clone(); m0[:, i] = 0; m1[:, i] = 1
                gain[i] += float((((f(te_t, m0) - yt[te_t]) ** 2).mean() - ((f(te_t, m1) - yt[te_t]) ** 2).mean())) / var / rounds
    gt = net.gates(); return gt / (gt.max() + 1e-12), gain
