# -*- coding: utf-8 -*-
"""门槛取假字段门控强度的不同分位数时，找回比例与选出比例的变化（方法：随机稀疏屏蔽 + 惩罚 0.0005）。"""
import os, json, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); rows = []
for f in glob.glob(os.path.join(ROOT, "outputs", "res_seed*_r3.json")):
    for r in json.load(open(f, encoding="utf-8")):
        if r["method"] != "F_屏蔽门控+假字段门槛(惩罚0.0005,稀疏3)":
            continue
        t, dec, g = np.array(r["truth"]), np.array(r["decoy"]), np.array(r["gate"]); real = ~dec; use = (t >= .05) & real
        if not use.any():
            continue
        for q in (100, 90, 75, 50):
            sel = g > np.percentile(g[dec], q); miss = t[use & ~sel]
            rows.append(dict(数据=r["data"], 门槛分位=q, 找回比例=sel[use].mean(), 漏掉的最大真值=miss.max() if len(miss) else 0, 选出比例=sel[real].mean(), 假字段误选=sel[dec].mean()))
d = pd.DataFrame(rows).groupby(["数据", "门槛分位"]).agg(找回比例=("找回比例", "mean"), 最差找回=("找回比例", "min"), 漏掉的最大真值=("漏掉的最大真值", "max"), 选出比例=("选出比例", "mean"), 假字段误选=("假字段误选", "mean")).round(3)
d.to_csv(os.path.join(ROOT, "outputs", "threshold.csv")); print(d.to_string())
