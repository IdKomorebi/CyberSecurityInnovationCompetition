# -*- coding: utf-8 -*-
"""根据 evidence.json 与任务结果画测试结果图（figures/chart_*.png）。"""
import os, json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); V8 = os.path.dirname(os.path.dirname(HERE)); FIG = os.path.join(HERE, "figures")
fm.fontManager.addfont("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#94a3b8",
                     "axes.grid": True, "grid.color": "#e2e8f0", "grid.linewidth": .8, "axes.axisbelow": True, "savefig.dpi": 220, "savefig.bbox": "tight"})
E = json.load(open(os.path.join(HERE, "evidence.json"), encoding="utf-8"))
ORDER = ["ieee30", "pjm", "community", "insurance", "u20261015234851", "u20261015234830"]; NAMES = [E[k]["名称"] for k in ORDER]
B1, B2 = "#94a3b8", "#2563eb"

def pair(ax, before, after, title, log=False, fmt="{:d}"):
    x = range(len(ORDER)); w = .38
    a = ax.bar([i - w / 2 for i in x], before, w, color=B1, label="一次定级"); b = ax.bar([i + w / 2 for i in x], after, w, color=B2, label="二次定级")
    for bars in (a, b):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, max(r.get_height(), .6 if log else 0), fmt.format(int(r.get_height())), ha="center", va="bottom", fontsize=9.5, color="#334155")
    ax.set_xticks(list(x)); ax.set_xticklabels(NAMES); ax.set_title(title, fontsize=12.5, loc="left", fontweight="bold"); ax.legend(frameon=False, loc="upper right")
    if log: ax.set_yscale("symlog", linthresh=1); ax.set_ylim(0, 6000)

fig, axs = plt.subplots(1, 2, figsize=(13, 4.2))
pair(axs[0], [E[k]["越线组合"][0] for k in ORDER], [E[k]["越线组合"][1] for k in ORDER], "最小越线组合数（对数坐标）", log=True)
pair(axs[1], [E[k]["越线格"][0] for k in ORDER], [E[k]["越线格"][1] for k in ORDER], "越线的“接收方 × 保护对象”情形数")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "chart_combos.png")); plt.close(fig)

# 联合评估与精确最优、只做一次定级的综合效用
fig, ax = plt.subplots(figsize=(13, 4)); x = range(len(ORDER)); w = .27
v0 = [E[k]["效用"]["只做一次定级"] for k in ORDER]; v1 = [E[k]["效用"]["联合评估"] for k in ORDER]; v2 = [E[k]["效用"]["参照最优"] for k in ORDER]
for off, v, c, lab in ((-w, v0, "#cbd5e1", "只做一次定级"), (0, v1, "#2563eb", "联合评估（强化学习）"), (w, v2, "#0f9f6e", "精确最优（穷举或整数规划）")):
    bars = ax.bar([i + off for i in x], v, w, color=c, label=lab)
    for r, val in zip(bars, v): ax.text(r.get_x() + r.get_width() / 2, val, f"{val:.1f}", ha="center", va="top", fontsize=8.5, color="#334155")
ax.set_yscale("symlog", linthresh=10); ax.set_xticks(list(x)); ax.set_xticklabels([f"{n}\n差距 {abs(a - b) / abs(b) * 100:.1f}%" for n, a, b in zip(NAMES, v1, v2)])
ax.set_title("综合效用（越接近 0 越好，对数坐标）", fontsize=12.5, loc="left", fontweight="bold"); ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1, 1.0), ncol=3); ax.set_ylim(-4000, 0)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "chart_utility.png")); plt.close(fig)

# 训练过程：社区统计（95 个字段）与 PJM
fig, axs = plt.subplots(1, 2, figsize=(13, 3.8))
for ax, k in zip(axs, ("community", "pjm")):
    d = json.load(open(os.path.join(V8, "samples", k + ".json"), encoding="utf-8")); cu = d["GRPO"]["训练曲线"]; st = [c["步"] for c in cu]
    ax.plot(st, [c["组内平均"] for c in cu], color="#2563eb", lw=2.2, label="组内平均"); ax.plot(st, [c["组内最好"] for c in cu], color="#93c5fd", lw=1.5, label="组内最好")
    ax.axhline(d["GRPO"]["参照最优"], color="#0f9f6e", ls="--", lw=1.4, label="精确最优"); ax.set_title(f"{E[k]['名称']}：每步采样 128 套方案", fontsize=12.5, loc="left", fontweight="bold")
    ax.set_xlabel("训练步"); ax.set_ylabel("综合效用"); ax.legend(frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "chart_training.png")); plt.close(fig)

# PJM：各接收方调级前后的推断精度（合并全部可获取字段，神经网络与梯度提升树取较高）
S = E["pjm"]; rows = [x for x in S["能力"]]
fig, ax = plt.subplots(figsize=(13, 5.2)); y = range(len(rows))
for i, (r, t, a, b, line, n) in enumerate(rows):
    ax.plot([a, b], [i, i], color="#cbd5e1", lw=3, zorder=1); ax.scatter([a], [i], color="#94a3b8", s=60, zorder=2); ax.scatter([b], [i], color="#e5484d" if b > line else "#0f9f6e", s=80, zorder=3)
    ax.plot([line, line], [i - .38, i + .38], color="#0f1a2e", lw=2); ax.text(1.02, i, f"{a:.3f} → {b:.3f}（可获取字段 {n[0]} → {n[1]}）", va="center", fontsize=10, transform=ax.get_yaxis_transform())
ax.set_yticks(list(y)); ax.set_yticklabels([f"{r} → {t}" for r, t, *_ in rows]); ax.set_xlim(0, 1.0); ax.invert_yaxis()
ax.set_title("PJM 2025：各接收方合并全部可获取字段后的推断精度（灰点调级前，彩点调级后，竖线为判定线）", fontsize=12, loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "chart_pjm.png")); plt.close(fig)
print("完成")
