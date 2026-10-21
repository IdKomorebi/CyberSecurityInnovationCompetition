# -*- coding: utf-8 -*-
"""生成内置演示任务：一次定级（读缓存）→ 推断验证 → 背景预算 K 的选定 → 字段推断风险 → 二次定级 → 处置 → 换模型复测 → 导出 JSON。
用法：python build_samples.py ieee30|insurance|pjm|community [--gpu 0] [--regrade] [--params JSON]"""
import os, sys, json, csv, itertools, argparse, time
os.environ.setdefault("OMP_NUM_THREADS", "8")
import numpy as np, pandas as pd
SYS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # 本版本的目录
ROOT = os.path.dirname(SYS)                                                    # 项目根目录（算法 engine/ 与数据 data/ 各版本共用）
for d in ("grading", "infer", "treat", "verify"):
    sys.path.insert(0, os.path.join(ROOT, "engine", d))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import review, second, actions, independent
from first_grade import RULES, kind_of
from nets import fit_subsets, split
ap = argparse.ArgumentParser(); ap.add_argument("task"); ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--regrade", action="store_true", help="复用已缓存的推断精度，只重做二次定级及之后的步骤"); ap.add_argument("--params", default="", help="JSON：要覆盖的参数")
ap.add_argument("--curves", action="store_true", help="只为聚合推断页导出越线组合的推断曲线（读取已生成的任务文件）")
a = ap.parse_args(); dev = "cpu" if a.gpu < 0 else f"cuda:{a.gpu}"; T0 = time.time(); import pickle
PARAMS = dict(公众判定线=0.7, 其他判定线=0.8, K="自动", 直接定级线=0.7, beta=2.5, lam=1.0, eta=1.0, sigma=0.5, rho=2.0, rho_w=2.0, steps=400, group=128, 严格模式=False)
PARAMS.update(json.loads(a.params) if a.params else {}); CACHE = os.path.join(SYS, "runtime", "cache"); os.makedirs(CACHE, exist_ok=True)
OUT = os.path.join(SYS, "samples", a.task + ".json"); OLD = json.load(open(OUT, encoding="utf-8")) if a.regrade and os.path.exists(OUT) else None
RAW = os.path.join(ROOT, "data", "raw")                                       # 原始数据都在项目内
log = lambda *x: print(f"[{time.time()-T0:5.0f}s]", *x, flush=True)


from taskdata import load, catalog_path                                     # 各任务的数据读取


def fix_path(task):
    """内置任务在界面上修改过的复核意见存在本版本的 runtime/复核/ 下，不改动各版本共用的 data/catalog/。"""
    return os.path.join(SYS, "runtime", "复核", task + "_复核.json")


meta, base, candd, targd, V = load(a.task)
ONLY = PARAMS.get("只保护") or None; TIDX = list(targd).index(ONLY) if ONLY else None      # 只保护某一项保护对象：其余保护对象视为不保护
if ONLY:
    assert a.regrade, "只保护模式需要已缓存的推断精度（--regrade）"; targd = {ONLY: targd[ONLY]}
cand, targ, bids = list(candd), list(targd), list(base); n, nt = len(cand), len(targ)
Xb = np.hstack(list(base.values())) if base else np.zeros((len(next(iter(candd.values()))), 0)); Xs = [candd[c] for c in cand]; Ys = [targd[t] for t in targ]
X = np.hstack([Xb] + Xs); Y = np.hstack(Ys); nb = Xb.shape[1]; off = nb + np.cumsum([0] + [x.shape[1] for x in Xs]); toff = np.cumsum([0] + [y.shape[1] for y in Ys])
tr, te = split(len(X))


def masks_of(subsets):
    m = np.zeros((len(subsets), X.shape[1]), np.float32); m[:, :nb] = 1
    for r, s in enumerate(subsets):
        for i in s:
            m[r, off[i]:off[i + 1]] = 1
    return m


def infer(subsets, Xuse=None, seeds=(0,), keep=None, epochs=80):
    """各字段子集对各项敏感数据的推断精度 [子集数, 敏感数据数]。"""
    acc, pred = 0, None
    for s in seeds:
        r2, p, _ = fit_subsets(X if Xuse is None else Xuse, Y, masks_of(subsets), dev, seed=s, epochs=epochs, keep_pred=keep if s == seeds[0] else None)
        acc = acc + np.stack([r2[:, toff[t]:toff[t + 1]].mean(1) for t in range(nt)], 1) / len(seeds); pred = p if s == seeds[0] else pred
        raw = r2 if s == seeds[0] else raw
    return acc, pred, raw


if a.curves:                                          # 越线组合的推断曲线：每个字段取含它的前 6 个越线组合，训练“组合”与“组合去掉该字段”两个模型
    D0 = json.load(open(OUT, encoding="utf-8")); ci = {nm: i for i, nm in enumerate(D0["候选"])}; key = lambda s: "、".join(D0["候选"][i] for i in s)
    want = {}
    for t, tname in enumerate(D0["敏感"]):
        cs = {}
        for x in D0["一次定级下的越线"]:
            if x["敏感数据"] == tname:
                k = tuple(sorted(ci[nm] for nm in x["组合"])); cs[k] = max(cs.get(k, 0), x["精度"])
        for i in range(n):
            for k in sorted((k for k in cs if i in k), key=lambda k: -cs[k])[:6]:
                want.setdefault(t, set()).update({k, tuple(x for x in k if x != i)})
    subs = sorted({s for v in want.values() for s in v if s or nb}); pos = {s: k for k, s in enumerate(subs)}; log("组合曲线：训练", len(subs), "个模型")
    preds = {}
    for lo in range(0, len(subs), 400):
        _, p_, _ = infer(subs[lo:lo + 400], keep=list(range(len(subs[lo:lo + 400])))); preds.update({lo + k: v for k, v in p_.items()})
    outc = {}
    for t, ss in want.items():
        sh = D0["展示"][D0["敏感"][t]]; comp = toff[t] + sh["分量"]
        o = np.argsort(te) if D0["时间序列"] else np.argsort(Y[te, comp]); o = o[:240] if D0["时间序列"] else o[np.linspace(0, len(o) - 1, min(240, len(o))).astype(int)]
        outc[D0["敏感"][t]] = {key(s): np.round(preds[pos[s]][:, comp][o], 3).tolist() for s in ss if s in pos}
    json.dump(outc, open(OUT.replace(".json", "_组合曲线.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    log("组合曲线完成", {k: len(v) for k, v in outc.items()}); sys.exit(0)

est_info = None; second.set_lines(PARAMS["公众判定线"], PARAMS["其他判定线"]); cpath = os.path.join(CACHE, a.task + ".pkl")
if a.regrade and os.path.exists(cpath):
    cc = pickle.load(open(cpath, "rb")); V, kmax, est_info = cc["V"], cc["kmax"], cc["est_info"]; log("读取已缓存的推断精度", len(V), "个组合")
    if TIDX is not None:
        V = {k_: np.asarray(v_)[[TIDX]] for k_, v_ in V.items()}
elif isinstance(V, str):
    import fast
    kmax = 3; log("训练快速估计模型（同时给出字段作用排序）")
    F = fast.Fast(Xb, np.hstack(Xs), Y, [list(range(off[i] - nb, off[i + 1] - nb)) for i in range(n)], tr, te, dev)
    rel, th = F.relevance(90); keep = [int(i) for i in np.argsort(-rel) if rel[i] > th][:45]
    subs = [()] + [(i,) for i in range(n)] + [tuple(sorted(s)) for k in (2, 3) for s in itertools.combinations(keep, k)]
    tmean = lambda r: np.stack([r[:, toff[t]:toff[t + 1]].mean(1) for t in range(nt)], 1)
    t1 = time.time(); est = tmean(F.estimate(subs)); t_est = time.time() - t1; log(f"快速估计 {len(subs)} 个组合，用时 {t_est:.1f}s")
    near = [k for k in np.argsort(-est.max(1)) if est[k].max() >= 0.7 - 0.15][:2500]; need = {subs[k] for k in near} | {(i,) for i in range(n)} | {()}
    need |= {tuple(sorted(set(s) - {i})) for s in list(need) for i in s}; need |= {tuple(sorted(set(s) - {i})) for s in list(need) for i in s}
    rs = np.random.default_rng(0); rnd = [subs[k] for k in rs.choice(len(subs), 400, replace=False)]; vs = sorted(need | set(rnd))
    t1 = time.time(); r = np.vstack([infer(vs[lo:lo + 600], seeds=(0, 1, 2))[0] for lo in range(0, len(vs), 600)]); t_ver = time.time() - t1
    pos = {s: k for k, s in enumerate(subs)}; ev = np.array([est[pos[s]] for s in vs]); er = np.array([est[pos[s]] for s in rnd]); tr_ = np.array([r[vs.index(s)] for s in rnd])
    est_info = dict(圈定字段数=len(keep), 候选字段数=n, 估计的组合数=len(subs), 估计用时秒=round(t_est, 1), 重新训练核对的组合数=len(vs), 核对用时秒=round(t_ver, 1),
                    平均绝对误差=round(float(np.abs(er - tr_).mean()), 3), 随机抽查数=len(rnd), 抽查中被筛掉却实际越线的=int(((er.max(1) < 0.55) & (tr_.max(1) > 0.7)).sum()),
                    字段作用排序=[dict(序=int(i), 强度=round(float(rel[i]), 3), 入围=bool(i in keep)) for i in np.argsort(-rel)], 门槛=round(float(th), 3))
    V = {frozenset(s): r[k] for k, s in enumerate(vs)}; log("核对完成", {k: v for k, v in est_info.items() if k != "字段作用排序"})
elif V is None:
    kmax = n if n <= 8 else 3
    subs = [()] + [s for k in range(1, kmax + 1) for s in itertools.combinations(range(n), k)] + ([tuple(range(n))] if kmax < n else [])
    log(f"推断验证：逐一训练 {len(subs)} 个字段组合 × 3 个随机种子")
    r = np.zeros((len(subs), nt))
    for lo in range(0, len(subs), 600):
        r[lo:lo + 600] = infer(subs[lo:lo + 600], seeds=(0, 1, 2))[0]
    V = {frozenset(s): r[k] for k, s in enumerate(subs)}
    if not nb:
        V[frozenset()] = np.zeros(nt)
else:
    kmax = n
if not (a.regrade and os.path.exists(cpath)):
    pickle.dump(dict(V=V, kmax=kmax, est_info=est_info), open(cpath, "wb"))
rows, model = review.load(catalog_path(a.task), fix_path(a.task)); by = {r["字段"]: r for r in rows}
L1 = [by[c]["一次等级"] for c in cand]; TL = [by[t]["一次等级"] for t in targ]
GP = {k: PARAMS[k] for k in ("beta", "lam", "eta", "sigma", "rho", "rho_w", "steps", "group")}
cn = lambda i: by[cand[i]]["中文名"]; tn = lambda t: by[targ[t]]["中文名"]; names = lambda k: [cn(i) for i in k]
cols_of = lambda s: list(range(nb)) + [j for i in s for j in range(off[i], off[i + 1])]
vis = lambda L, c: tuple(i for i in range(n) if L[i] <= c); GB = {}


def gb(s, t):
    if (s, t) not in GB:
        GB[(s, t)] = independent.r2(X[:, cols_of(s)], Ys[t], tr, te)
    return GB[(s, t)]


TOPF, POOL, EPS_MEAN, EPS_MAX = 10, 20, 0.01, 0.05


def choose_K():
    """背景预算 K 在 2、3 中选定。审查方不知道接收方手里有什么，K 越大越保守，但字段之间多有冗余，背景增益很快饱和。
    做法：取每个保护对象 M（K = 2）最大的 TOPF 个字段，看 K 从 1 到 2 时它们的 M 平均还涨多少；
      几乎不涨（< EPS_MEAN）就取 K = 2，不再训练；否则再试 K = 3：在 K = 2 的见证背景上逐个加入一个字段（候选取 M 最大的 POOL 个），重新训练，
      若平均再涨不少于 EPS_MEAN 或有字段再涨不少于 EPS_MAX，取 K = 3，否则取 K = 2。
    字段不超过 8 个时全部组合都已精确计算，K = 3 直接精确求出。"""
    global V
    if str(PARAMS["K"]) != "自动":
        return dict(方式="手动", 选定=int(float(PARAMS["K"])))
    if ONLY and OLD and OLD.get("K选择", {}).get("方式") == "自动":             # 只保护一项时沿用整体结果选定的 K
        return dict(OLD["K选择"])
    Vc0 = second.closure(V, nt); MS = {k: second.sensitivity(Vc0, n, nt, k) for k in (0, 1, 2)}
    top = {t: [int(i) for i in np.argsort(-MS[2][0][:, t])[:TOPF]] for t in range(nt)}
    avg = lambda M_: float(np.mean([M_[i, t] for t in range(nt) for i in top[t]]))
    info = dict(方式="自动", 候选=[2, 3], 关注字段数=TOPF, 平均M=[round(avg(MS[k][0]), 3) for k in (0, 1, 2)], 阈值=dict(平均=EPS_MEAN, 单个=EPS_MAX))
    d2 = avg(MS[2][0]) - avg(MS[1][0])
    if d2 < EPS_MEAN and kmax < n:                                      # 已精确算到全部组合时，K = 3 不需另外训练，直接比较
        info.update(选定=2, 依据=f"K 从 1 加到 2 时，风险靠前的字段 M 平均只增加 {d2:.3f}，背景增益已经饱和，不再测试 K = 3。")
        return info
    need = set()
    if kmax < n:                                                       # 未精确算到 4 个字段的组合：在见证背景上逐个加字段试
        for t in range(nt):
            pool = [int(j) for j in np.argsort(-MS[2][0][:, t])[:POOL]]
            for i in top[t]:
                T2 = MS[2][1][i][t]
                for j in pool:
                    if j != i and j not in T2:
                        need |= {tuple(sorted(T2 + (j,))), tuple(sorted(T2 + (j, i)))}
        need = sorted(s for s in need if frozenset(s) not in V)
        if need:
            log(f"测试 K = 3：重新训练 {len(need)} 个组合")
            r = np.vstack([infer(need[lo:lo + 600], seeds=(0, 1, 2))[0] for lo in range(0, len(need), 600)])
            V.update({frozenset(s): r[k] for k, s in enumerate(need)})
            if not ONLY:
                pickle.dump(dict(V=V, kmax=kmax, est_info=est_info), open(cpath, "wb"))
    Vc0 = second.closure(V, nt); M3, W3 = second.sensitivity(Vc0, n, nt, 3)
    inc = [(M3[i, t] - MS[2][0][i, t], i, t) for t in range(nt) for i in top[t]]; d3 = avg(M3) - avg(MS[2][0]); best = max(inc)
    k3 = d3 >= EPS_MEAN or best[0] >= EPS_MAX
    info.update(平均M=info["平均M"] + [round(avg(M3), 3)], 测试方式="精确" if kmax >= n else "在见证背景上逐个加字段", 新训练组合数=len(need),
                增量最大=dict(字段=cn(best[1]), 保护对象=tn(best[2]), K2=round(float(MS[2][0][best[1], best[2]]), 3), K3=round(float(M3[best[1], best[2]]), 3),
                           背景=names(W3[best[1]][best[2]])), 选定=3 if k3 else 2)
    info["依据"] = (f"K 从 1 加到 2，风险靠前的字段 M 平均增加 {d2:.3f}；从 2 加到 3 平均增加 {d3:.3f}，最多的“{cn(best[1])}”增加 {best[0]:.3f}。"
                  + ("背景增益还没有饱和，取 K = 3。" if k3 else f"均低于 {EPS_MEAN}（平均）和 {EPS_MAX}（单个），取 K = 2。"))
    return info


KSEL = choose_K(); KUSE = KSEL["选定"]; log("背景预算", KSEL)
log("二次定级：联合评估开始")
res = second.grade(L1, TL, V, K=KUSE, direct_line=PARAMS["直接定级线"], P=GP, strict=PARAMS["严格模式"])
Vc = res["V"]; L2 = list(res["二次等级"]); G_ = res["GRPO"]

# ---- 整体核对：各类接收方合并全部可获取字段后的推断精度，一律用重新训练的结果；快速估计只用来给候选字段排序 ----
import grpo as _g
RW = float(PARAMS["rho_w"]); STRICT = bool(PARAMS["严格模式"]); MARGIN = 0.02; rounds = []; why2 = {}; steps_log = []; aux = []
S_, C_ = _g.field_table(L1, res["M"].max(1), [1.0] * n, dict(_g.DEFAULT, **GP)); FT = S_ + C_
cells = {c: [t_ for t_ in range(nt) if TL[t_] > c and Vc[frozenset()][t_] <= second.LINE[c]] for c in (1, 2, 3)}


def true_pen(s, c):
    """接收方 c 可获取字段 s 时的整体推断惩罚与各项精度（重新训练，神经网络与梯度提升树取较高）。"""
    if not cells[c] or not s:
        return 0.0, {t_: 0.0 for t_ in cells[c]}
    r = infer([s])[0][0]; v = {t_: float(max(r[t_], gb(s, t_))) for t_ in cells[c]}
    return float(sum(RW * max(v[t_] - second.LINE[c], 0) / 0.1 for t_ in cells[c])), v


def nn_pen(sets, c):
    r = infer(list(sets))[0]; return [float(sum(RW * max(r[k][t_] - second.LINE[c], 0) / 0.1 for t_ in cells[c])) for k in range(len(sets))]


log("整体核对开始")
pen0 = {c: true_pen(vis(L1, c), c) for c in (1, 2, 3)}
if (RW > 0 or STRICT) and any(cells.values()):
    import fast, torch
    Fw = fast.Fast(Xb, np.hstack(Xs), Y, [list(range(off[i] - nb, off[i + 1] - nb)) for i in range(n)], tr, te, dev, n_decoy=0, epochs=300)
    tm = torch.zeros(Y.shape[1], nt, device=dev)
    for t_ in range(nt):
        tm[toff[t_]:toff[t_ + 1], t_] = 1.0 / (toff[t_ + 1] - toff[t_])
    for c in (1, 2, 3):
        if not cells[c]:
            continue
        pen, v = true_pen(vis(L2, c), c); start = max(v.values()) if v else 0.0; raised = []; prev = {}
        over = lambda v_: max(v_[t_] - second.LINE[c] for t_ in cells[c]) if v_ else -1
        path = [(0.0, pen, v)]; acc = 0.0                                    # 路径上每一步的（累计代价，真实惩罚，各项精度）
        for _ in range(n):
            if not (over(v) > -MARGIN):
                break
            s = list(vis(L2, c))
            if len(s) <= 1:
                break
            sel = torch.ones(len(s), n, device=dev) * torch.tensor([1.0 if i in s else 0.0 for i in range(n)], device=dev)
            for k, i in enumerate(s):
                sel[k, i] = 0
            est = (Fw.estimate_sel(sel) @ tm).cpu().numpy()                     # 估计：撤出每个字段后的整体推断精度
            cost = np.array([FT[i, L2[i] - 1] - FT[i, c] for i in s])            # 把字段 i 调到 c+1 级的效用损失（负数表示反而有利）
            epen = np.array([sum(RW * max(est[k][t_] - second.LINE[c], 0) / 0.1 for t_ in cells[c]) for k in range(len(s))])
            topk = np.argsort(epen + cost)[:6]; sets = [tuple(x for x in s if x != s[k]) for k in topk]
            npen = nn_pen(sets, c); aux += [abs(a_ - b_) for a_, b_ in zip(npen, epen[topk])]
            j = int(np.argmin(np.array(npen) + cost[topk])); i = s[topk[j]]; pen2, v2 = true_pen(sets[j], c); acc += float(cost[topk[j]])
            prev[i] = L2[i]; L2[i] = c + 1; raised.append(i); path.append((acc, pen2, v2))
            why2[i] = dict(接收方=second.RECV[c], 敏感数据=tn(max(cells[c], key=lambda t_: v[t_])), 精度=round(max(v.values()), 3), 上调后=round(max(v2.values()), 3))
            pen, v = pen2, v2
        if not STRICT and raised:                                            # 在整条路径上取综合效用最高的位置，其后的上调撤销
            kbest = int(np.argmax([-(a_ + p_) for a_, p_, _ in path]))
            for i in raised[kbest:]:
                L2[i] = prev[i]; why2.pop(i, None)
            raised = raised[:kbest]; _, pen, v = path[kbest]
        back = 0
        for i in reversed(raised[:-1]):                                          # 逐个尝试放回
            old = L2[i]; L2[i] = prev[i]; penb, vb = true_pen(vis(L2, c), c); saved = FT[i, prev[i] - 1] - FT[i, old - 1]
            if (over(vb) <= -MARGIN) if STRICT else (saved - (penb - pen) > 0):
                back += 1; why2.pop(i, None); pen, v = penb, vb
            else:
                L2[i] = old
        if raised or start > second.LINE[c]:
            rounds.append(dict(接收方=second.RECV[c], 核对前推断精度=round(start, 3), 撤出字段数=len(raised), 放回字段数=back, 核对后推断精度=round(max(v.values()), 3) if v else 0.0))
            log("整体核对", rounds[-1])
    res["二次等级"] = L2; res["二次定级后的越线"] = second.active(L2, TL, res["越线组合"])
pen1 = {c: true_pen(vis(L2, c), c) for c in (1, 2, 3)}
fsum = lambda L: (float(sum(S_[i, L[i] - 1] for i in range(n))), float(sum(C_[i, L[i] - 1] for i in range(n))))
for key, L, pp in (("只做一次定级", L1, pen0), ("最终", L2, pen1)):
    s_, c_ = fsum(L); agg = G_["只做一次定级"]["构成"]["聚合推断惩罚"] if key == "只做一次定级" else -sum(_g.combo_weight(x["精度"], second.LINE[x["接收方"]], dict(_g.DEFAULT, **GP)) for x in res["二次定级后的越线"])
    comp = dict(安全收益=round(s_, 3), 可用性成本=round(c_, 3), 聚合推断惩罚=round(float(agg), 3), 整体推断惩罚=round(-sum(p[0] for p in pp.values()), 3))
    if key == "最终":
        G_["效用构成"] = comp; G_["最终效用"] = round(sum(comp.values()), 3)
    else:
        G_["只做一次定级"] = dict(效用=round(sum(comp.values()), 3), 构成=comp)
G_["整体核对"] = dict(快速估计与重新训练的平均偏差=round(float(np.mean(aux)), 3) if aux else None, 候选核对次数=len(aux))
log("二次定级：上调", sum(x > y for x, y in zip(L2, L1)), "个字段；越线组合", len(res["一次定级下的越线"]), "→", len(res["二次定级后的越线"]), "；联合评估效用", G_["效用"], "参照最优", G_["参照最优"], "；最终效用", G_["最终效用"])

# ---- 逐个加入的阶梯与曲线 ----
stairs, curves = (OLD["阶梯"], OLD["曲线"]) if OLD else ([], [])
for t in ([] if OLD else range(nt)):
    act = [x for x in res["一次定级下的越线"] if x["敏感数据"] == t and len(x["组合"]) >= 2]
    if act:
        act.sort(key=lambda x: (x["接收方"], -len(x["组合"]), -x["精度"])); combo = act[0]["组合"]
    else:
        combo = sorted(max((k for k in Vc if 2 <= len(k) <= 3), key=lambda k: Vc[k][t]))
    order = sorted(combo, key=lambda i: Vc[frozenset([i])][t]); pre = ([[]] if nb else []) + [order[:k] for k in range(1, len(order) + 1)]
    r2, pred, raw = infer(pre, keep=list(range(len(pre)))); comp = toff[t] + int(np.argmax(raw[-1, toff[t]:toff[t + 1]]))
    o = np.argsort(te) if meta["时间序列"] else np.argsort(Y[te, comp]); o = o[:240] if meta["时间序列"] else o[np.linspace(0, len(o) - 1, min(240, len(o))).astype(int)]
    lab = lambda p: [cn(i) for i in p] if p else ["仅公开基底"]
    stairs.append(dict(敏感数据=tn(t), 步骤=[dict(加入=(cn(p[-1]) if p else "仅公开基底"), 组合=lab(p), 精度=round(float(max(r2[k, t], Vc.get(frozenset(p), r2[k])[t])), 3),
                                          单独=round(float(Vc[frozenset(p[-1:])][t]), 3)) for k, p in enumerate(pre)]))
    curves.append(dict(敏感数据=tn(t), 真实=np.round(Y[te, comp][o], 3).tolist(), 还原=[dict(组合=lab(p), 值=np.round(pred[k][:, comp][o], 3).tolist()) for k, p in enumerate(pre)]))

# ---- 各类接收方的推断能力：调级前、调级后（按可见的全部字段重新训练） ----
J = lambda x: dict(接收方=second.RECV[x["接收方"]], 敏感数据=tn(x["敏感数据"]), 组合=names(x["组合"]), 精度=round(x["精度"], 3), 硬条件=x["硬条件"])
pairs = [(c, t) for c in (1, 2, 3) for t in range(nt) if TL[t] > c]
sets = sorted({vis(L, c) for c in second.RECV for L in (L1, L2)}); rv = infer(sets, seeds=(0, 1, 2))[0]; RV = {s: rv[k] for k, s in enumerate(sets)}
cap = [dict(接收方=second.RECV[c], 敏感数据=tn(t), 判定线=second.LINE[c], 可见字段数=[len(vis(L1, c)), len(vis(L2, c))],
            定级前=round(float(max(RV[vis(L1, c)][t], gb(vis(L1, c), t))), 3), 定级后=round(float(max(RV[vis(L2, c)][t], gb(vis(L2, c), t))), 3)) for c, t in pairs]
residual = [dict(接收方=second.RECV[c], 敏感数据=tn(t), 精度=round(float(Vc[frozenset()][t]), 3), 判定线=second.LINE[c]) for c, t in pairs if Vc[frozenset()][t] > second.LINE[c]]
log("接收方能力完成；仅凭公开基底即可推出的有", len(residual), "项")

# ---- 换一种模型复测（梯度提升树）：各接收方最终可获取的全部字段 ----
indep = []
for c, t in pairs:
    s = vis(L2, c); s0 = vis(L1, c)
    indep.append(dict(接收方=second.RECV[c], 敏感数据=tn(t), 判定线=second.LINE[c], 神经网络=round(float(RV[s][t]), 3), 梯度提升树=round(gb(s, t), 3),
                      调级前神经网络=round(float(RV[s0][t]), 3), 调级前梯度提升树=round(gb(s0, t), 3)))
log("换模型复测完成")

# ---- 展示用曲线：单字段推断、各接收方合并全部字段、背景增益前后（都在留出数据上，与真实值对照） ----
KSHOW = min(n - 1, max(2, KUSE, len(KSEL.get("平均M", [])) - 1))
if not ONLY:
    def pick_order(comp):
        o = np.argsort(te) if meta["时间序列"] else np.argsort(Y[te, comp])
        return o[:240] if meta["时间序列"] else o[np.linspace(0, len(o) - 1, min(240, len(o))).astype(int)]


    Mk = {K_: second.sensitivity(Vc, n, nt, K_) for K_ in range(KSHOW + 1)}                                          # 背景明细算到 K = 2、3 中算过的最大值
    single_sets = [(i,) for i in range(n)]; recv_sets = [vis(L1, c) for c in (1, 2, 3)]; all_set = [tuple(range(n))]
    gain_items = []
    for t in range(nt):
        Kt = max(Mk); top = sorted(range(n), key=lambda i: -Mk[Kt][0][i, t])[:8]                              # M 最大的 8 个
        amp = sorted(range(n), key=lambda i: -(Mk[Kt][0][i, t] - Mk[0][0][i, t]))                            # 加背景后增加最多的
        top += [i for i in amp if i not in top][:6]
        for i in top:
            gain_items.append((t, i, [tuple(sorted(Mk[K_][1][i][t])) for K_ in sorted(Mk)]))             # 每个 K 下的最危险背景
    gain_sets = sorted({s for _, i, Ts in gain_items for T_ in Ts for s in (T_, tuple(sorted(T_ + (i,)))) if s})
    SH = single_sets + recv_sets + all_set + gain_sets; pos = {s: k for k, s in enumerate(SH)}
    r2s, preds, rawr = infer(SH, keep=list(range(len(SH))))
    show = {}
    for t in range(nt):
        comp = toff[t] + int(np.argmax(rawr[pos[all_set[0]], toff[t]:toff[t + 1]])); o = pick_order(comp)
        val = lambda s: np.round(preds[pos[s]][:, comp][o], 3).tolist()
        gv = lambda s: round(float(Vc[frozenset(s)][t]) if frozenset(s) in Vc else float(r2s[pos[s], t]), 3)
        detail = [dict(字段=cn(i), 背景=[names(Mk[K_][1][i][t]) for K_ in sorted(Mk)], 背景精度=[gv(Mk[K_][1][i][t]) for K_ in sorted(Mk)],
                       合并精度=[gv(tuple(sorted(Mk[K_][1][i][t] + (i,)))) for K_ in sorted(Mk)], M=[round(float(Mk[K_][0][i, t]), 3) for K_ in sorted(Mk)]) for i in range(n)]
        show[tn(t)] = dict(分量=int(comp - toff[t]), 真实=np.round(Y[te, comp][o], 3).tolist(), 背景明细=detail,
            单字段=[dict(字段=cn(i), 精度=gv((i,)), 值=val((i,))) for i in range(n)],
            接收方全部=[dict(接收方=second.RECV[c], 可获取字段数=len(recv_sets[k]), 有权获取=TL[t] <= c, 精度=round(float(max(r2s[pos[recv_sets[k]], t], gb(recv_sets[k], t))), 3) if recv_sets[k] else 0.0, 值=val(recv_sets[k]) if recv_sets[k] else []) for k, c in enumerate((1, 2, 3))],
            背景增益=[dict(字段=cn(i), M=[round(float(Mk[K_][0][i, t]), 3) for K_ in sorted(Mk)], 背景=[names(Mk[K_][1][i][t]) for K_ in sorted(Mk)],
                           背景精度=[gv(Mk[K_][1][i][t]) for K_ in sorted(Mk)], 合并精度=[gv(tuple(sorted(Mk[K_][1][i][t] + (i,)))) for K_ in sorted(Mk)],
                           曲线=[dict(背景=val(T_) if T_ else [], 合并=val(tuple(sorted(T_ + (i,))))) for T_ in Ts]) for (t2, i, Ts) in gain_items if t2 == t])
    log("展示用曲线完成：", len(SH), "个模型")

else:
    show = {}

# ---- 导出 ----
fields = []
for c in bids + cand + targ:
    r = by[c]; f = {k: r[k] for k in ("字段", "中文名", "类别", "公开情况", "说明", "影响对象", "影响程度", "一次等级", "初判", "复核调整", "检索到的条文")}
    f["复核理由"] = r.get("复核理由", ""); f["复核来源"] = r.get("复核来源", ""); f["最低级别"] = max([1] + [RULES["最低参考级别"][k] for k in kind_of(r, r)]); f["角色"] = "公开基底" if c in base else "候选" if c in candd else "敏感"
    if c in candd:
        i = cand.index(c); f.update(直接定级=res["直接定级"][i], 二次等级=L2[i], M=[round(float(v), 3) for v in res["M"][i]],
                                    见证=[names(res["见证"][i][t]) for t in range(nt)], 单独精度=[round(float(v), 3) for v in Vc[frozenset([i])]])
        if i in why2:
            f["整体核对上调"] = why2[i]
        if i in res["依据"]:
            y = res["依据"][i]; f["依据"] = dict(直接定级=y["直接定级"], 对应敏感数据=tn(y["直接定级对应"]) if y["直接定级对应"] is not None else None,
                                            重新成立的数量=y["重新成立的数量"], 重新成立的越线组合=[J(x) for x in y["降回后重新成立的越线组合"]], 各级效用=y["各级效用"])
    else:
        f.update(直接定级=r["一次等级"], 二次等级=r["一次等级"])
    fields.append(f)
if ONLY:                                             # 只保护一项：把结果并入已有任务文件，不覆盖“保护全部”的结果
    sub = dict(参数=PARAMS, K选择=KSEL, 保护对象=tn(0), 字段={f["字段"]: {k_: f[k_] for k_ in ("一次等级", "直接定级", "二次等级", "依据", "整体核对上调", "M") if k_ in f} for f in fields if f["角色"] == "候选"},
               GRPO=res["GRPO"], 一次定级下的越线=[J(x) for x in res["一次定级下的越线"]], 二次定级后的越线=[J(x) for x in res["二次定级后的越线"]],
               接收方能力=cap, 整体核对=rounds, 换模型复测=indep, 仅凭公开基底可推出=residual, 生成耗时秒=round(time.time() - T0))
    OLD = json.load(open(OUT, encoding="utf-8")); OLD.setdefault("单独保护", {})[ONLY] = sub
    json.dump(OLD, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print("单独保护", tn(0), "| 二次", L2, "| 越线组合", len(sub["一次定级下的越线"]), "→", len(sub["二次定级后的越线"])); sys.exit(0)
Kcap = min(n - 1, 4) if kmax >= n else KSHOW; MK = []
for K_ in range(Kcap + 1):
    m_, w_ = second.sensitivity(Vc, n, nt, K_); MK.append(dict(K=K_, M=np.round(m_, 3).tolist(), 见证=[[names(w_[i][t]) for t in range(nt)] for i in range(n)]))
if est_info:
    for x in est_info["字段作用排序"]:
        x["字段"] = cn(x["序"])
out = dict(meta, 展示=show, 背景增益=MK, 参数=PARAMS, K选择=KSEL, 样本数=int(len(X)), 规则库=RULES["标准"], 大语言模型=model, 等级表=RULES["等级"], 判定表=RULES["判定表"], 条文=RULES["条文"],
           接收方=[dict(级=c, 名称=v, 判定线=second.LINE[c]) for c, v in second.RECV.items()], 组合上限=kmax, 已核对的组合数=len(V),
           字段=fields, 候选=[cn(i) for i in range(n)], 敏感=[tn(t) for t in range(nt)], 阶梯=stairs, 曲线=curves, 接收方能力=cap, 仅凭公开基底可推出=residual,
           一次定级下的越线=[J(x) for x in res["一次定级下的越线"]], 二次定级后的越线=[J(x) for x in res["二次定级后的越线"]],
           求解方式=res["求解方式"], GRPO=res["GRPO"], 换模型复测=indep, 整体核对=rounds, 快速估计=est_info, 生成耗时秒=round(time.time() - T0))
if OLD and OLD.get("单独保护"):                         # 参数没变时保留已算好的“只保护某一项”
    same = lambda p_: {k: v for k, v in p_.items() if k != "只保护"} == PARAMS
    out["单独保护"] = {k: v for k, v in OLD["单独保护"].items() if same(v["参数"])}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
import lattice; lattice.add(a.task)                                        # 越线组合页的子集格子数据
print(meta["名称"], "| 一次", L1, "→ 二次", L2, "| 敏感", TL)
for x in cap: print("  能力", x)
print("  越线组合：一次", len(out["一次定级下的越线"]), "二次后", len(out["二次定级后的越线"]), "切断比例", res["GRPO"]["切断比例"], "| 公开基底可推出", len(residual))
