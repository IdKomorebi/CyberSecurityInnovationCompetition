# -*- coding: utf-8 -*-
"""01 号主程序：五种方法 × 两个数据集。用法：run.py --seed 0 --gpu 0 --crime_dir <社区统计数据目录>"""
import os, sys, re, json, argparse, itertools, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, "src"))
from gate import train_gate, plain_r2
ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int); ap.add_argument("--gpu", type=int); ap.add_argument("--crime_dir")
a = ap.parse_args(); dev = f"cuda:{a.gpu}"; TH = 0.02; TAU = 0.7
E06 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prior")      # 前期工作的窗口数据与处理代码，随实验保存


def methods(Xc, Xb, y, seed):
    out = {}
    for name, lam, mk in [("A_原门控", 5e-3, False), ("C_低惩罚", 5e-4, False), ("D_随机屏蔽", 5e-3, True), ("E_随机屏蔽低惩罚", 5e-4, True)]:
        g, r2 = train_gate(Xc, Xb, y, lam, mk, seed, dev); out[name] = dict(gate=g.tolist(), sel=(g >= TH).tolist(), r2=r2)
    # B：逐轮剥离
    rest = list(range(Xc.shape[1])); H = []
    for _ in range(6):
        Xr = Xc[:, rest]; full = np.hstack([Xb, Xr]) if Xb is not None else Xr
        if not rest or plain_r2(full, y, seed, dev) <= TAU:
            break
        g, _ = train_gate(Xr, Xb, y, 5e-3, False, seed, dev); pick = [rest[i] for i in np.flatnonzero(g >= TH)] or [rest[int(g.argmax())]]
        H += pick; rest = [i for i in rest if i not in pick]
    sel = np.zeros(Xc.shape[1], bool); sel[H] = True
    out["B_逐轮剥离"] = dict(gate=sel.astype(float).tolist(), sel=sel.tolist(), r2=None)
    return out


res = []; t0 = time.time()
# ---------- PJM ----------
sys.path.insert(0, E06); import data6 as D
df = pd.read_csv(D.CSV); _cols = D.BASE + D.CAND + D.TARG; df[_cols] = df[_cols].interpolate().ffill().bfill(); assert not df[_cols].isna().any().any(); _, keys = D.sets(); kid = {k: r for r, k in enumerate(keys)}; n = len(D.CAND)
for w in (0, 4, 8):
    V = np.load(f"{E06}/windows/w{w}.npz")["V"]; d = df.iloc[D.window_rows(w)]
    Xb = d[D.BASE].to_numpy(float); Xc = d[D.CAND].to_numpy(float)
    for t, tn in enumerate(D.TARG):
        M = np.zeros(n)
        for i in range(n):
            for k in range(0, 3):
                for T in itertools.combinations([j for j in range(n) if j != i], k):
                    M[i] = max(M[i], V[kid[tuple(sorted(T + (i,)))], t] - V[kid[T], t])
        y = d[tn].to_numpy(float)
        for name, o in methods(Xc, Xb, y, a.seed).items():
            res.append(dict(data="PJM", task=f"w{w}/{tn}", method=name, seed=a.seed, truth=M.tolist(), decoy=[False] * n, **o))
        print(f"PJM w{w} {tn} 有作用 {int((M >= .05).sum())}/{n}  {time.time()-t0:.0f}s", flush=True)
# ---------- 社区统计 ----------
if a.crime_dir:
    names = [re.split(r"\s+", l.strip())[1] for l in open(a.crime_dir + "/communities.names", encoding="latin-1") if l.startswith("@attribute")]
    c = pd.read_csv(a.crime_dir + "/communities.data", header=None, names=names, na_values="?").drop(columns=["state", "county", "community", "communityname", "fold"]).dropna(axis=1)
    single = json.load(open(os.path.join(ROOT, "outputs", "crime_single.json"), encoding="utf-8"))
    rng = np.random.default_rng(100 + a.seed)
    for tn in ["PctPopUnderPov", "medIncome", "PctIlleg"]:
        feats = [f for f in c.columns if f != tn]; X = c[feats].to_numpy(float)
        dec = np.column_stack([rng.permutation(X[:, j]) for j in rng.choice(len(feats), 30, replace=False)])
        Xc = np.hstack([X, dec]); truth = [single[tn][f] for f in feats] + [0.0] * 30
        for name, o in methods(Xc, None, c[tn].to_numpy(float), a.seed).items():
            res.append(dict(data="社区统计", task=tn, method=name, seed=a.seed, truth=truth, decoy=[False] * len(feats) + [True] * 30, **o))
        print(f"社区统计 {tn}  {time.time()-t0:.0f}s", flush=True)
json.dump(res, open(os.path.join(ROOT, "outputs", f"res_seed{a.seed}.json"), "w", encoding="utf-8"), ensure_ascii=False)
