# -*- coding: utf-8 -*-
"""截取系统界面（以 NEM 2024 任务、保护对象“PPCCGT 机组出力”为主线），存为 figures/ui_*.png。需要系统服务在 8788 端口运行。"""
import os, json, time, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); FIG = os.path.join(HERE, "figures"); PROJ = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
# T 为内置 PJM 任务；UPT 为上传测试得到的同一份 PJM 任务，用于展示进度页
B = "http://127.0.0.1:8788"; T = "nem"; UPT = "u20261014225125"; op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
call = lambda p, b=None, raw=False: json.load(op.open(urllib.request.Request(B + p, data=(b if raw else json.dumps(b).encode()) if b is not None else None, method="POST" if b is not None else "GET"), timeout=600))
# 临时上传一份钢铁数据并起草目录，用于截“确认字段目录”这一步，截完删除
f = os.path.join(PROJ, "data", "upload_examples", "01_PJM区域电力市场_2025.xlsx")
tmp = call("/api/upload?name=" + urllib.parse.quote("01_PJM区域电力市场_2025.xlsx") + "&title=" + urllib.parse.quote("PJM 区域电力市场 2025"), open(f, "rb").read(), raw=True)["任务"]
call("/api/draft", {"任务": tmp, "说明": "美国 PJM 电力市场 2025 年逐小时运行与市场数据"})
while call("/api/status")["作业"]["状态"] == "运行中": time.sleep(2)
U = f"{B}/frontend/?task={T}&t=2&page="
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
        if rows.nth(i).locator("code").inner_text() in ("total_losses", "total_gen", "gross_actual_interchange_mw", "net_actual_interchange_mw"):
            pg.select_option(f'select[data-r="{i - 1}"][data-f="角色"]', "保护对象"); pg.wait_for_timeout(150)
    shot("wizard_catalog")
    pg.evaluate(f"openNew('{UPT}')"); pg.wait_for_selector(".wprog"); pg.wait_for_timeout(1500); shot("wizard_progress")
    pg.goto(U + "grade1"); pg.wait_for_timeout(1500); pg.locator("tr.c", has_text="PPCCGT").first.click(); shot("grade1")
    pg.click('[data-m="review"]'); pg.wait_for_timeout(900); shot("review")
    pg.goto(U + "single"); pg.wait_for_timeout(1500); shot("single")
    pg.goto(U + "aggr"); pg.wait_for_timeout(1500); pg.locator("tr.c", has_text="南澳风电出力预测").first.click(); pg.wait_for_timeout(1200); shot("aggr", 1830)
    pg.goto(U + "combos"); pg.wait_for_timeout(1800); shot("combos", 1720)
    pg.goto(U + "regrade"); pg.wait_for_timeout(1500); pg.locator("tr.c", has_text="南澳风电出力预测").first.click(); shot("regrade", 1760)
    pg.goto(U + "effect"); pg.wait_for_timeout(1500); shot("effect", 1330)
    pg.goto(U + "combos&guide=1"); pg.wait_for_timeout(1200); pg.locator(".dw").screenshot(path=os.path.join(FIG, "ui_guide.png"))
    print("页面错误", errs); b.close()
print("删除临时任务", call("/api/delete", {"任务": tmp}).get("已删除"))
