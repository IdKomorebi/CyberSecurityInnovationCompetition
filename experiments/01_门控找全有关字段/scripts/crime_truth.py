# -*- coding: utf-8 -*-
"""社区统计的参照：每个真实字段单独推断各敏感数据的精度（梯度提升树，四折）。用法：crime_truth.py <数据目录>"""
import os, sys, re, json
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import cross_val_predict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); d = sys.argv[1]
names = [re.split(r"\s+", l.strip())[1] for l in open(d + "/communities.names", encoding="latin-1") if l.startswith("@attribute")]
c = pd.read_csv(d + "/communities.data", header=None, names=names, na_values="?").drop(columns=["state", "county", "community", "communityname", "fold"]).dropna(axis=1)
def r2(x, y):
    p = cross_val_predict(HistGradientBoostingRegressor(max_iter=150, max_leaf_nodes=15, random_state=0), x, y, cv=4)
    return float(max(0, 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()))
out = {}
for t in ["PctPopUnderPov", "medIncome", "PctIlleg"]:
    fs = [f for f in c.columns if f != t]; y = c[t].to_numpy(float)
    v = Parallel(n_jobs=24)(delayed(r2)(c[[f]].to_numpy(float), y) for f in fs); out[t] = dict(zip(fs, v))
    print(t, "有作用(≥0.05)", sum(x >= .05 for x in v), "/", len(fs))
json.dump(out, open(os.path.join(ROOT, "outputs", "crime_single.json"), "w", encoding="utf-8"))
