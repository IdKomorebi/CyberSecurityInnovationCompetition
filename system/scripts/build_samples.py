# -*- coding: utf-8 -*-
"""生成内置演示任务：一次定级（读缓存）→ 推断验证 → 字段推断敏感度 → 二次定级 → 导出给界面用的 JSON。
用法：python build_samples.py ieee30|insurance [--gpu 0]"""
import os, sys, json, itertools, argparse
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "engine", "grading")); sys.path.insert(0, os.path.join(ROOT, "engine", "infer"))
import review, second
from first_grade import RULES
from nets import fit_subsets
ap = argparse.ArgumentParser(); ap.add_argument("task"); ap.add_argument("--gpu", type=int, default=0); a = ap.parse_args(); dev = f"cuda:{a.gpu}"
E08 = "/data1/duhaocun/projects/GNN_Aggresvation/reports/南网/南网claude/实验/08_IEEE30算例分级示例"


def masks_of(subsets, items):
    d = sum(x.shape[1] for x in items); off = np.cumsum([0] + [x.shape[1] for x in items]); m = np.zeros((len(subsets), d), np.float32)
    for r, s in enumerate(subsets):
        for i in s:
            m[r, off[i]:off[i + 1]] = 1
    return m


def load(task):
    if task == "ieee30":
        z = np.load(E08 + "/outputs/case30_dcopf.npz"); d = {k: z[k].astype(float) for k in z.files}
        d["sysload"] = d["load"].sum(1, keepdims=True); d["cong"] = d["cong"][:, d["cong"].mean(0) > 0.005]
        cand = ["sysload", "lmp", "cong", "ren_fc", "reserve", "zone_load", "load", "pg"]; targ = ["flow", "ang", "bid"]
        keys = [s for k in range(1, 9) for s in itertools.combinations(range(8), k)]; Vn = np.load(E08 + "/outputs/V.npy")
        V = {frozenset(k): Vn[r] for r, k in enumerate(keys)}
        meta = dict(id="ieee30", 名称="电力市场标准算例（IEEE 30 节点）", 类别="行业数据", 横轴="时段",
                    数据说明="IEEE 30 节点系统按直流最优潮流逐时段出清生成的运行与市场数据，共 5881 个时段。每个数据项是一类数据（例如线路潮流含 41 条线路），推断精度取各分量的平均。")
        return meta, cand, [d[c] for c in cand], targ, [d[t] for t in targ], V
    if task == "insurance":
        df = pd.read_csv(os.path.join(ROOT, "data", "raw", "insurance.csv"))
        it = {"age": df[["age"]].to_numpy(float), "sex": (df[["sex"]] == "male").to_numpy(float), "bmi": df[["bmi"]].to_numpy(float),
              "children": df[["children"]].to_numpy(float), "smoker": (df[["smoker"]] == "yes").to_numpy(float), "region": pd.get_dummies(df["region"]).to_numpy(float)}
        cand = list(it); meta = dict(id="insurance", 名称="医疗保险个人数据", 类别="个人信息", 横轴="个人（按真实费用排序）",
                                    数据说明="1338 名被保险人的个人属性与年度医疗费用。教学用的公开模拟数据，规模小，用作一眼能看懂的例子。")
        return meta, cand, [it[c] for c in cand], ["charges"], [df[["charges"]].to_numpy(float)], None
    raise SystemExit("未知任务")


meta, cand, Xs, targ, Ys, V = load(a.task); n, nt = len(cand), len(targ)
X = np.hstack(Xs); Y = np.hstack(Ys); toff = np.cumsum([0] + [y.shape[1] for y in Ys])
if V is None:                                  # 小算例：全部子集逐一训练，三个随机种子取平均
    subs = [s for k in range(1, n + 1) for s in itertools.combinations(range(n), k)]
    r2 = np.mean([fit_subsets(X, Y, masks_of(subs, Xs), dev, seed=s)[0] for s in range(3)], 0)
    V = {frozenset(s): np.array([r2[r, toff[t]:toff[t + 1]].mean() for t in range(nt)]) for r, s in enumerate(subs)}
rows, model = review.load(os.path.join(ROOT, "data", "catalog", a.task + ".csv")); by = {r["字段"]: r for r in rows}
L1 = [by[c]["一次等级"] for c in cand]; TL = [by[t]["一次等级"] for t in targ]
locked = [i for i, c in enumerate(cand) if by[c]["公开情况"] == "已公开" and False]
res = second.grade(L1, TL, V, K=2, locked=locked); Vc = res["V"]; cn = lambda i: by[cand[i]]["中文名"]; tn = lambda t: by[targ[t]]["中文名"]

# 每项敏感数据的“逐个加入”阶梯与曲线
stairs, curves = [], []
for t in range(nt):
    act = [x for x in res["一次定级下的越线"] if x["敏感数据"] == t and len(x["组合"]) >= 2]
    if act:
        act.sort(key=lambda x: (x["接收方"], -len(x["组合"]), -x["精度"])); combo = act[0]["组合"]
    else:
        combo = sorted(max((k for k in Vc if 2 <= len(k) <= 3), key=lambda k: Vc[k][t]))
    order = sorted(combo, key=lambda i: Vc[frozenset([i])][t]); order = order[1:] + order[:1] if len(order) > 2 else order
    pre = [order[:k] for k in range(1, len(order) + 1)]; singles = [[i] for i in order[1:]]
    stairs.append(dict(敏感数据=tn(t), 步骤=[dict(加入=cn(p[-1]), 组合=[cn(i) for i in p], 精度=round(float(Vc[frozenset(p)][t]), 3),
                                          单独=round(float(Vc[frozenset([p[-1]])][t]), 3)) for p in pre]))
    r2, pred, te = fit_subsets(X, Y, masks_of(pre, Xs), dev, seed=0, keep_pred=list(range(len(pre))))
    comp = toff[t] + int(np.argmax(r2[-1, toff[t]:toff[t + 1]])); o = np.argsort(te) if meta["横轴"] == "时段" else np.argsort(Y[te, comp])
    o = o[:240] if meta["横轴"] == "时段" else o[np.linspace(0, len(o) - 1, min(240, len(o))).astype(int)]
    curves.append(dict(敏感数据=tn(t), 分量=int(comp - toff[t]), 真实=np.round(Y[te, comp][o], 3).tolist(),
                       还原=[dict(组合=[cn(i) for i in p], 本分量精度=round(float(r2[k, comp]), 3), 值=np.round(pred[k][:, comp][o], 3).tolist()) for k, p in enumerate(pre)]))

names = lambda k: [cn(i) for i in k]
J = lambda x: dict(接收方=second.RECV[x["接收方"]], 敏感数据=tn(x["敏感数据"]), 组合=names(x["组合"]), 精度=round(x["精度"], 3), 硬条件=x["硬条件"])
fields = []
for i, c in enumerate(cand + targ):
    r = by[c]; f = {k: r[k] for k in ("字段", "中文名", "类别", "公开情况", "说明", "影响对象", "影响程度", "一次等级", "初判", "复核调整", "检索到的条文")}
    f["复核理由"] = r.get("复核理由", ""); f["角色"] = "候选" if i < n else "敏感"
    if i < n:
        f.update(直接定级=res["直接定级"][i], 二次等级=res["二次等级"][i], M=[round(float(v), 3) for v in res["M"][i]],
                 见证=[names(res["见证"][i][t]) for t in range(nt)], 单独精度=[round(float(v), 3) for v in Vc[frozenset([i])]])
        if i in res["依据"]:
            y = res["依据"][i]; f["依据"] = dict(直接定级=y["直接定级"], 对应敏感数据=tn(y["直接定级对应"]) if y["直接定级对应"] is not None else None,
                                            重新成立的数量=y["重新成立的数量"], 重新成立的越线组合=[J(x) for x in y["降回后重新成立的越线组合"]])
    else:
        f.update(直接定级=r["一次等级"], 二次等级=r["一次等级"])
    fields.append(f)
cap = []
for c in second.RECV:
    for t in range(nt):
        if TL[t] > c:
            v0 = Vc[frozenset(i for i in range(n) if L1[i] <= c)][t]; v1 = Vc[frozenset(i for i in range(n) if res["二次等级"][i] <= c)][t]
            cap.append(dict(接收方=second.RECV[c], 敏感数据=tn(t), 判定线=second.LINE[c], 可见字段数=[sum(x <= c for x in L1), sum(x <= c for x in res["二次等级"])], 定级前=round(float(v0), 3), 定级后=round(float(v1), 3)))
out = dict(meta, 接收方能力=cap, 样本数=int(len(X)), 规则库=RULES["标准"], 大语言模型=model, 等级表=RULES["等级"], 判定表=RULES["判定表"], 条文=RULES["条文"],
           接收方=[dict(级=c, 名称=v, 判定线=second.LINE[c], 硬条件=(c == 1)) for c, v in second.RECV.items()],
           字段=fields, 候选=[cn(i) for i in range(n)], 敏感=[tn(t) for t in range(nt)], 阶梯=stairs, 曲线=curves,
           一次定级下的越线=[J(x) for x in res["一次定级下的越线"]], 二次定级后的越线=[J(x) for x in res["二次定级后的越线"]],
           对照=[dict(r, 等级=None) for r in second.baselines(L1, TL, V, res)], 求解方式=res["求解方式"],
           全部字段合起来=[round(float(v), 3) for v in Vc[frozenset(range(n))]])
json.dump(out, open(os.path.join(ROOT, "system", "samples", a.task + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
print(meta["名称"]); print("一次", L1, "→ 直判", res["直接定级"], "→ 二次", res["二次等级"], "| 敏感", TL, "|", res["求解方式"])
for s in stairs: print(" ", s["敏感数据"], " → ".join(f"{x['加入']}({x['单独']})={x['精度']}" for x in s["步骤"]))
for r in out["对照"]: print(" ", {k: v for k, v in r.items() if k != "等级"})
print("  越线：一次定级下", len(out["一次定级下的越线"]), "二次定级后", len(out["二次定级后的越线"]))
