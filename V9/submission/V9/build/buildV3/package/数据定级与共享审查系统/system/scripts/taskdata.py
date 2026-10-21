# -*- coding: utf-8 -*-
"""各任务的数据读取（计算脚本与越线组合估计共用）：返回说明、公开基底、候选字段、保护对象、已有的推断精度表。"""
import os, sys, json, itertools
import numpy as np, pandas as pd
SYS = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.dirname(SYS); RAW = os.path.join(ROOT, "data", "raw")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load(task):
    """返回：说明、公开基底（始终可见）、候选字段、敏感数据、已有的推断精度表（没有则为 None）。"""
    if task == "ieee30":
        z = np.load(RAW + "/ieee30/case30_dcopf.npz"); d = {k: z[k].astype(float) for k in z.files}
        d["sysload"] = d["load"].sum(1, keepdims=True); d["cong"] = d["cong"][:, d["cong"].mean(0) > 0.005]
        cand = ["sysload", "lmp", "cong", "ren_fc", "reserve", "zone_load", "load", "pg"]; targ = ["flow", "ang", "bid"]
        keys = [s for k in range(1, 9) for s in itertools.combinations(range(8), k)]; Vn = np.load(RAW + "/ieee30/V.npy")
        meta = dict(id="ieee30", 名称="电力市场标准算例（IEEE 30 节点）", 类别="行业数据", 横轴="时段", 时间序列=True,
                    数据说明="IEEE 30 节点系统按直流最优潮流逐时段出清生成的运行与市场数据，共 5881 个时段。每个数据项是一类数据（例如线路潮流含 41 条线路），推断精度取各分量的平均。")
        return meta, {}, {c: d[c] for c in cand}, {t: d[t] for t in targ}, {frozenset(k): Vn[r] for r, k in enumerate(keys)}
    if task == "insurance":
        df = pd.read_csv(os.path.join(ROOT, "data", "raw", "insurance.csv"))
        it = {"age": df[["age"]].to_numpy(float), "sex": (df[["sex"]] == "male").to_numpy(float), "bmi": df[["bmi"]].to_numpy(float),
              "children": df[["children"]].to_numpy(float), "smoker": (df[["smoker"]] == "yes").to_numpy(float), "region": pd.get_dummies(df["region"]).to_numpy(float)}
        meta = dict(id="insurance", 名称="医疗保险个人数据", 类别="个人信息", 横轴="个人（按真实费用排序）", 时间序列=False,
                    数据说明="1338 名被保险人的个人属性与年度医疗费用。教学用的公开模拟数据，规模小，用作一眼能看懂的例子。")
        return meta, {}, it, {"charges": df[["charges"]].to_numpy(float)}, None
    if task == "pjm":
        cat = pd.read_csv(os.path.join(ROOT, "data", "catalog", "pjm.csv")); cols = cat["字段"].tolist()
        df = pd.read_csv(RAW + "/pjm/pjm_rto_hourly_2025_cleaned.csv")[cols].interpolate().ffill().bfill()
        targ = cols[-4:]; cand = cols[:-4]                                      # 不设公开基底：两项负荷预测也是候选字段，可以调级
        meta = dict(id="pjm", 名称="区域电力市场实测数据（PJM 2025）", 类别="行业数据", 横轴="时段", 时间序列=True,
                    数据说明="美国 PJM 电力市场 2025 年逐小时公开数据，8760 个时段。24 个已公开的负荷预测与市场字段是候选字段；4 项运行数据在本任务中设为未公开的敏感数据。")
        g = lambda c: df[[c]].to_numpy(float)
        return meta, {}, {c: g(c) for c in cand}, {c: g(c) for c in targ}, None
    if task == "nem":
        cat = pd.read_csv(os.path.join(ROOT, "data", "catalog", "nem.csv")); df = pd.read_csv(os.path.join(RAW, "nem", "nem_2024_hourly.csv"))
        targ = [c for c in cat["字段"] if c.startswith("unit_")]; cand = [c for c in cat["字段"] if c not in targ]
        meta = dict(id="nem", 名称="澳大利亚国家电力市场（NEM 2024）", 类别="行业数据", 横轴="时段", 时间序列=True,
                    数据说明="澳大利亚国家电力市场 2024 年逐小时数据，8784 个时段。5 个地区的实际需求、可用发电容量、风电与光伏出力预测、出清电价，以及 6 条区域间联络线潮流共 30 个字段按规定公开，作为候选字段；燃煤、水电、燃气 3 台机组的实际出力属发电企业的商业信息，本任务设为不对外公开的保护对象。")
        g = lambda c: df[[c]].to_numpy(float)
        return meta, {}, {c: g(c) for c in cand}, {c: g(c) for c in targ}, None
    if task == "community":
        import re
        raw = os.path.join(ROOT, "data", "raw", "community"); txt = open(raw + "/communities.names", encoding="latin-1").read()
        nm = [re.split(r"\s+", l.strip())[1] for l in txt.splitlines() if l.startswith("@attribute")]
        df = pd.read_csv(raw + "/communities.data", header=None, names=nm, na_values="?"); cat = pd.read_csv(os.path.join(ROOT, "data", "catalog", "community.csv"))
        cols = cat["字段"].tolist(); targ = cat[cat["公开情况"] == "未公开"]["字段"].tolist(); cand = [c for c in cols if c not in targ]
        meta = dict(id="community", 名称="社区人口经济统计（公共数据）", 类别="公共数据", 横轴="社区（按真实值排序）", 时间序列=False,
                    数据说明="美国 1994 个社区的人口、住房、就业、收入等统计数据（取自公开的人口普查与执法统计合并数据集，数值已归一化到 0 至 1）。本任务假设贫困人口比例等 5 项统计量未对外开放，其余字段已开放或有条件开放。")
        g = lambda c: df[[c]].to_numpy(float)
        return meta, {}, {c: g(c) for c in cand}, {c: g(c) for c in targ}, "fast"
    up = os.path.join(SYS, "runtime", "uploads", task)
    if os.path.isdir(up):                                                         # 界面上传的任务：数据表 + 用户确认过的字段目录
        import tabular
        m = json.load(open(os.path.join(up, "meta.json"), encoding="utf-8")); cat = json.load(open(os.path.join(up, "目录.json"), encoding="utf-8"))
        cols, roles = tabular.prepare(tabular.read_table(os.path.join(up, m["数据文件"])), cat, m["时间序列"])
        cand = [c for c in cols if roles[c] == "候选字段"]; targ = [c for c in cols if roles[c] == "保护对象"]
        if not cand or not targ:
            raise SystemExit("至少需要一个候选字段和一个保护对象")
        meta = dict(id=task, 名称=m["名称"], 类别=m.get("类别", "行业数据"), 横轴="时段" if m["时间序列"] else "样本（按真实值排序）", 时间序列=m["时间序列"],
                    数据说明=m.get("说明") or f"用户上传的数据表，{m['行数']} 行；{len(cand)} 个候选字段，{len(targ)} 项保护对象。")
        return meta, {}, {c: cols[c] for c in cand}, {c: cols[c] for c in targ}, (None if len(cand) <= 30 else "fast")
    raise SystemExit("未知任务")


def catalog_path(task):
    up = os.path.join(SYS, "runtime", "uploads", task, task + ".csv")
    return up if os.path.exists(up) else os.path.join(ROOT, "data", "catalog", task + ".csv")
