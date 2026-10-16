# -*- coding: utf-8 -*-
"""截取系统界面（以钢铁企业用电任务为主线），存为 figures/ui_*.png。需要 V8 服务在 8788 端口运行。"""
import os, json, time, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FIG = os.path.join(HERE, "figures"); PROJ = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
B = "http://127.0.0.1:8788"; T = "u20261015234851"; op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
call = lambda p, b=None, raw=False: json.load(op.open(urllib.request.Request(B + p, data=(b if raw else json.dumps(b).encode()) if b is not None else None, method="POST" if b is not None else "GET"), timeout=600))
# 临时上传一份钢铁数据并起草目录，用于截“确认字段目录”这一步，截完删除
f = os.path.join(PROJ, "data", "upload_examples", "01_钢铁企业用电.csv")
tmp = call("/api/upload?name=" + urllib.parse.quote("01_钢铁企业用电.csv") + "&title=" + urllib.parse.quote("钢铁企业用电"), open(f, "rb").read(), raw=True)["任务"]
call("/api/draft", {"任务": tmp, "说明": "一家钢铁企业每15分钟的用电、无功功率、功率因数、碳排放与负荷类型"})
while call("/api/status")["作业"]["状态"] == "运行中": time.sleep(2)
U = f"{B}/frontend/?task={T}&t=0&page="
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1920, "height": 1080}); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    def shot(n, h=1080):                    # 用足够高的窗口截图，不用整页截图（吸顶条和侧栏在整页截图里会错位）
        pg.set_viewport_size({"width": 1920, "height": h}); pg.wait_for_timeout(500); pg.evaluate("window.scrollTo(0, 0)")
        for e in pg.locator("[data-sk]").all(): e.evaluate("e => e.scrollTop = 0")
        pg.wait_for_timeout(500); pg.screenshot(path=os.path.join(FIG, f"ui_{n}.png"))
    pg.goto(U + "tasks"); pg.wait_for_timeout(1500); shot("tasks")
    pg.locator(f'.tcard[data-up="{tmp}"]').click(); pg.wait_for_selector("table.wtab")
    rows = pg.locator("table.wtab tr")
    for i in range(1, rows.count()):
        if rows.nth(i).locator("code").inner_text() in ("Usage_kWh", "Load_Type"):
            pg.select_option(f'select[data-r="{i - 1}"][data-f="角色"]', "保护对象"); pg.wait_for_timeout(150)
    shot("wizard_catalog")
    pg.evaluate(f"openNew('{T}')"); pg.wait_for_selector(".wprog"); pg.wait_for_timeout(1500); shot("wizard_progress")
    pg.goto(U + "grade1"); pg.wait_for_timeout(1500); pg.locator("tr.c", has_text="二氧化碳排放").first.click(); shot("grade1")
    pg.click('[data-m="review"]'); pg.wait_for_timeout(900); shot("review")
    pg.goto(U + "single"); pg.wait_for_timeout(1500); shot("single")
    pg.goto(U + "aggr"); pg.wait_for_timeout(1500); pg.locator("tr.c", has_text="滞后功率因数").first.click(); pg.wait_for_timeout(600)
    cm = pg.locator(".cmb", has_text="当天时刻"); (cm.first.click() if cm.count() else None); pg.wait_for_timeout(1200); shot("aggr", 1720)
    pg.goto(U + "regrade"); pg.wait_for_timeout(1500); pg.locator("tr.c", has_text="滞后功率因数").first.click(); shot("regrade", 1580)
    pg.goto(U + "effect"); pg.wait_for_timeout(1500); shot("effect", 1330)
    pg.goto(U + "aggr&guide=1"); pg.wait_for_timeout(1200); pg.locator(".dw").screenshot(path=os.path.join(FIG, "ui_guide.png"))
    print("页面错误", errs); b.close()
print("删除临时任务", call("/api/delete", {"任务": tmp}).get("已删除"))
