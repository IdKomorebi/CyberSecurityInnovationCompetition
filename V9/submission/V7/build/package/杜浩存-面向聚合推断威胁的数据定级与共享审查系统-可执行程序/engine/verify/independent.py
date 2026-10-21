# -*- coding: utf-8 -*-
"""换一种没参与定级的预测模型（梯度提升树）复测：接收方可见的全部字段对敏感数据的推断精度。"""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor


def r2(X, Y, tr, te, max_comp=4):
    if X.shape[1] == 0:
        return 0.0
    comps = np.linspace(0, Y.shape[1] - 1, min(max_comp, Y.shape[1])).astype(int); out = []
    for j in comps:
        m = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, random_state=0).fit(X[tr], Y[tr, j]); p = m.predict(X[te])
        out.append(max(0.0, 1 - ((Y[te, j] - p) ** 2).sum() / (((Y[te, j] - Y[tr, j].mean()) ** 2).sum() + 1e-12)))
    return float(np.mean(out))
