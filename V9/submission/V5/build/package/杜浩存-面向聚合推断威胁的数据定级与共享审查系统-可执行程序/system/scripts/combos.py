# -*- coding: utf-8 -*-
"""越线组合：在已逐个重新训练的组合之外，用估计器当场计算规模更大的最小越线组合。

用法：python combos.py <任务> --target <保护对象字段> --k <最大规模> [--gpu 自动|处理器|编号] [--verify 20]
做法：
  1. 训练（或读取缓存的）快速估计网络：随机遮挡输入、分解式门控、诱饵字段，一次训练即可估计任意字段组合；
  2. 按门控强度圈出作用较强的字段（最多 22 个），对其中规模不超过 k 的全部组合打分；已重新训练过的组合用真实值；
  3. 单调闭包后，对每类接收方找出估计的最小越线组合（凑齐即越线，去掉任一字段即不越线）；
  4. 对估计值最高的若干个新组合重新训练核对，结果标为“估计、已核对”。
结果写到 runtime/cache/<任务>_组合_<保护对象>_k<k>.json，界面读取。"""
import os, sys, json, time, pickle, itertools, argparse
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SYS = os.path.dirname(HERE); ROOT = os.path.dirname(SYS)
for d in ("grading", "infer"):
    sys.path.insert(0, os.path.join(ROOT, "engine", d))
sys.path.insert(0, HERE)
import torch, second, fast, device, review
from nets import fit_subsets, split
from taskdata import load, catalog_path

ap = argparse.ArgumentParser(); ap.add_argument("task"); ap.add_argument("--target", required=True); ap.add_argument("--k", type=int, default=4)
ap.add_argument("--gpu", default="自动"); ap.add_argument("--verify", type=int, default=20); ap.add_argument("--keep", type=int, default=22)
a = ap.parse_args(); T0 = time.time(); log = lambda *x: print(f"[{time.time() - T0:5.0f}s]", *x, flush=True)
g, devname = device.pick(a.gpu); dev = "cpu" if g < 0 else f"cuda:{g}"; log("计算设备：", devname)
CACHE = os.path.join(SYS, "runtime", "cache"); D = json.load(open(os.path.join(SYS, "samples", a.task + ".json"), encoding="utf-8"))
meta, base, candd, targd, _ = load(a.task); cand, targ = list(candd), list(targd); n = len(cand)
t = targ.index(a.target); tname = D["敏感"][t]
Xb = np.hstack(list(base.values())) if base else np.zeros((len(next(iter(candd.values()))), 0)); Xs = [candd[c] for c in cand]; Ys = [targd[c] for c in targ]
X = np.hstack([Xb] + Xs); Y = np.hstack(Ys); nb = Xb.shape[1]; off = nb + np.cumsum([0] + [x.shape[1] for x in Xs]); toff = np.cumsum([0] + [y.shape[1] for y in Ys])
tr, te = split(len(X)); groups = [list(range(off[i] - nb, off[i + 1] - nb)) for i in range(n)]

# 1 快速估计网络（同一任务只训练一次，缓存参数）
fpath = os.path.join(CACHE, a.task + "_估计器.pt")
F = fast.Fast(Xb, np.hstack(Xs), Y, groups, tr, te, dev, epochs=0 if os.path.exists(fpath) else 300)
if os.path.exists(fpath):
    F.net.load_state_dict(torch.load(fpath, map_location=dev)); F.net.eval(); log("读取已训练的估计器")
else:
    torch.save(F.net.state_dict(), fpath); log("估计器训练完成")
tmean = lambda r: r[:, toff[t]:toff[t + 1]].mean(1)

# 2 圈定字段，估计全部规模不超过 k 的组合；已重新训练过的组合用真实值
rel, th = F.relevance(90); keep = sorted([int(i) for i in np.argsort(-rel) if rel[i] > th][:a.keep])
exact = {k: float(np.asarray(v)[t]) for k, v in second.closure(pickle.load(open(os.path.join(CACHE, a.task + ".pkl"), "rb"))["V"], len(targ)).items()}
subs = [()] + [s for k in range(1, a.k + 1) for s in itertools.combinations(keep, k)]
log(f"圈定 {len(keep)} 个字段（共 {n} 个），估计 {len(subs)} 个组合")
est = np.zeros(len(subs))
for lo in range(0, len(subs), 2048):
    est[lo:lo + 2048] = tmean(F.estimate(subs[lo:lo + 2048], chunk=64))
both = [(s, e) for s, e in zip(subs, est) if frozenset(s) in exact and len(s) > 0]
mae = float(np.mean([abs(e - exact[frozenset(s)]) for s, e in both])) if both else None
V = {frozenset(s): (exact[frozenset(s)] if frozenset(s) in exact else float(e)) for s, e in zip(subs, est)}
src = {frozenset(s): ("重训" if frozenset(s) in exact else "估计") for s in subs}
for s in sorted(V, key=len):                                             # 单调闭包：多给字段不会更推不准
    for i in s:
        V[s] = max(V[s], V.get(s - {i}, 0.0))
log("估计完成；与已重新训练组合的平均绝对误差", round(mae, 3) if mae is not None else "无")

# 3 每类接收方的最小越线组合（只看接收方按一次等级能凑齐、且无权获取保护对象的情形）
rows, model = review.load(catalog_path(a.task)); by = {r["字段"]: r for r in rows}
L1 = [by[c]["一次等级"] for c in cand]; L2 = [f["二次等级"] for f in D["字段"] if f["角色"] == "候选"]; TL = by[a.target]["一次等级"]
LINE = {r["级"]: r["判定线"] for r in D["接收方"]}; RN = {r["级"]: r["名称"] for r in D["接收方"]}
found = []
for c in (1, 2, 3):
    if TL <= c:
        continue
    vis = [i for i in keep if L1[i] <= c]
    for s in V:
        if len(s) < 1 or not s <= set(vis) or V[s] <= LINE[c] or any(V.get(s - {i}, 0.0) > LINE[c] for i in s):
            continue
        found.append(dict(接收方=RN[c], 级=c, 组合=sorted(s), 规模=len(s), 精度=round(V[s], 3), 来源=src[s], 判定线=LINE[c]))

# 4 对估计得到的新组合，按估计值从高到低重新训练核对
new = sorted([x for x in found if x["来源"] == "估计"], key=lambda x: -x["精度"])[:a.verify]
if new:
    masks = np.zeros((len(new), X.shape[1]), np.float32); masks[:, :nb] = 1
    for r, x in enumerate(new):
        for i in x["组合"]:
            masks[r, off[i]:off[i + 1]] = 1
    r2, _, _ = fit_subsets(X, Y, masks, dev, seed=0)
    for r, x in enumerate(new):
        x["重训精度"] = round(float(r2[r, toff[t]:toff[t + 1]].mean()), 3); x["来源"] = "估计、已核对"; x["核对越线"] = bool(x["重训精度"] > x["判定线"])
    log(f"重新训练核对 {len(new)} 个估计组合")
for x in found:
    s = frozenset(x["组合"])
    x["子集"] = [dict(字段=[cand[i] for i in sorted(u)], 精度=round(V[frozenset(u)], 3), 来源=src[frozenset(u)]) for k in range(1, len(s)) for u in itertools.combinations(sorted(s), k)]
    x["二次定级后仍成立"] = all(L2[i] <= x["级"] for i in x["组合"])
    x["拆开字段"] = [cand[i] for i in x["组合"] if L2[i] > x["级"]]
    x["组合"] = [cand[i] for i in x["组合"]]
found.sort(key=lambda x: (x["规模"], -x["精度"]))
out = dict(任务=a.task, 保护对象=a.target, 名称=tname, 最大规模=a.k, 圈定字段=[cand[i] for i in keep], 候选字段数=n, 估计组合数=len(subs),
           估计与重训平均绝对误差=round(mae, 3) if mae is not None else None, 组合=found, 设备=devname, 用时秒=round(time.time() - T0, 1))
json.dump(out, open(os.path.join(CACHE, f"{a.task}_组合_{a.target}_k{a.k}.json"), "w", encoding="utf-8"), ensure_ascii=False)
log(f"完成：最小越线组合 {len(found)} 个，其中规模 > 3 的 {sum(x['规模'] > 3 for x in found)} 个")
