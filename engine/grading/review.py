# -*- coding: utf-8 -*-
"""复核：把大语言模型的初判与复核意见合并，得到最终的一次等级。复核改动过的字段保留初判和理由。"""
import os, json
from first_grade import level_of, RULES


def load(catalog_csv):
    base = catalog_csv[:-4]
    rows = json.load(open(base + "_一次定级.json", encoding="utf-8"))
    fix = {r["字段"]: r for r in json.load(open(base + "_复核.json", encoding="utf-8"))} if os.path.exists(base + "_复核.json") else {}
    out = []
    for r in rows["结果"]:
        kind = r.get("个人信息类型", ""); kind = kind if kind in RULES["最低参考级别"] else ""
        f = dict(r, 初判={"影响对象": r["影响对象"], "影响程度": r["影响程度"], "等级": r["一次等级"], "理由": r["理由"]}, 复核调整=False)
        if r["字段"] in fix:
            x = fix[r["字段"]]
            f.update(影响对象=x["影响对象"], 影响程度=x["影响程度"], 复核调整=True, 复核理由=x["理由"], 一次等级=level_of(x["影响对象"], x["影响程度"], kind))
        out.append(f)
    return out, rows["模型"]
