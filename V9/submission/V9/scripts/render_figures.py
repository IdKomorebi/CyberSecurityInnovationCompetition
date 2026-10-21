# -*- coding: utf-8 -*-
"""把 figures/src 中的示意图逐张渲染为图片（figures/fig_*.png）。
diagrams.html 为宽幅总览图；diagrams_v3.html 为按报告版心（1000 像素宽、大字号）设计的原理图。
用法：python scripts/render_figures.py [diagrams_v3.html ...]（不带参数时渲染全部）"""
import os, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRC = os.path.join(HERE, "figures", "src")
files = sys.argv[1:] or ["diagrams.html", "diagrams_v3.html"]
GPT_FIGS = {"route", "arch", "grade1", "infer", "theory", "regrade", "batch", "gate", "readout", "grpo3", "whole"}
with sync_playwright() as p:
    b = p.chromium.launch()
    for f in files:
        pg = b.new_page(viewport={"width": 1700 if f == "diagrams.html" else 1060, "height": 1200}, device_scale_factor=1.5 if f == "diagrams.html" else 2)
        pg.goto("file://" + os.path.join(SRC, f)); pg.wait_for_timeout(800)
        for e in pg.locator(".fig").all():
            fid = e.get_attribute("id")
            if fid[2:] in GPT_FIGS:                      # 这些图已改用 build/buildV4/scripts 中的矢量重绘版，不再覆盖
                continue
            fid = fid; e.screenshot(path=os.path.join(HERE, "figures", f"fig_{fid[2:]}.png")); print("已渲染", fid)
        pg.close()
    b.close()
