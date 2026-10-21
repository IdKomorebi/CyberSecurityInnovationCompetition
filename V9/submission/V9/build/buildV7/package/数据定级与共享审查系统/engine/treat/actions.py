# -*- coding: utf-8 -*-
"""处置方式：对一个字段（可含多列）做变换，返回变换后的数据。可用程度 = 变换后与原值的拟合优度（1 表示原样）。"""
import numpy as np


def _noise(x, k, rng):
    return x + rng.normal(0, 1, x.shape) * x.std(0, keepdims=True) * k


def _roll(x, win):
    c = np.cumsum(np.vstack([np.zeros((1, x.shape[1])), x]), 0); n = len(x); i = np.arange(n); lo = np.maximum(0, i - win + 1)
    return (c[i + 1] - c[lo]) / (i + 1 - lo)[:, None]


def _bins(x, b):
    out = x.copy()
    for j in range(x.shape[1]):
        q = np.unique(np.quantile(x[:, j], np.linspace(0, 1, b + 1)))
        if len(q) < 3:
            continue
        g = np.clip(np.searchsorted(q, x[:, j], side="right") - 1, 0, len(q) - 2)
        out[:, j] = np.array([x[g == v, j].mean() if (g == v).any() else 0 for v in range(len(q) - 1)])[g]
    return out


def catalog(time_series):
    acts = [("加噪声（0.25 倍标准差）", lambda x, r: _noise(x, .25, r)), ("加噪声（0.5 倍标准差）", lambda x, r: _noise(x, .5, r)),
            ("加噪声（1 倍标准差）", lambda x, r: _noise(x, 1., r)), ("加噪声（2 倍标准差）", lambda x, r: _noise(x, 2., r)),
            ("分档（10 档）", lambda x, r: _bins(x, 10)), ("分档（5 档）", lambda x, r: _bins(x, 5)), ("分档（3 档）", lambda x, r: _bins(x, 3)), ("分档（2 档）", lambda x, r: _bins(x, 2))]
    if time_series:
        acts += [("时间平均（6 个时段）", lambda x, r: _roll(x, 6)), ("时间平均（24 个时段）", lambda x, r: _roll(x, 24)), ("时间平均（168 个时段）", lambda x, r: _roll(x, 168))]
    return acts


def usable(x0, x1):
    v = ((x0 - x0.mean(0)) ** 2).sum(0) + 1e-12
    return float(np.clip(1 - ((x0 - x1) ** 2).sum(0) / v, 0, 1).mean())
