# -*- coding: utf-8 -*-
"""从系统的任务结果中提取文档要引用的数字，写成 evidence.json，保证文档与系统一致。"""
import os, json
V8 = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TASKS = {"ieee30": "IEEE 30 节点", "pjm": "PJM 2025", "community": "社区统计", "insurance": "医疗保险", "u20261015234851": "钢铁企业用电", "u20261015234830": "楼宇人员在室"}
out = {}
for k, nm in TASKS.items():
    d = json.load(open(os.path.join(V8, "samples", k + ".json"), encoding="utf-8"))
    c = [f for f in d["字段"] if f["角色"] == "候选"]; s = [f for f in d["字段"] if f["角色"] == "敏感"]
    kind = lambda f: "" if f["二次等级"] <= f["一次等级"] else "直接定级" if (f.get("依据") or {}).get("直接定级") else "整体核对" if f.get("整体核对上调") else "联合评估"
    G = d["GRPO"]
    out[k] = dict(名称=nm, 全称=d["名称"], 样本=d["样本数"], 候选=len(c), 保护对象=[(f["中文名"], f["一次等级"]) for f in s], 基底=sum(f["角色"] == "公开基底" for f in d["字段"]),
                  大模型初判=len(d["字段"]), 复核调整=sum(bool(f["复核调整"]) for f in d["字段"]), 组合上限=d["组合上限"], 已核对组合=d["已核对的组合数"],
                  越线组合=[len(d["一次定级下的越线"]), len(d["二次定级后的越线"])], 调高=sum(f["二次等级"] > f["一次等级"] for f in c),
                  方式={m: sum(kind(f) == m for f in c) for m in ("直接定级", "联合评估", "整体核对")},
                  效用=dict(只做一次定级=G["只做一次定级"]["效用"], 联合评估=G["效用"], 参照最优=G["参照最优"], 求法=G["参照最优求法"], 最终=G["最终效用"], 切断比例=G["切断比例"]),
                  越线格=[sum(x["定级前"] > x["判定线"] for x in d["接收方能力"]), sum(x["定级后"] > x["判定线"] for x in d["接收方能力"])],
                  能力=[(x["接收方"], x["敏感数据"], x["定级前"], x["定级后"], x["判定线"], x["可见字段数"]) for x in d["接收方能力"]],
                  复测=[(x["接收方"], x["敏感数据"], x["神经网络"], x["梯度提升树"]) for x in d["换模型复测"]],
                  整体核对=d["整体核对"], 快速估计=({kk: vv for kk, vv in d["快速估计"].items() if kk != "字段作用排序"} if d.get("快速估计") else None),
                  生成耗时秒=d.get("生成耗时秒"), 公开基底可推出=d["仅凭公开基底可推出"])
for k in ("u20261015234851", "u20261015234830", "u20261014225125", "u20261014230351", "u20261014233306"):
    p = os.path.join(V8, "runtime", "uploads", k, "进度.json")
    if os.path.exists(p):
        g = json.load(open(p, encoding="utf-8")); out.setdefault("上传用时", {})[k] = (g["设备"], g["用时秒"])
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in out.items():
    if k == "上传用时": print("上传用时", v); continue
    print(f"== {v['名称']} 样本{v['样本']} 候选{v['候选']} 保护{v['保护对象']} 基底{v['基底']} 复核{v['复核调整']} 组合上限{v['组合上限']} 核对组合{v['已核对组合']}")
    print(f"   越线组合{v['越线组合']} 调高{v['调高']} {v['方式']} 越线格{v['越线格']} 效用{v['效用']} 耗时{v['生成耗时秒']}")
    if v["快速估计"]: print("   快速估计", v["快速估计"])
    print("   整体核对", v["整体核对"])
