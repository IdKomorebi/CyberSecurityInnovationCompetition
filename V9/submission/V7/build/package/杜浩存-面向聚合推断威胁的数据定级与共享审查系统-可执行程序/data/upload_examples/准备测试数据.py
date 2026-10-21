# -*- coding: utf-8 -*-
"""把 data/raw/ 下从 UCI 机器学习库下载的公开数据集整理成可以直接在“新建任务”里上传的表格。
用法：python data/upload_examples/准备测试数据.py"""
import os, zipfile
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(os.path.dirname(HERE), "raw")
out = lambda name: os.path.join(HERE, name)
z = lambda d, f: zipfile.ZipFile(os.path.join(RAW, d, "download.zip")).open(f)        # 直接从下载的压缩包里读，不必解压

# 1 PJM 区域电力市场 2025 年逐小时数据：取系统内置 PJM 任务所用的 28 列，存为 Excel（同时检验表格格式的上传）
cat = pd.read_csv(os.path.join(os.path.dirname(HERE), "catalog", "pjm.csv"))
pjm = pd.read_csv(os.path.join(RAW, "pjm", "pjm_rto_hourly_2025_cleaned.csv"))[cat["字段"].tolist()]
pjm.to_excel(out("01_PJM区域电力市场_2025.xlsx"), index=False)

# 2 钢铁企业用电（Steel Industry Energy Consumption）
steel = pd.read_csv(z("steel", "Steel_industry_data.csv"))
steel.to_csv(out("02_钢铁企业用电.csv"), index=False)

# 3 楼宇环境传感器与人员在室（Occupancy Detection）：三个文件按时间合并
occ = pd.concat([pd.read_csv(z("occupancy", f)) for f in ("datatraining.txt", "datatest.txt", "datatest2.txt")])
occ = occ.sort_values("date").drop_duplicates("date").reset_index(drop=True)
occ.to_csv(out("03_楼宇传感器与人员在室.csv"), index=False)

for f in sorted(os.listdir(HERE)):
    if f[:2].isdigit():
        print(f, f"{os.path.getsize(out(f)) / 2 ** 20:.1f} MB")
