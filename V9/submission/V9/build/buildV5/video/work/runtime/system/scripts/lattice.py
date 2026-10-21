# -*- coding: utf-8 -*-
"""为任务文件中每个已核对的最小越线组合补上全部真子集的推断精度（读推断缓存，不重新训练），供“越线组合”页画子集格子图。
用法：python lattice.py <任务> [<任务> ...]；计算脚本生成任务文件后也会自动调用。"""
import os, sys, json, pickle, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); SYS = os.path.dirname(HERE); ROOT = os.path.dirname(SYS)
sys.path.insert(0, os.path.join(ROOT, "engine", "grading")); import second


def add(task):
    p = os.path.join(SYS, "samples", task + ".json"); D = json.load(open(p, encoding="utf-8"))
    V = second.closure(pickle.load(open(os.path.join(SYS, "runtime", "cache", task + ".pkl"), "rb"))["V"], len(D["敏感"]))
    ci = {nm: i for i, nm in enumerate(D["候选"])}; ti = {nm: t for t, nm in enumerate(D["敏感"])}; out = {}
    for x in D["一次定级下的越线"]:
        key = x["敏感数据"] + "|" + "、".join(x["组合"])
        if key in out:
            continue
        idx = sorted(ci[n] for n in x["组合"]); t = ti[x["敏感数据"]]
        out[key] = [[[D["候选"][i] for i in u], round(float(V[frozenset(u)][t]), 3)] for k in range(1, len(idx)) for u in itertools.combinations(idx, k) if frozenset(u) in V]
    D["组合子集"] = out; json.dump(D, open(p, "w", encoding="utf-8"), ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(task, "补充", len(out), "个组合的子集精度")


if __name__ == "__main__":
    for t in sys.argv[1:]:
        add(t)
