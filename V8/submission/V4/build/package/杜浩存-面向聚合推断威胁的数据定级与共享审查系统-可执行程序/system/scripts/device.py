# -*- coding: utf-8 -*-
"""选择计算设备：有显卡时选空闲显存最多的一张，空闲不足时用处理器；没有显卡或没装显卡版深度学习库时用处理器。

查显存用 nvidia-smi 子进程，不在进程里逐张查询：逐张查询会给每张卡都建一个约 380 MB 的上下文，
在共享的服务器上白占别人的显存。nvidia-smi 的编号与本进程看到的编号对不上时（设置了 CUDA_VISIBLE_DEVICES），
才退回逐张查询。"""
import os, subprocess

MIN_FREE_MB = 1800                     # 少于这么多空闲显存就不用这张卡，宁可慢也不要中途显存不足


def gpu_status():
    import torch
    if not torch.cuda.is_available():
        return []
    n = torch.cuda.device_count()
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=index,name,memory.free,memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5, check=True).stdout
        rows = [dict(index=int(a), name=b.strip(), free_mb=int(c), total_mb=int(d)) for a, b, c, d in (l.split(",") for l in out.strip().splitlines())]
        if len(rows) == n and not os.environ.get("CUDA_VISIBLE_DEVICES"):
            return rows
    except Exception:
        pass
    rows = []
    for i in range(n):
        try:
            free, total = torch.cuda.mem_get_info(i)
            rows.append(dict(index=i, name=torch.cuda.get_device_name(i), free_mb=int(free / 2 ** 20), total_mb=int(total / 2 ** 20)))
        except Exception:
            continue
    return rows


def pick(pref="自动"):
    """返回（设备编号，说明）。编号 -1 表示处理器。pref 可以是 自动、处理器 或显卡编号。"""
    pref = str(pref)
    if pref in ("处理器", "cpu", "-1"):
        return -1, "处理器（按要求）"
    if pref.isdigit():
        return int(pref), f"显卡 {pref}（指定）"
    try:
        rows = gpu_status()
    except Exception:
        rows = []
    if not rows:
        return -1, "处理器（未检测到可用显卡）"
    best = max(rows, key=lambda r: r["free_mb"])
    if best["free_mb"] < MIN_FREE_MB:
        return -1, f"处理器（显卡空闲显存都不足 {MIN_FREE_MB} MB）"
    return best["index"], f"显卡 {best['index']}（{best['name']}，空闲 {best['free_mb'] / 1024:.1f} GB）"
