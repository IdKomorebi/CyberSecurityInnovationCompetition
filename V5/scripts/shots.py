# -*- coding: utf-8 -*-
"""页面巡检：逐页截图，并收集浏览器报错。用法：python shots.py [端口] [输出目录] [任务,任务]"""
import sys, os
from playwright.sync_api import sync_playwright
port = sys.argv[1] if len(sys.argv) > 1 else "8780"; out = sys.argv[2] if len(sys.argv) > 2 else "runtime/shots"; os.makedirs(out, exist_ok=True)
tasks = sys.argv[3].split(",") if len(sys.argv) > 3 else ["ieee30", "insurance", "pjm", "community"]
VIEWS = [("tasks", ""), ("overview", ""), ("grade1", "&sel=7"), ("grade1", "&modal=llm"), ("single", "&t=0"), ("aggr", "&t=0"), ("regrade", "&t=0"), ("effect", "&t=0"), ("aggr", "&guide=1")]
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1920, "height": 1000}); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    for task in tasks:
        for k, (page, extra) in enumerate(VIEWS):
            n0 = len(errs); pg.goto(f"http://127.0.0.1:{port}/frontend/?task={task}&page={page}{extra}"); pg.wait_for_timeout(1100)
            pg.screenshot(path=f"{out}/{task}_{k:02d}_{page}.png", full_page=True)
            if len(errs) > n0: print(task, page, extra, errs[n0:])
    b.close(); print("报错总数：", len(errs))
