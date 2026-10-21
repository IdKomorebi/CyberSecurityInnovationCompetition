# -*- coding: utf-8 -*-
"""估计器的训练与缓存（同一任务、同一组保护对象只训练一次）。
  门控网络（engine/infer/fast.py）：给出字段作用强度与诱饵门槛，用于圈定字段；
  闭式读出估计器（engine/infer/readout.py）：给出任意组合的估计推断精度，用于筛选、当场估计和整体核对的候选排序。"""
import os, hashlib, torch
import fast, readout


def _key(task, targets):
    return task + "_" + hashlib.md5("|".join(targets).encode("utf-8")).hexdigest()[:8]


def gated(task, targets, Xb, Xc, Y, groups, tr, te, dev, cache, log=print):
    p = os.path.join(cache, _key(task, targets) + "_门控网络.pt")
    F = fast.Fast(Xb, Xc, Y, groups, tr, te, dev, epochs=0 if os.path.exists(p) else 300)
    if os.path.exists(p):
        F.net.load_state_dict(torch.load(p, map_location=dev, weights_only=True)); F.net.eval(); log("读取已训练的门控网络")
    else:
        torch.save(F.net.state_dict(), p); log("门控网络训练完成")
    return F


def closed_form(task, targets, Xb, Xc, Y, groups, tr, te, dev, cache, log=print):
    p = os.path.join(cache, _key(task, targets) + "_读出估计器.pt")
    st = torch.load(p, map_location=dev, weights_only=False) if os.path.exists(p) else None
    R = readout.Readout(Xb, Xc, Y, groups, tr, te, dev, state=st)
    if st is None:
        torch.save(R.state(), p); log(f"闭式读出估计器训练完成，λ = {R.alpha}")
    else:
        log("读取已训练的闭式读出估计器")
    return R
