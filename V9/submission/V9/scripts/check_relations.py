# -*- coding: utf-8 -*-
"""检验 2.5.3 节 M 与最小越线组合的三条关系（K = 2，判定线 0.7），在全部已重新训练的组合上逐一核对。
用法：python scripts/check_relations.py → 输出到 evidence_relations.json"""
import os, sys, json, pickle, itertools
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SYS = os.path.dirname(os.path.dirname(HERE)); ROOT = os.path.dirname(SYS)
sys.path.insert(0, os.path.join(ROOT, "engine", "grading")); import second
K, TH, EPS = 2, 0.7, 1e-9
out = {}
for task in ("nem", "pjm", "ieee30", "community"):
    raw = pickle.load(open(os.path.join(SYS, "runtime", "cache", task + ".pkl"), "rb"))["V"]; nt = len(next(iter(raw.values())))
    V = second.closure(raw, nt); V = {k: v for k, v in V.items() if len(k) <= K + 1}
    n = max(max(k) for k in V if k) + 1; M = {k_: second.sensitivity(V, n, nt, k_)[0] for k_ in (1, 2)}
    v0 = V[frozenset()]; r1 = r3 = bad1 = bad3 = 0
    for A, va in V.items():
        if not A:
            continue
        for t in range(nt):
            r1 += 1; bad1 += va[t] - v0[t] > sum(M[K][i, t] for i in A) + EPS
            if len(A) >= 2:
                r3 += 1; sub = max(V[frozenset(s)][t] for k in range(len(A)) for s in itertools.combinations(A, k) if frozenset(s) in V)
                bad3 += va[t] - sub > min(M[len(A) - 1][j, t] for j in A) + EPS
    mus = {t: [k for k in second.minimal_over(V, t, TH) if len(k) <= K + 1] for t in range(nt)}
    r2 = bad2 = 0
    for t in range(nt):
        if v0[t] > TH:
            continue
        for i in range(n):
            crit = any(V[T][t] <= TH < V[T | {i}][t] for T in V if len(T) <= K and i not in T and (T | {i}) in V)
            inmus = any(i in k for k in mus[t]); r2 += 1; bad2 += crit != inmus
    out[task] = dict(关系一配对=r1, 关系一违例=int(bad1), 关系二配对=r2, 关系二不一致=int(bad2), 关系三配对=r3, 关系三违例=int(bad3))
    print(task, out[task], flush=True)
tot = {k: sum(v[k] for v in out.values()) for k in next(iter(out.values()))}; out["合计"] = tot; print("合计", tot)
json.dump(out, open(os.path.join(HERE, "evidence_relations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
