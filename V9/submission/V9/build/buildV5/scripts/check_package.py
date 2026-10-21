"""Verify the freshly unpacked package with standard-library server mode."""
import asyncio,json,urllib.request
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1]
async def main():
 url='http://127.0.0.1:8796';status=json.load(urllib.request.urlopen(url+'/api/status'));assert status['完整方式'] is False
 checks=[];errors=[]
 async with async_playwright() as pw:
  b=await pw.chromium.launch(executable_path='/data1/duhaocun/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell',args=['--no-sandbox'])
  pg=await b.new_page(viewport={'width':1600,'height':900});pg.on('pageerror',lambda e:errors.append(str(e)))
  for page in ['tasks','overview','grade1','single','aggr','combos','regrade','effect']:
   await pg.goto(f'{url}/frontend/?task=nem&t=2&page={page}',wait_until='networkidle');await pg.wait_for_timeout(450)
   txt=await pg.locator('#main').inner_text();assert len(txt)>80,(page,txt)
   assert not await pg.get_by_text('估计器计算失败',exact=False).count(),page
   checks.append({'task':'nem','page':page,'characters':len(txt)})
  for task in ['pjm','ieee30','community','insurance','u20261015234830','u20261015234851']:
   await pg.goto(f'{url}/frontend/?task={task}&page=effect',wait_until='networkidle')
   await pg.locator('.rcards').wait_for();checks.append({'task':task,'page':'effect','loaded':True})
  await b.close()
 assert not errors,errors
 (R/'程序包验证.json').write_text(json.dumps({'stdlib_only':True,'server_python':'/usr/bin/python3','checks':checks,'browser_errors':errors},ensure_ascii=False,indent=2))
 print('Fresh package: standard-library server, 8 NEM pages and 6 other datasets passed.')
asyncio.run(main())
