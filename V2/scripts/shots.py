"""Browser inspection: python V2/scripts/shots.py --serve [--browser /path/to/chrome].
Requires Playwright. Screenshots and the report go to V2/runtime/shots (ignored).
"""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['overview', 'grade1', 'risk', 'sens', 'regrade', 'effect', 'tasks', 'rules', 'params', 'policy']
TASKS = ['ieee30', 'insurance', 'community', 'pjm']


def inspect(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    base = f'http://127.0.0.1:{args.port}/frontend/'
    errors, failures = [], []
    checks = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(**({'executable_path': args.browser} if args.browser else {}))
        page = browser.new_page(viewport={'width': 1500, 'height': 1000}, locale='zh-CN', reduced_motion='reduce')
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)

        def visit(task='ieee30', view='overview', extra=''):
            page.goto(f'{base}?task={task}&page={view}{extra}')
            page.wait_for_selector(f'#main[data-ready="{view}"]')
            assert f'task={task}' in page.url, f'Task failed to load: {task}'

        for width, height in [(1500, 1000), (390, 844)]:
            page.set_viewport_size({'width': width, 'height': height})
            for task in TASKS:
                for view in PAGES:
                    visit(task, view)
                    page.wait_for_timeout(120)
                    if page.evaluate('document.documentElement.scrollWidth > innerWidth + 2'):
                        failures.append(f'{task}/{view}/{width}: horizontal overflow')
                    text = page.locator('#main').inner_text()
                    if any(word in text for word in ['undefined', 'NaN', '[object Object]']):
                        failures.append(f'{task}/{view}/{width}: invalid display value')
                    checks += 1
                    if width == 1500 or (task == 'ieee30' and view in ['overview', 'risk', 'grade1']):
                        page.screenshot(path=str(out / f'{task}_{view}_{width}.png'), full_page=True)
            print(f'{width}px: 40 pages checked', flush=True)

        page.set_viewport_size({'width': 1500, 'height': 1000})
        visit(view='grade1')
        page.locator('#field-search').fill('机组报价')
        assert page.locator('tbody tr').count() == 1
        assert '机组报价' in page.locator('.detail-title').inner_text()
        page.locator('#field-search').fill('不存在的字段')
        assert '没有匹配的字段' in page.locator('#main').inner_text()
        checks += 2

        visit(view='risk', extra='&t=2&r=关联方')
        page.locator('[data-step="1"]').click()
        assert page.locator('#curve-score').inner_text() == '0.993'
        page.locator('#receiver').select_option('社会公众')
        assert page.locator('[data-step="1"]').is_disabled()
        page.locator('#receiver').select_option('关联方')
        page.locator('#play-steps').click()
        page.wait_for_function('document.querySelector("#curve-score").textContent === "0.993"')
        page.locator('[data-cell="0"][data-receiver="社会公众"]').click()
        assert '线路潮流' in page.locator('.tab.active').inner_text()
        checks += 4

        visit(view='sens', extra='&t=2')
        page.locator('#sensitivity-k').fill('0')
        first = page.locator('#selected-m').inner_text()
        page.locator('#sensitivity-k').fill('2')
        assert page.locator('#selected-m').inner_text() != first
        page.locator('[data-sens-field]').nth(1).click()
        assert page.locator('[data-sens-field]').nth(1).get_attribute('aria-pressed') == 'true'
        checks += 2

        for task in TASKS:
            visit(task, 'effect')
            source = json.loads((ROOT / 'samples' / f'{task}.json').read_text())
            actual = sum(r['定级后'] > r['判定线'] for r in source['接收方能力'])
            headline = page.locator('.result-head h2').inner_text()
            assert (f'{actual} 项' in headline) if actual else ('均未越线' in headline)
            checks += 1

        visit(view='effect')
        with page.expect_download() as downloaded:
            page.locator('[data-export="csv"]').first.click()
        data = Path(downloaded.value.path()).read_text(encoding='utf-8-sig')
        records = list(csv.reader(io.StringIO(data)))
        assert len(records) == 12 and all(len(row) == len(records[0]) for row in records)
        with page.expect_download() as downloaded:
            page.locator('[data-export="json"]').click()
        exported = Path(downloaded.value.path()).read_bytes()
        assert json.loads(exported)['id'] == 'ieee30'
        visit(view='tasks')
        page.locator('#import-button').click()
        page.locator('#import-file').set_input_files({'name':'bad.json', 'mimeType':'application/json', 'buffer':b'{}'})
        assert '格式不完整' in page.locator('#import-message').inner_text()
        page.locator('#import-file').set_input_files({'name':'result.json', 'mimeType':'application/json', 'buffer':exported})
        page.wait_for_selector('#main[data-ready="overview"]')
        assert 'imported' in page.url
        checks += 4

        visit()
        page.locator('#nav [data-page="risk"]').click()
        page.locator('#nav [data-page="effect"]').click()
        page.go_back()
        assert page.locator('#main').get_attribute('data-ready') == 'risk'
        page.locator('#help-button').click()
        assert page.locator('#dialog').is_visible()
        page.keyboard.press('Escape')
        assert not page.locator('#dialog').is_visible()
        assert page.locator('#help-button').evaluate('(e) => e === document.activeElement')
        page.set_viewport_size({'width':390, 'height':844})
        page.locator('#menu-toggle').click()
        assert page.locator('#sidebar').evaluate('(e) => e.classList.contains("open")')
        page.locator('#nav [data-page="grade1"]').click()
        assert page.locator('#menu-toggle').get_attribute('aria-expanded') == 'false'
        checks += 4

        # Mock only these checks; never launch a GPU job during frontend inspection.
        page.set_viewport_size({'width':1500, 'height':1000})
        status = {'完整方式':False,'可重跑':[],'作业':{'状态':'空闲','任务':'','日志':''}}
        page.route('**/api/status', lambda route: route.fulfill(json=status))
        visit(view='params')
        assert page.locator('#run-params').is_disabled()
        status.update({'完整方式':True,'可重跑':['ieee30']})
        visit(view='params')
        assert page.locator('#run-params').is_enabled()
        page.locator('[data-param="公众判定线"]').fill('0.1')
        page.locator('#run-params').click()
        assert '范围内' in page.locator('#toast').inner_text()
        page.locator('#reset-params').click()
        page.route('**/api/rerun', lambda route: route.fulfill(json={'错误':'测试：服务暂不可用'}))
        page.locator('#run-params').click()
        page.wait_for_function('document.querySelector("#parameter-status").textContent.includes("服务暂不可用")')
        assert page.locator('#run-params').is_enabled()
        checks += 4
        browser.close()
    report = {'checks':checks,'browser_errors':errors,'failures':failures}
    (out / 'inspection.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    if errors or failures:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8782)
    parser.add_argument('--output', default=str(ROOT / 'runtime' / 'shots'))
    parser.add_argument('--browser', default=os.environ.get('CHROMIUM_EXECUTABLE'))
    parser.add_argument('--serve', action='store_true')
    args = parser.parse_args()
    server = None
    try:
        if args.serve:
            server = subprocess.Popen([sys.executable, str(ROOT / 'scripts' / 'serve.py'), str(args.port)], stdout=subprocess.DEVNULL)
            for _ in range(40):
                if server.poll() is not None:
                    raise RuntimeError('Inspection server exited; choose an unused port.')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/api/status', timeout=.4):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Inspection server did not become ready.')
        inspect(args)
    finally:
        if server:
            server.terminate()
            server.wait(timeout=5)
