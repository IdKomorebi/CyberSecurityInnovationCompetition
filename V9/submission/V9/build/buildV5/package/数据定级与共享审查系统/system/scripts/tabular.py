# -*- coding: utf-8 -*-
"""上传的数据表：读取（CSV 或 Excel）、逐列画像、按字段目录整理成推断用的数值矩阵。"""
import os, json, warnings
import numpy as np, pandas as pd

KINDS = ("数值", "类别", "时间", "文本")


def read_table(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        return pd.read_excel(path, engine="openpyxl")
    if ext == ".xls":
        return pd.read_excel(path)                              # 需要 xlrd；没有时报错，由服务端提示改存为 xlsx 或 csv
    for enc in ("utf-8-sig", "gb18030"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别文件编码，请另存为 UTF-8 编码的 CSV")


def kind_of(s):
    """判断一列是数值、类别、时间还是文本。"""
    if pd.api.types.is_datetime64_any_dtype(s):
        return "时间"
    if pd.api.types.is_bool_dtype(s):
        return "类别"
    if pd.api.types.is_numeric_dtype(s):
        return "类别" if s.nunique() <= 2 else "数值"
    x = s.dropna().astype(str)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        is_time = len(x) and pd.to_datetime(x.head(200), errors="coerce").notna().mean() > 0.9 and x.str.len().median() >= 8
    if is_time:
        return "时间"
    num = pd.to_numeric(x, errors="coerce")
    if len(x) and num.notna().mean() > 0.95:
        return "数值"
    return "类别" if s.nunique() <= 20 else "文本"


def profile(df):
    out = []
    for c in df.columns:
        s = df[c]; k = kind_of(s); x = s.dropna()
        p = dict(字段=str(c), 类型=k, 缺失比例=round(float(s.isna().mean()), 3), 不同取值数=int(s.nunique()), 示例=[str(v)[:24] for v in x.head(4).tolist()])
        if k == "数值":
            v = pd.to_numeric(x, errors="coerce").dropna()
            p.update(最小=round(float(v.min()), 4), 最大=round(float(v.max()), 4), 均值=round(float(v.mean()), 4))
        elif k == "类别":
            p["取值"] = [str(v)[:16] for v in x.value_counts().index[:8]]
        out.append(p)
    return out


def prepare(df, catalog, time_series):
    """按字段目录把各列整理成数值矩阵：数值列补缺失，类别列做独热编码，时间列与“不参与”的列丢弃。
    时间序列按文件原有的行序使用，不按时间列重排（各地日期写法不同，日、月容易解析颠倒）。
    返回 {字段: 二维数组}，以及每个字段所属的角色。"""
    cols, roles = {}, {}
    for r in catalog:
        c, role = r["字段"], r["角色"]
        if role == "不参与" or r.get("类型") in ("时间", "文本"):
            continue
        s = df[c]
        if r.get("类型") == "数值":
            v = pd.to_numeric(s, errors="coerce")
            v = v.interpolate().ffill().bfill() if time_series else v.fillna(v.median())
            cols[c] = v.to_numpy(float)[:, None]
        else:
            cols[c] = pd.get_dummies(s.astype(str).fillna("缺失")).to_numpy(float)
        roles[c] = role
    return cols, roles
