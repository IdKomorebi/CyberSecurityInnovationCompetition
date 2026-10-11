"""非电力数据集粗查：单个字段与字段组合对敏感数据的推断精度（留出集 R²）。"""
import sys, itertools, re, json
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold

def r2_cv(X, y, seed=0):
    if X.shape[1] == 0:
        return 0.0
    kf = KFold(n_splits=4, shuffle=True, random_state=seed)
    ss_res = ss_tot = 0.0
    for tr, te in kf.split(X):
        m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.08, max_leaf_nodes=15,
                                          min_samples_leaf=10, random_state=seed)
        m.fit(X[tr], y[tr])
        p = m.predict(X[te])
        ss_res += ((y[te] - p) ** 2).sum()
        ss_tot += ((y[te] - y[tr].mean()) ** 2).sum()
    return max(0.0, 1 - ss_res / ss_tot)

def insurance(path):
    d = pd.read_csv(path)
    d["sex"] = (d["sex"] == "male").astype(float)
    d["smoker"] = (d["smoker"] == "yes").astype(float)
    d["region"] = d["region"].astype("category").cat.codes.astype(float)
    y = d["charges"].to_numpy(float)
    feats = ["age", "sex", "bmi", "children", "smoker", "region"]
    X = d[feats].to_numpy(float)
    combos = [c for k in range(1, len(feats) + 1) for c in itertools.combinations(range(len(feats)), k)]
    vals = Parallel(n_jobs=16)(delayed(r2_cv)(X[:, list(c)], y) for c in combos)
    res = {tuple(feats[i] for i in c): v for c, v in zip(combos, vals)}
    print(f"[个人信息] 医疗费用数据集：{len(d)} 行，{len(feats)} 个字段，目标 charges（医疗费用）")
    for k in range(1, len(feats) + 1):
        top = sorted([(v, c) for c, v in res.items() if len(c) == k], reverse=True)[:4]
        print(f"  {k} 个字段：" + "；".join(f"{'+'.join(c)}={v:.2f}" for v, c in top))

def crime(data_path, names_path):
    names = [re.split(r"\s+", l.strip())[1] for l in open(names_path, encoding="latin-1") if l.startswith("@attribute")]
    d = pd.read_csv(data_path, header=None, names=names, na_values="?")
    d = d.drop(columns=["state", "county", "community", "communityname", "fold"])
    d = d.dropna(axis=1)
    print(f"[公共数据] 社区人口经济统计：{len(d)} 行，{d.shape[1]} 个无缺失数值字段")
    targets = ["ViolentCrimesPerPop", "medIncome", "PctPopUnderPov", "PctUnemployed", "PctIlleg", "PctKids2Par"]
    for t in targets:
        y = d[t].to_numpy(float)
        feats = [c for c in d.columns if c != t]
        X = d[feats].to_numpy(float)
        singles = Parallel(n_jobs=24)(delayed(r2_cv)(X[:, [i]], y) for i in range(len(feats)))
        order = np.argsort(singles)[::-1]
        full = r2_cv(X, y)
        print(f"\n  目标 {t}：全部 {len(feats)} 个字段 R²={full:.2f}")
        print("    单字段最高：" + "；".join(f"{feats[i]}={singles[i]:.2f}" for i in order[:6]))
        # 只在“单字段 < 0.5”的字段里做逐步加入，看低相关字段合起来能推多准
        weak = [i for i in range(len(feats)) if singles[i] < 0.5]
        chosen, cur = [], 0.0
        for step in range(6):
            cand = [i for i in weak if i not in chosen]
            vals = Parallel(n_jobs=24)(delayed(r2_cv)(X[:, chosen + [i]], y) for i in cand)
            j = int(np.argmax(vals))
            chosen.append(cand[j]); cur = vals[j]
            print(f"    弱字段逐步加入 第{step+1}个 {feats[cand[j]]}(单独 {singles[cand[j]]:.2f}) → 合起来 {cur:.2f}")
        allweak = r2_cv(X[:, weak], y)
        print(f"    全部 {len(weak)} 个弱字段（单独都 <0.5）合起来 R²={allweak:.2f}")

if __name__ == "__main__":
    base = sys.argv[1]
    insurance(f"{base}/insurance/insurance.csv")
    crime(f"{base}/crime/communities.data", f"{base}/crime/communities.names")
