# -*- coding: utf-8 -*-
"""越线组合：在已逐个重新训练的组合之外，用估计器当场计算规模更大的最小越线组合。

用法：python combos.py <任务> --target <保护对象字段> --k <最大规模> [--gpu 自动|处理器|编号] [--retrain 40]
做法：
  1. 训练（或读取缓存的）门控网络与闭式读出估计器：前者给出字段作用强度，后者对任意组合给出估计推断精度；
  2. 按门控强度圈出作用较强的字段（最多 22 个），用闭式读出估计器对其中规模不超过 k 的全部组合打分；已重新训练过的组合用真实值；
  3. 单调闭包后，对每类接收方找出估计的最小越线组合（凑齐即越线，去掉任一字段即不越线）；
  4. 列出值得重新训练的组合：估计越线的，以及估计值在判定线下 0.05 以内、且全部子集都不过线的（估计偏低时可能越线）。
  --retrain N：先重新训练上一次列出的前 N 个组合（3 个随机种子取平均），写入推断缓存，再按第 2～4 步重算；
  这些组合从此按重新训练的结果计入，重跑二次定级时也会用到。
结果写到 runtime/cache/<任务>_组合_<保护对象>_k<k>.json，界面读取。"""
import os, sys, json, time, pickle, itertools, argparse
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SYS = os.path.dirname(HERE); ROOT = os.path.dirname(SYS)
for d in ("grading", "infer"):
    sys.path.insert(0, os.path.join(ROOT, "engine", d))
sys.path.insert(0, HERE)
import torch, second, device, review, estimators
from nets import fit_subsets, split
from taskdata import load, catalog_path

ap = argparse.ArgumentParser(); ap.add_argument("task"); ap.add_argument("--target", required=True); ap.add_argument("--k", type=int, default=4)
ap.add_argument("--gpu", default="自动"); ap.add_argument("--retrain", type=int, default=0); ap.add_argument("--keep", type=int, default=22)
a = ap.parse_args(); T0 = time.time(); log = lambda *x: print(f"[{time.time() - T0:5.0f}s]", *x, flush=True)
g, devname = device.pick(a.gpu); dev = "cpu" if g < 0 else f"cuda:{g}"; log("计算设备：", devname)
CACHE = os.path.join(SYS, "runtime", "cache"); D = json.load(open(os.path.join(SYS, "samples", a.task + ".json"), encoding="utf-8"))
meta, base, candd, targd, _ = load(a.task); cand, targ = list(candd), list(targd); n = len(cand)
t = targ.index(a.target); tname = D["敏感"][t]
Xb = np.hstack(list(base.values())) if base else np.zeros((len(next(iter(candd.values()))), 0)); Xs = [candd[c] for c in cand]; Ys = [targd[c] for c in targ]
X = np.hstack([Xb] + Xs); Y = np.hstack(Ys); nb = Xb.shape[1]; off = nb + np.cumsum([0] + [x.shape[1] for x in Xs]); toff = np.cumsum([0] + [y.shape[1] for y in Ys])
tr, te = split(len(X)); groups = [list(range(off[i] - nb, off[i + 1] - nb)) for i in range(n)]

# 1 门控网络（字段作用强度）与闭式读出估计器（组合估计），同一任务只训练一次并缓存
F = estimators.gated(a.task, targ, Xb, np.hstack(Xs), Y, groups, tr, te, dev, CACHE, log)
R = estimators.closed_form(a.task, targ, Xb, np.hstack(Xs), Y, groups, tr, te, dev, CACHE, log)
tmean = lambda r: r[:, toff[t]:toff[t + 1]].mean(1)

# 2 圈定字段，估计全部规模不超过 k 的组合；已重新训练过的组合用真实值
rel, th = F.relevance(90); keep = sorted([int(i) for i in np.argsort(-rel) if rel[i] > th][:a.keep])
OUTF = os.path.join(CACHE, f"{a.task}_组合_{a.target}_k{a.k}.json"); PKL = os.path.join(CACHE, a.task + ".pkl"); CC = pickle.load(open(PKL, "rb"))
if a.retrain and os.path.exists(OUTF):                                       # 重新训练上一次列出的候选组合，写入推断缓存
    todo = [tuple(sorted(cand.index(c) for c in x["组合"])) for x in json.load(open(OUTF, encoding="utf-8")).get("待核对", [])][:a.retrain]
    todo = [s for s in todo if frozenset(s) not in CC["V"]]
    if todo:
        log(f"重新训练 {len(todo)} 个组合（3 个随机种子）")
        masks = np.zeros((len(todo), X.shape[1]), np.float32); masks[:, :nb] = 1
        for r, s in enumerate(todo):
            for i in s:
                masks[r, off[i]:off[i + 1]] = 1
        acc = 0
        for sd in (0, 1, 2):
            r2, _, _ = fit_subsets(X, Y, masks, dev, seed=sd)
            acc = acc + np.stack([r2[:, toff[q]:toff[q + 1]].mean(1) for q in range(len(targ))], 1) / 3
        CC["V"].update({frozenset(s): acc[k] for k, s in enumerate(todo)}); pickle.dump(CC, open(PKL, "wb")); log("已写入推断缓存")
exact = {k: float(np.asarray(v)[t]) for k, v in second.closure(CC["V"], len(targ)).items()}
subs = [()] + [s for k in range(1, a.k + 1) for s in itertools.combinations(keep, k)]
log(f"圈定 {len(keep)} 个字段（共 {n} 个），估计 {len(subs)} 个组合")
est = np.zeros(len(subs))
for lo in range(0, len(subs), 2048):
    est[lo:lo + 2048] = tmean(R.estimate(subs[lo:lo + 2048]))
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

# 4 值得重新训练的组合：估计越线的，以及估计值在线下 0.05 以内、全部子集都不过线的
pend = {}
for c in (1, 2, 3):
    if TL <= c:
        continue
    vis = set(i for i in keep if L1[i] <= c)
    for s, v in V.items():
        if len(s) < 2 or src[s] != "估计" or not s <= vis or v <= LINE[c] - 0.05 or any(V.get(s - {i}, 0.0) > LINE[c] for i in s):
            continue
        if s not in pend or v - LINE[c] > pend[s][0]:
            pend[s] = (v - LINE[c], v, c)
pend = sorted(pend.items(), key=lambda x: -x[1][0])[:60]
for x in found:
    s = frozenset(x["组合"])
    x["子集"] = [dict(字段=[cand[i] for i in sorted(u)], 精度=round(V[frozenset(u)], 3), 来源=src[frozenset(u)]) for k in range(1, len(s)) for u in itertools.combinations(sorted(s), k)]
    x["二次定级后仍成立"] = all(L2[i] <= x["级"] for i in x["组合"])
    x["拆开字段"] = [cand[i] for i in x["组合"] if L2[i] > x["级"]]
    x["组合"] = [cand[i] for i in x["组合"]]
found.sort(key=lambda x: (x["规模"], -x["精度"]))
out = dict(任务=a.task, 保护对象=a.target, 名称=tname, 最大规模=a.k, 圈定字段=[cand[i] for i in keep], 候选字段数=n, 估计组合数=len(subs),
           估计与重训平均绝对误差=round(mae, 3) if mae is not None else None, 组合=found, 设备=devname, 用时秒=round(time.time() - T0, 1),
           待核对=[dict(组合=[cand[i] for i in sorted(s)], 估计=round(v, 3), 接收方=RN[c], 判定线=LINE[c]) for s, (_, v, c) in pend],
           已重训的大组合=sum(1 for s in exact if len(s) > 3))
json.dump(out, open(OUTF, "w", encoding="utf-8"), ensure_ascii=False)
log(f"完成：最小越线组合 {len(found)} 个，其中规模 > 3 的 {sum(x['规模'] > 3 for x in found)} 个；值得重新训练的 {len(pend)} 个")
