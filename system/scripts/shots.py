# -*- coding: utf-8 -*-
"""页面巡检：逐页截图，并收集浏览器报错。用法：python shots.py [端口] [输出目录]"""
import sys, os
from playwright.sync_api import sync_playwright
port = sys.argv[1] if len(sys.argv) > 1 else "8780"; out = sys.argv[2] if len(sys.argv) > 2 else "runtime/shots"; os.makedirs(out, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1500, "height": 950}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    for task in ("ieee30", "insurance"):
        for page, extra in ((1, ""), (2, "&t=2&step=9" if task == "ieee30" else "&step=9"), (3, ""), (4, "")):
            pg.goto(f"http://127.0.0.1:{port}/frontend/?task={task}&page={page}{extra}"); pg.wait_for_timeout(1200)
            pg.screenshot(path=f"{out}/{task}_p{page + 1}.png", full_page=True)
    b.close(); print("报错：", errs or "无")
