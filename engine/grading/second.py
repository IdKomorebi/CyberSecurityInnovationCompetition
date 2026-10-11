# -*- coding: utf-8 -*-
"""二次定级：字段推断敏感度 M → 直接定级 → 整体评估 → 每次调级的依据。

约定：候选字段编号 0..n-1；V 是 {frozenset(字段编号): [对各敏感数据的推断精度]}，包含空集。
接收方按可获取的最高等级 c 区分（1 社会公众，2 关联方，3 特定授权对象，4 内部受控范围）。
"""
import itertools
import numpy as np

RECV = {1: "社会公众", 2: "关联方", 3: "特定授权对象", 4: "内部受控范围"}
LINE = {1: 0.7, 2: 0.8, 3: 0.8, 4: 0.8}      # 判定线：社会公众 0.7（硬条件），其余 0.8（软条件）


def closure(V, n_t):
    """推断精度对字段集合单调：多给字段不会更推不准。按子集取最大补齐。"""
    V = {k: np.asarray(v, float).copy() for k, v in V.items()}; V.setdefault(frozenset(), np.zeros(n_t))
    for k in sorted(V, key=len):
        for i in k:
            s = k - {i}
            if s in V:
                V[k] = np.maximum(V[k], V[s])
    return V


def sensitivity(V, n, n_t, K=2):
    """M[i,t] = max over |T|≤K 的 V(T∪i) − V(T)，并记下取到最大值的 T。"""
    M = np.zeros((n, n_t)); W = [[() for _ in range(n_t)] for _ in range(n)]
    for i in range(n):
        for k in range(K + 1):
            for T in itertools.combinations([j for j in range(n) if j != i], k):
                a, b = frozenset(T) | {i}, frozenset(T)
                if a in V and b in V:
                    g = V[a] - V[b]
                    for t in range(n_t):
                        if g[t] > M[i, t]:
                            M[i, t] = g[t]; W[i][t] = T
    return M, W


def minimal_over(V, t, line):
    """对敏感数据 t，推断精度超过 line 的最小字段组合（去掉任何一个字段就不再超过）。"""
    over = [k for k, v in V.items() if v[t] > line and len(k) > 0]
    out = [k for k in over if not any(k - {i} in V and V[k - {i}][t] > line for i in k) and not (V[frozenset()][t] > line)]
    return sorted(out, key=lambda k: (len(k), -V[k][t]))


def active(levels, t_levels, combos):
    """当前等级下仍然成立的越线组合：某类接收方凑得齐全部字段，且无权获取被推断的数据。"""
    out = []
    for c in RECV:
        for t, lt in enumerate(t_levels):
            if lt <= c:
                continue
            for k, v in combos[(t, LINE[c])]:
                if all(levels[i] <= c for i in k):
                    out.append(dict(接收方=c, 敏感数据=t, 组合=sorted(k), 精度=float(v), 硬条件=(c == 1)))
    return out


def grade(L1, t_levels, V, K=2, direct_line=0.7, w=None, rho=1.0, locked=None):
    n, n_t = len(L1), len(t_levels); w = w or [1.0] * n; locked = set(locked or [])
    V = closure(V, n_t); M, W = sensitivity(V, n, n_t, K)
    combos = {(t, line): [(k, V[k][t]) for k in minimal_over(V, t, line)] for t in range(n_t) for line in set(LINE.values())}
    # 直接定级
    direct = list(L1); why_direct = {}
    for i in range(n):
        for t in range(n_t):
            if i not in locked and M[i, t] >= direct_line and t_levels[t] > direct[i]:
                direct[i] = t_levels[t]; why_direct[i] = t
    top = max(max(t_levels), max(L1)); top = min(top, 4)
    rng = [[direct[i]] if i in locked else list(range(direct[i], max(top, direct[i]) + 1)) for i in range(n)]

    def cost(a):
        act = active(a, t_levels, combos)
        if any(x["硬条件"] for x in act):
            return None, act
        return sum(w[i] * (a[i] - L1[i]) for i in range(n)) + rho * sum(t_levels[x["敏感数据"]] - x["接收方"] for x in act), act

    size = int(np.prod([len(r) for r in rng], dtype=float))
    best, best_a = None, None
    if size <= 3_000_000:
        for a in itertools.product(*rng):
            c, _ = cost(a)
            if c is not None and (best is None or c < best - 1e-9):
                best, best_a = c, list(a)
        solver = f"逐一比较全部 {size} 种等级方案，取最优"
    if best_a is None:                      # 方案太多或无可行解时：从直接定级出发，每次上调最划算的一个字段
        a = list(direct); solver = "逐步上调（每次选最划算的一个字段）"
        for _ in range(4 * n):
            c0, act = cost(a); hard = [x for x in act if x["硬条件"]]
            if not act or (not hard and c0 is not None and all(_gain(a, i, cost, rng) <= 0 for i in range(n))):
                break
            tgt = hard or act; cand = {i for x in tgt for i in x["组合"] if a[i] < rng[i][-1]}
            if not cand:
                break
            i = max(cand, key=lambda i: sum(1 for x in tgt if i in x["组合"]) / w[i]); a[i] += 1
        best_a = a; best, _ = cost(a)
    final = best_a; _, act_final = cost(final)
    # 依据：把该字段降回一次等级，看哪些越线组合会重新成立
    reasons = {}
    for i in range(n):
        if final[i] > L1[i]:
            a = list(final); a[i] = L1[i]; back = [x for x in active(a, t_levels, combos) if i in x["组合"]]
            back.sort(key=lambda x: (-x["硬条件"], -x["精度"]))
            reasons[i] = dict(直接定级=(i in why_direct), 直接定级对应=why_direct.get(i), M=float(M[i].max()), 降回后重新成立的越线组合=back[:5], 重新成立的数量=len(back))
    return dict(M=M, 见证=W, 直接定级=direct, 二次等级=final, 依据=reasons, 越线组合=combos, 求解方式=solver, 代价=best,
                一次定级下的越线=active(L1, t_levels, combos), 二次定级后的越线=act_final, V=V)


def _gain(a, i, cost, rng):
    if a[i] >= rng[i][-1]:
        return -1
    b = list(a); b[i] += 1; c0, c1 = cost(a)[0], cost(b)[0]
    return -1 if c1 is None or c0 is None else c0 - c1


def baselines(L1, t_levels, V, res):
    """三种对照做法：只做逐字段定级；单个字段推断精度过线才上调；凡出现在越线组合里的字段一律上调到被推断数据的等级。"""
    n = len(L1); combos = res["越线组合"]; out = {}
    a = list(L1); out["只做逐字段定级"] = a
    b = list(L1)
    for i in range(n):
        for t, lt in enumerate(t_levels):
            if res["V"][frozenset([i])][t] > 0.7:
                b[i] = max(b[i], min(lt, 4))
    out["按单字段相关性上调"] = b
    c = list(L1)
    for x in res["一次定级下的越线"]:
        for i in x["组合"]:
            c[i] = max(c[i], min(t_levels[x["敏感数据"]], 4))
    out["越线组合里的字段一律上调"] = c
    out["本系统"] = res["二次等级"]
    rows = []
    for name, lv in out.items():
        act = active(lv, t_levels, combos)
        rows.append(dict(做法=name, 等级=lv, 上调字段数=sum(x > y for x, y in zip(lv, L1)), 上调级数=sum(x - y for x, y in zip(lv, L1)),
                         公众越线组合=sum(x["硬条件"] for x in act), 其他接收方越线组合=sum(not x["硬条件"] for x in act)))
    return rows
