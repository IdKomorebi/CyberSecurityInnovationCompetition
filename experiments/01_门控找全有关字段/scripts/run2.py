# -*- coding: utf-8 -*-
"""01 号第二轮：混入打乱的假字段定门槛。F=门控强度超过假字段最大值；G=屏蔽增益超过假字段最大值。"""
import os, sys, re, json, argparse, itertools, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "src"))
from gate import train_masked
ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int); ap.add_argument("--gpu", type=int); ap.add_argument("--crime_dir")
a = ap.parse_args(); dev = f"cuda:{a.gpu}"; ND = 30
GNN = "/data1/duhaocun/projects/GNN_Aggresvation"; E06 = GNN + "/reports/南网/南网claude/实验/06_PJM五级动态分级"
res = []; t0 = time.time()


def run(data, task, Xreal, Xb, y, truth):
    rng = np.random.default_rng(100 + a.seed); n = Xreal.shape[1]
    dec = np.column_stack([rng.permutation(Xreal[:, j]) for j in rng.choice(n, ND, replace=n < ND)])
    for lam in (5e-3, 5e-4):
        gate, gain = train_masked(np.hstack([Xreal, dec]), Xb, y, lam, a.seed, dev)
        for name, s in (("F_屏蔽门控+假字段门槛", gate), ("G_屏蔽增益+假字段门槛", gain)):
            th = s[n:].max(); sel = np.r_[s[:n] > th, np.zeros(ND, bool)]
            res.append(dict(data=data, task=task, method=f"{name}(惩罚{lam:g})", seed=a.seed, truth=list(truth) + [0.0] * ND,
                            decoy=[False] * n + [True] * ND, gate=s.tolist(), sel=sel.tolist(), r2=None, th=float(th)))


sys.path.insert(0, E06 + "/src"); import data6 as D
df = pd.read_csv(D.CSV); cols = D.BASE + D.CAND + D.TARG; df[cols] = df[cols].interpolate().ffill().bfill()
_, keys = D.sets(); kid = {k: r for r, k in enumerate(keys)}; n = len(D.CAND)
for w in (0, 4, 8):
    V = np.load(f"{E06}/outputs/windows/w{w}.npz")["V"]; d = df.iloc[D.window_rows(w)]
    for t, tn in enumerate(D.TARG):
        M = np.zeros(n)
        for i in range(n):
            for k in range(0, 3):
                for T in itertools.combinations([j for j in range(n) if j != i], k):
                    M[i] = max(M[i], V[kid[tuple(sorted(T + (i,)))], t] - V[kid[T], t])
        run("PJM", f"w{w}/{tn}", d[D.CAND].to_numpy(float), d[D.BASE].to_numpy(float), d[tn].to_numpy(float), M)
    print("PJM", w, f"{time.time()-t0:.0f}s", flush=True)
names = [re.split(r"\s+", l.strip())[1] for l in open(a.crime_dir + "/communities.names", encoding="latin-1") if l.startswith("@attribute")]
c = pd.read_csv(a.crime_dir + "/communities.data", header=None, names=names, na_values="?").drop(columns=["state", "county", "community", "communityname", "fold"]).dropna(axis=1)
single = json.load(open(os.path.join(ROOT, "outputs", "crime_single.json"), encoding="utf-8"))
for tn in ["PctPopUnderPov", "medIncome", "PctIlleg"]:
    feats = [f for f in c.columns if f != tn]
    run("社区统计", tn, c[feats].to_numpy(float), None, c[tn].to_numpy(float), [single[tn][f] for f in feats]); print("社区统计", tn, f"{time.time()-t0:.0f}s", flush=True)
json.dump(res, open(os.path.join(ROOT, "outputs", f"res_seed{a.seed}_r2.json"), "w", encoding="utf-8"), ensure_ascii=False)
