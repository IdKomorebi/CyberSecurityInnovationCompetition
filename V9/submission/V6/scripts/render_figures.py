# -*- coding: utf-8 -*-
"""把 figures/src/diagrams.html 中的示意图逐张渲染为图片（figures/fig_*.png）。"""
import os
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRC = os.path.join(HERE, "figures", "src", "diagrams.html")
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1700, "height": 1200}, device_scale_factor=1.5)
    pg.goto("file://" + SRC); pg.wait_for_timeout(800)
    for e in pg.locator(".fig").all():
        fid = e.get_attribute("id"); e.screenshot(path=os.path.join(HERE, "figures", f"fig_{fid[2:]}.png")); print("已渲染", fid)
    b.close()
