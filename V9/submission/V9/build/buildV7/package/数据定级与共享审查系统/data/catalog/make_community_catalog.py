# -*- coding: utf-8 -*-
"""社区统计的字段目录：英文字段说明取自数据集自带的说明文件，中文名和中文说明由大语言模型翻译，人工复核后使用。"""
import os, re, sys, json, csv, urllib.request
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, os.path.join(ROOT, "engine", "grading"))
from first_grade import _env
raw = os.path.join(ROOT, "data", "raw", "community"); txt = open(raw + "/communities.names", encoding="latin-1").read()
names = [re.split(r"\s+", l.strip())[1] for l in txt.splitlines() if l.startswith("@attribute")]
c = pd.read_csv(raw + "/communities.data", header=None, names=names, na_values="?").drop(columns=["state", "county", "community", "communityname", "fold"]).dropna(axis=1)
desc = dict(re.findall(r"^-- (\w+): (.+?)(?: \(numeric|\(nominal)", txt, flags=re.M))
TARGET = ["PctPopUnderPov", "medIncome", "PctUnemployed", "PctIlleg", "ViolentCrimesPerPop"]
COND = ["medFamInc", "perCapInc", "whitePerCap", "blackPerCap", "indianPerCap", "AsianPerCap", "OtherPerCap", "HispPerCap", "NumUnderPov", "pctWPubAsst", "pctWInvInc", "pctWSocSec", "pctWRetire", "pctWWage", "pctWFarmSelf", "NumIlleg"]
cfg = _env(); cols = list(c.columns); out = {}
for lo in range(0, len(cols), 25):
    part = {k: desc.get(k, k) for k in cols[lo:lo + 25]}
    body = json.dumps({"model": cfg["DEEPSEEK_MODEL"], "temperature": 0, "response_format": {"type": "json_object"}, "messages": [
        {"role": "system", "content": "把美国社区统计数据集的字段说明翻译成中文。对每个字段给出不超过10个字的中文名和一句中文说明（说明里不要出现英文）。输出 JSON：{字段名:{\"中文名\":\"\",\"说明\":\"\"}}"},
        {"role": "user", "content": json.dumps(part, ensure_ascii=False)}]}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(cfg["DEEPSEEK_BASE_URL"] + "/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + cfg["DEEPSEEK_API_KEY"]}), timeout=120))
    out.update(json.loads(r["choices"][0]["message"]["content"])); print(lo, r["usage"]["total_tokens"], flush=True)
order = [k for k in cols if k not in TARGET] + TARGET
with open(os.path.join(ROOT, "data", "catalog", "community.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["字段", "中文名", "类别", "公开情况", "说明"])
    for k in order:
        st = "未公开" if k in TARGET else "有条件开放" if k in COND else "已公开"
        w.writerow([k, out[k]["中文名"], "公共数据", st, out[k]["说明"] + ("（社区一级的统计量，未对外开放）" if k in TARGET else "")])
print(len(order))
