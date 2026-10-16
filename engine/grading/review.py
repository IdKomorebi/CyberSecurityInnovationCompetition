# -*- coding: utf-8 -*-
"""复核：把大语言模型的初判与复核意见合并，得到最终的一次等级。复核改动过的字段保留初判和理由。"""
import os, json
from first_grade import level_of, kind_of, RULES


def load(catalog_csv, fix_path=None):
    """fix_path：另用一份复核意见（例如某个系统版本自己保存的）；不给时读字段目录旁边的 _复核.json。"""
    base = catalog_csv[:-4]; fp = fix_path if fix_path and os.path.exists(fix_path) else base + "_复核.json"
    rows = json.load(open(base + "_一次定级.json", encoding="utf-8"))
    fix = {r["字段"]: r for r in json.load(open(fp, encoding="utf-8"))} if os.path.exists(fp) else {}
    out = []
    for r in rows["结果"]:
        kind = kind_of(r, r)
        r["一次等级"] = level_of(r["影响对象"], r["影响程度"], kind)
        f = dict(r, 初判={"影响对象": r["影响对象"], "影响程度": r["影响程度"], "等级": r["一次等级"], "理由": r["理由"]}, 复核调整=False)
        if r["字段"] in fix:
            x = fix[r["字段"]]
            f.update(影响对象=x["影响对象"], 影响程度=x["影响程度"], 复核调整=True, 复核理由=x["理由"], 复核来源=x.get("来源", "人工复核"), 一次等级=level_of(x["影响对象"], x["影响程度"], kind))
        out.append(f)
    return out, rows["模型"]
