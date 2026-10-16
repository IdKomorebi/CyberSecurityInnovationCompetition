# -*- coding: utf-8 -*-
"""二次定级：字段推断敏感度 M → 直接定级 → 联合评估（GRPO）→ 每次调级的依据。

约定：候选字段编号 0..n-1；V 是 {frozenset(字段编号): [对各敏感数据的推断精度]}，包含空集。
接收方按可获取的最高等级 c 区分（1 社会公众，2 关联方，3 特定授权对象，4 内部受控范围）。
"""
import itertools
import numpy as np
import grpo

RECV = {1: "社会公众", 2: "关联方", 3: "特定授权对象", 4: "内部受控范围"}
LINE = {1: 0.7, 2: 0.8, 3: 0.8, 4: 0.8}      # 判定线：社会公众 0.7，其余 0.8


def set_lines(public, other):
    LINE.update({1: float(public), 2: float(other), 3: float(other), 4: float(other)})


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
    """对敏感数据 t，推断精度超过 line 的最小字段组合（去掉任何一个字段就不再超过）。子集没有全部核对过的组合不计入。"""
    if V[frozenset()][t] > line:
        return []
    over = [k for k, v in V.items() if v[t] > line and len(k) > 0 and all(k - {i} in V for i in k)]
    out = [k for k in over if not any(V[k - {i}][t] > line for i in k)]
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
                    out.append(dict(接收方=c, 敏感数据=t, 组合=sorted(k), 精度=float(v), 硬条件=True))
    return out


def grade(L1, t_levels, V, K=2, direct_line=0.7, w=None, locked=None, P=None, strict=False, whole=None, device="cpu"):
    P = dict(grpo.DEFAULT, **(P or {})); n, n_t = len(L1), len(t_levels); w = w or [1.0] * n; locked = set(locked or [])
    V = closure(V, n_t); M, W = sensitivity(V, n, n_t, K)
    combos = {(t, line): [(k, V[k][t]) for k in minimal_over(V, t, line)] for t in range(n_t) for line in set(LINE.values())}
    direct = list(L1); why_direct = {}
    for i in range(n):
        for t in range(n_t):
            if i not in locked and M[i, t] >= direct_line and t_levels[t] > direct[i]:
                direct[i] = min(t_levels[t], 4); why_direct[i] = t
    top = min(max(max(t_levels), max(L1)), 4); low = list(direct); high = [direct[i] if i in locked else max(top, direct[i]) for i in range(n)]
    Mmax = M.max(1); S, Cst = grpo.field_table(L1, Mmax, w, P); FT = S + Cst
    cons = [(c, tuple(sorted(k)), grpo.combo_weight(v, LINE[c], P)) for c in RECV if c <= 3 for t, lt in enumerate(t_levels) if lt > c for k, v in combos[(t, LINE[c])]]

    def pen(a):
        return float(sum(x for c, k, x in cons if all(a[i] <= c for i in k)))

    def wpen(a):
        if whole is None:
            return 0.0
        import torch
        return float(whole(torch.tensor([list(a)], device=device))[0])

    def util(a):
        return float(sum(FT[i, a[i] - 1] for i in range(n))) - pen(a) - wpen(a)

    def parts(a):
        return dict(安全收益=round(float(sum(S[i, a[i] - 1] for i in range(n))), 3), 可用性成本=round(float(sum(Cst[i, a[i] - 1] for i in range(n))), 3), 聚合推断惩罚=round(-pen(a), 3), 整体推断惩罚=round(-wpen(a), 3))

    # 参照：同一效用下的精确最优（严格模式下要求没有越线组合）
    size = int(np.prod([high[i] - low[i] + 1 for i in range(n)], dtype=float)); ref = None; ref_how = "含整体推断项，未求精确解"
    if whole is not None and size > 7000:
        pass
    elif size <= 300_000:
        bu = None
        for a in itertools.product(*[range(low[i], high[i] + 1) for i in range(n)]):
            if strict and pen(a) > 0:
                continue
            u = util(a)
            if bu is None or u > bu:
                bu, ref = u, list(a)
        ref_how = f"穷举全部 {size} 种方案"
    else:
        ref = _milp(low, high, FT, cons, n, strict); ref_how = "整数规划"
    a, curve = grpo.solve(L1, low, high, Mmax, w, cons, P, strict, device=device, whole=whole)
    a = list(a) if a is not None else list(low); fixes = 0
    if strict:                                       # 严格模式：输出后做硬线检查，仍有越线组合时上调组合中 M 最大的字段
        for _ in range(4 * n):
            act = active(a, t_levels, combos)
            if not act:
                break
            x = act[0]; cand = [i for i in x["组合"] if a[i] < high[i]]
            if not cand:
                break
            i = max(cand, key=lambda i: Mmax[i]); a[i] = max(a[i], x["接收方"] + 1); fixes += 1
    final = a; act0, act1 = active(L1, t_levels, combos), active(final, t_levels, combos)
    info = dict(参数=P, 严格模式=bool(strict), 训练曲线=curve, 效用=round(util(final), 3), 效用构成=parts(final), 硬线检查上调次数=fixes,
                参照最优=round(util(ref), 3) if ref else None, 参照最优求法=ref_how, 参照最优上调字段数=sum(x > y for x, y in zip(ref, L1)) if ref else None,
                只做一次定级=dict(效用=round(util(L1), 3), 构成=parts(L1)), 切断比例=round(1 - len(act1) / len(act0), 4) if act0 else 1.0)
    reasons = {}                                     # 依据：把该字段降回一次等级，看哪些越线组合会重新成立
    for i in range(n):
        if final[i] > L1[i]:
            b = list(final); b[i] = L1[i]; back = [x for x in active(b, t_levels, combos) if i in x["组合"]]; back.sort(key=lambda x: -x["精度"])
            lv = []                                  # 其他字段不动，只改这一个字段的等级时，整套方案的效用
            for l in range(L1[i], max(high[i], final[i]) + 1):
                b2 = list(final); b2[i] = l; lv.append(dict(等级=l, 允许=bool(low[i] <= l <= high[i]), 效用=round(util(b2), 3), 构成=parts(b2),
                                                          含该字段的越线组合=sum(1 for x in active(b2, t_levels, combos) if i in x["组合"])))
            reasons[i] = dict(直接定级=(i in why_direct), 直接定级对应=why_direct.get(i), M=float(M[i].max()), 降回后重新成立的越线组合=back[:5], 重新成立的数量=len(back), 各级效用=lv)
    return dict(M=M, 见证=W, 直接定级=direct, 二次等级=final, 依据=reasons, 越线组合=combos, 求解方式="组相对策略优化（GRPO）",
                一次定级下的越线=act0, 二次定级后的越线=act1, V=V, GRPO=info)


def _milp(low, high, FT, cons, n, strict):
    """同一效用下的精确最优（整数规划）。变量 u[i,c]=1 表示字段 i 的等级不高于 c；等级 = 4 − Σu。非严格时每个越线组合带一个松弛变量。"""
    from scipy.optimize import milp, LinearConstraint, Bounds
    nu = n * 3; ns = 0 if strict else len(cons); idx = lambda i, c: i * 3 + (c - 1)
    obj = np.zeros(nu + ns); lb = np.zeros(nu + ns); ub = np.ones(nu + ns)
    for i in range(n):
        for c in (1, 2, 3):
            obj[idx(i, c)] = -(FT[i, c - 1] - FT[i, c])
            if c < low[i]:
                ub[idx(i, c)] = 0
            if c >= high[i]:
                lb[idx(i, c)] = 1
    A, hi = [], []
    for i in range(n):
        for c in (1, 2):
            r = np.zeros(nu + ns); r[idx(i, c)] = 1; r[idx(i, c + 1)] = -1; A.append(r); hi.append(0)
    for j, (c, k, x) in enumerate(cons):
        r = np.zeros(nu + ns)
        for i in k:
            r[idx(i, c)] = 1
        if not strict:
            r[nu + j] = -1; obj[nu + j] = x
        A.append(r); hi.append(len(k) - 1)
    res = milp(obj, constraints=LinearConstraint(np.array(A), -np.inf, hi), integrality=np.ones(nu + ns), bounds=Bounds(lb, ub), options=dict(time_limit=120))
    if res.x is None:
        return None
    u = np.round(res.x[:nu]).reshape(n, 3); return [int(4 - u[i].sum()) for i in range(n)]
