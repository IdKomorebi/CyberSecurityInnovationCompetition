# -*- coding: utf-8 -*-
"""汇总：找回比例、漏掉字段里的最大真值、选出比例、假字段误选比例、门控强度对“有作用”的排序能力。"""
import os, json, glob
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for f in sorted(glob.glob(os.path.join(ROOT, "outputs", "res_seed*.json"))):
    for r in json.load(open(f, encoding="utf-8")):
        t, sel, dec, g = np.array(r["truth"]), np.array(r["sel"]), np.array(r["decoy"]), np.array(r["gate"])
        real = ~dec; use = (t >= 0.05) & real
        if use.sum() == 0:
            continue
        miss = t[use & ~sel]
        rows.append(dict(数据=r["data"], 方法=r["method"], 任务=r["task"], 种子=r["seed"],
                         找回比例=sel[use].mean(), 漏掉的最大真值=miss.max() if len(miss) else 0.0,
                         选出比例=sel[real].mean(), 假字段误选=sel[dec].mean() if dec.any() and "假字段门槛" not in r["method"] else np.nan,
                         排序能力=roc_auc_score(use[real] if not dec.any() else np.r_[use[real], np.zeros(dec.sum(), bool)],
                                              g[real] if not dec.any() else np.r_[g[real], g[dec]]) if 0 < use.sum() < len(t) else np.nan))
d = pd.DataFrame(rows); d.to_csv(os.path.join(ROOT, "outputs", "detail.csv"), index=False)
s = d.groupby(["数据", "方法"]).agg(任务数=("找回比例", "size"), 找回比例=("找回比例", "mean"), 最差找回=("找回比例", "min"),
                                漏掉的最大真值=("漏掉的最大真值", "max"), 选出比例=("选出比例", "mean"), 假字段误选=("假字段误选", "mean"), 排序能力=("排序能力", "mean")).round(3)
s.to_csv(os.path.join(ROOT, "outputs", "summary.csv")); print(s.to_string())
