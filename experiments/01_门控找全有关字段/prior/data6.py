# -*- coding: utf-8 -*-
"""前期工作中的 PJM 窗口数据处理（随实验一起保存，原样保留算法）：PJM 窗口数据、公开基底 + 候选组合的掩码、真值合成（攻击器取 max + 含空集的单调闭包）。"""
import os, sys, json, itertools
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PROJ = os.path.dirname(os.path.dirname(ROOT))
CSV = os.path.join(PROJ, "data", "raw", "pjm", "pjm_rto_hourly_2025_cleaned.csv")
BASE = ["forecast_load_mw_latest_available", "forecast_load_mw_day_ahead"]
CAND = json.load(open(os.path.join(HERE, "fields.json"), encoding="utf-8"))["cand"]
CONF2 = set(json.load(open(os.path.join(HERE, "fields.json"), encoding="utf-8"))["added_timely"])
TARG = ["total_losses", "total_gen", "gross_actual_interchange_mw", "net_actual_interchange_mw"]
TARG_CN = ["实际网损", "发电总出力", "实际总交换", "联络线净交换"]
TT = [("单位自身", 3), ("经济运行", 3), ("公共利益", 3), ("国家安全", 3)]   # 影响对象、影响程度（严重）
NW = 10


def window_rows(w, n=8760):
    m = np.array_split(np.arange(n), 12)
    return np.concatenate(m[w:w + 3])


def sets():
    keys = [()] + [s for k in range(1, 4) for s in itertools.combinations(range(len(CAND)), k)]
    M = np.zeros((len(keys), len(BASE) + len(CAND)), np.float32); M[:, :len(BASE)] = 1
    for r, s in enumerate(keys):
        M[r, [len(BASE) + i for i in s]] = 1
    return M, keys


def closure(V, keys):
    idx = {k: r for r, k in enumerate(keys)}; V = V.copy()
    for r in sorted(range(len(keys)), key=lambda r: len(keys[r])):
        k = keys[r]
        subs = [k[:j] + k[j + 1:] for j in range(len(k))] if len(k) > 1 else ([()] if len(k) == 1 else [])
        for s in subs:
            V[r] = np.maximum(V[r], V[idx[s]])
    return V
