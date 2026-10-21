# -*- coding: utf-8 -*-
"""推断模型：同时训练多个“只能看到某个字段子集”的神经网络，得到每个子集的推断精度（留出集 R²）。"""
import numpy as np, torch


def split(n, seed=42, ratio=0.8):
    o = np.random.default_rng(seed).permutation(n); k = int(n * ratio); return o[:k], o[k:]


def fit_subsets(X, Y, masks, device="cuda:0", hidden=(64, 32), epochs=80, batch=256, lr=2e-3, seed=0, keep_pred=None):
    """X [n,d]，Y [n,c]，masks [S,d]（1 表示该列可见）。
    返回 r2 [S,c]（各输出分量的留出集 R²，不小于 0），以及 keep_pred 指定的子集在留出集上的预测值（原量纲）。"""
    torch.manual_seed(seed); tr, te = split(len(X))
    xm, xs = X[tr].mean(0), X[tr].std(0) + 1e-8; ym, ys = Y[tr].mean(0), Y[tr].std(0) + 1e-8
    T = lambda a: torch.tensor(a, dtype=torch.float32, device=device)
    x, y, m = T((X - xm) / xs), T((Y - ym) / ys), T(np.asarray(masks, np.float32))
    S, d, c = m.shape[0], X.shape[1], Y.shape[1]; h1, h2 = hidden
    P = [torch.nn.Parameter(torch.randn(S, d, h1, device=device) * (2 / d) ** .5), torch.nn.Parameter(torch.zeros(S, 1, h1, device=device)),
         torch.nn.Parameter(torch.randn(S, h1, h2, device=device) * (2 / h1) ** .5), torch.nn.Parameter(torch.zeros(S, 1, h2, device=device)),
         torch.nn.Parameter(torch.randn(S, h2, c, device=device) * (1 / h2) ** .5), torch.nn.Parameter(torch.zeros(S, 1, c, device=device))]

    def f(xb):
        z = torch.relu(torch.einsum("nd,sdh->snh", xb, P[0] * m[:, :, None]) + P[1])
        return torch.bmm(torch.relu(torch.bmm(z, P[2]) + P[3]), P[4]) + P[5]

    opt = torch.optim.Adam(P, lr=lr); sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs); trt = torch.tensor(tr, device=device)
    for _ in range(epochs):
        o = trt[torch.randperm(len(trt), device=device)]
        for s in range(0, len(o), batch):
            idx = o[s:s + batch]; loss = ((f(x[idx]) - y[idx][None]) ** 2).mean((1, 2)).sum()
            opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        sched.step()
    with torch.no_grad():
        tet = torch.tensor(te, device=device); p = torch.cat([f(x[tet[i:i + 4096]]) for i in range(0, len(tet), 4096)], 1)
        res = ((p - y[tet][None]) ** 2).sum(1); tot = ((y[tet] - y[trt].mean(0)) ** 2).sum(0)
        r2 = (1 - res / tot).clamp(min=0).cpu().numpy()
        pred = {int(k): (p[int(k)].cpu().numpy() * ys + ym) for k in (keep_pred or [])}
    return r2, pred, te
