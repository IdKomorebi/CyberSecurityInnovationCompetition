"""Record stable full-page views. Narration starts only after each action settles."""
from pathlib import Path
import argparse, asyncio, base64, json, time
from playwright.async_api import async_playwright

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[5]
URL='http://127.0.0.1:8797'
CHROME='/data1/duhaocun/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell'
CSS='''
html,body,body *{overflow-anchor:none!important}
.v2-mark{position:fixed;border:2.5px solid #dc3434;border-radius:12px;pointer-events:none;z-index:9999995;box-sizing:border-box}
.tcard[data-up],.tcards .tcard[data-k^="u2026"]{display:none}
'''

async def main(dry=False):
    rows=json.loads((BASE/'work/takes.json').read_text())
    frames=BASE/'work'/('rehearsal' if dry else 'action_frames');frames.mkdir(exist_ok=True)
    items=[];cuts=[];errors=[];extra=0;origin=0
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
        opts=dict(viewport={'width':1600,'height':800},device_scale_factor=1)
        if not dry:opts.update(record_video_dir=str(BASE/'work/recording'),record_video_size={'width':1600,'height':800})
        ctx=await browser.new_context(**opts);page=await ctx.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.goto(URL+'/frontend/?task=nem&t=2&page=overview',wait_until='networkidle')
        await page.locator('#main .kpis').wait_for();await page.add_style_tag(content=CSS)

        def now():return time.monotonic()-origin-extra
        async def clear():await page.evaluate("document.querySelectorAll('.v2-mark').forEach(e=>e.remove())")
        async def mark(*locs):
            boxes=[]
            for loc in locs:
                b=await loc.first.bounding_box();assert b, 'Missing mark target'
                assert b['y']>=45 and b['y']+b['height']<=798, ('Mark outside viewport',b)
                boxes.append(b)
            await clear()
            await page.evaluate('''boxes=>{for(let b of boxes){let e=document.createElement('div');e.className='v2-mark';Object.assign(e.style,{left:(b.x-4)+'px',top:(b.y-4)+'px',width:(b.width+8)+'px',height:(b.height+8)+'px'});document.body.append(e)}}''',boxes)
        async def region(x,y,w,h):
            await clear()
            await page.evaluate('''([x,y,w,h])=>{let e=document.createElement('div');e.className='v2-mark';Object.assign(e.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px'});document.body.append(e)}''',[x,y,w,h])
        async def click(loc):
            b=await loc.first.bounding_box();assert b
            await page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2,steps=6)
            await loc.first.evaluate('e=>{let y=scrollY;e.click();window.scrollTo({top:y,behavior:"instant"})}')
            await page.mouse.move(210,775,steps=3)
            await page.wait_for_timeout(250)
        async def scroll(loc,top=100):
            await clear()
            await loc.first.evaluate('(e,t)=>window.scrollTo({top:Math.max(0,scrollY+e.getBoundingClientRect().top-t),behavior:"smooth"})',top)
            await page.wait_for_timeout(750)
        async def table_row(loc):
            await loc.first.evaluate('''e=>{let p=e.parentElement;while(p&&!p.classList.contains('scroll'))p=p.parentElement;if(p)p.scrollTo({top:p.scrollTop+e.getBoundingClientRect().top-p.getBoundingClientRect().top-p.clientHeight/3,behavior:'smooth'})}''')
            await page.wait_for_timeout(400)
        def card(s):return page.locator('.card').filter(has=page.locator('h3').filter(has_text=s)).first
        async def board_close():await page.evaluate("document.querySelector('#v2-board')?.remove()")
        async def nav(p):
            await clear();await board_close()
            await page.evaluate('(p)=>{S.sel=null;go(p);window.scrollTo({top:0,behavior:"instant"})}',p)
            await page.wait_for_timeout(800)
        async def close_modal():
            await clear()
            for sel in ['#wx','#mx','#dx']:
                if await page.locator(sel).count():
                    await page.locator(sel).evaluate('e=>e.click()');await page.wait_for_timeout(150);break
        async def board(kind):
            await clear();await board_close()
            if kind=='intro':
                html='''<div class="eyebrow">面向聚合推断威胁的数据定级与共享审查系统</div>
                <h1>逐个字段看起来安全，<br>放在一起，还安全吗？</h1>
                <div class="cols"><div><small>先看字段本身</small><strong>泄露后，会造成多大影响</strong><p>影响对象 · 影响程度 · 字段等级</p></div>
                <div><small>再看字段之间的关联</small><strong>能否推算出需要保护的信息</strong><p>单独推断 · 背景知识 · 字段组合</p></div></div>'''
            elif kind=='end':
                html='''<div class="eyebrow">作品演示</div><h1 style="margin-top:150px">面向聚合推断威胁的<br>数据定级与共享审查系统</h1><p style="margin:60px 90px;font-size:28px">谢谢观看</p>'''
            else:
                f=BASE/'img/结果汇总.png' if kind=='summary' else BASE/'img/开场案例.png'
                html='<img id="board-img" src="data:image/png;base64,'+base64.b64encode(f.read_bytes()).decode()+'">'
            await page.evaluate('''html=>{let e=document.createElement('div');e.id='v2-board';e.style.cssText='position:fixed;inset:0;z-index:9999990;background:#f4f8ff;color:#10243f;font-family:Noto Sans CJK SC,sans-serif';e.innerHTML=`<style>
            #v2-board .eyebrow{margin:65px 90px;color:#50698d;font-size:20px;letter-spacing:2px}#v2-board h1{font-size:50px;line-height:1.5;margin:55px 90px;font-weight:750}
            #v2-board .cols{display:flex;gap:32px;margin:60px 90px}#v2-board .cols>div{padding:30px;background:white;border:1px solid #d8e4f3;border-radius:18px;flex:1}
            #v2-board small{display:block;color:#5a78a0;font-size:18px;margin-bottom:18px}#v2-board strong{font-size:26px}#v2-board p{color:#718198;font-size:21px;margin-bottom:0}
            #board-img{width:1600px;height:800px;object-fit:contain;position:absolute;left:0;top:0}
            </style>`+html;document.body.append(e)}''',html)
        async def upload():
            await nav('tasks');await click(page.locator('#new'))
            await page.locator('#nt').fill('PJM 区域电力市场 2025（videoV2 演示）')
            await page.locator('#nf').set_input_files(str(ROOT/'data/upload_examples/01_PJM区域电力市场_2025.xlsx'))
            await page.locator('#nn').fill('美国 PJM 电力市场 2025 年逐小时运行与市场数据。机组总发电量、实际网损、总交换功率及净交换功率需要保护，其余数值列作为候选字段。')
            await mark(page.locator('#nf'))
        async def catalog():
            nonlocal extra
            await clear()
            if dry:
                await page.evaluate("""async()=>{let u=await api('/api/upload?任务=u20261014225125');S.up={id:'u20261014225125',step:2,info:u.信息,prof:u.画像,err:''};useDraft(u);wizard()}""")
            else:
                await click(page.locator('#wgo'));start=time.monotonic()-origin
                await page.locator('.wtab').wait_for(timeout=240000)
                spent=time.monotonic()-origin-start
                if spent>2:
                    cuts.append(dict(start=start+1.2,end=start+spent,reason='省略大模型起草目录的后台等待'))
                    extra+=spent-1.2
                (BASE/'work/upload_id.txt').write_text(await page.evaluate('S.up.id'))
            await mark(page.locator('.wsum'))
        async def roles():
            await clear()
            for name in ['total_losses','total_gen','gross_actual_interchange_mw','net_actual_interchange_mw']:
                r=page.locator('.wtab tr').filter(has=page.locator('code').filter(has_text=name)).first
                await r.locator('select[data-f="公开情况"]').select_option('未公开')
                await r.locator('select[data-f="角色"]').select_option('保护对象')
            r=page.locator('.wtab tr').filter(has=page.locator('code').filter(has_text='total_gen')).first
            await r.scroll_into_view_if_needed();await page.wait_for_timeout(500)
            await mark(r.locator('select[data-f="角色"]'),page.locator('#wcnt'))
        async def start_task():
            await clear()
            if not dry:
                await click(page.locator('#wrun'));await page.locator('.wprog').wait_for(timeout=15000)
                await mark(page.locator('.wprog'))
            else:await mark(page.locator('#wrun'))
        async def grade():
            await close_modal();await page.evaluate("()=>{setTask('nem');S.t=2;S.scope='all'}")
            await nav('grade1')
            r=page.locator('tr.c').filter(has_text='南澳风电出力预测');await table_row(r);await click(r)
            await scroll(page.locator('.split'),100)
            await mark(page.locator('.right .mx'))
        async def review():
            await scroll(page.locator('[data-m="review"]'),130)
            await mark(page.locator('[data-m="review"]'))
        async def levels():
            await nav('grade1');await click(page.locator('[data-f="保护对象"]'))
            await mark(page.locator('.left table'))
        async def single():
            await nav('single');await click(page.locator('tr.c').filter(has_text='南澳出清价'))
            await mark(page.locator('.kpis'))
        async def select_k(k):
            await clear();b=await page.locator(f'[data-rk="{k}"]').bounding_box()
            await page.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2)
            await page.mouse.move(210,775);await page.wait_for_timeout(650)
            assert await page.evaluate('S.rk')==k
        async def aggr():
            await nav('aggr');await scroll(page.locator('.split'),90)
            await click(page.locator('tr.c').filter(has_text='南澳风电出力预测'))
            await select_k(0);await mark(page.locator('#dec'))
        async def bg():
            await select_k(3);await mark(page.locator('#dec .bgline'))
        async def ability():await mark(page.locator('#dec'))
        async def m_value():await mark(page.locator('#dec .box').last)
        async def change_k():
            await select_k(1);await mark(page.locator('#dec'))
        async def combos():
            await nav('combos');await click(page.locator('[data-ck="3"]'))
            assert await page.evaluate('verifiedCombos().length')==13
            await scroll(page.locator('.split'),95)
            await mark(page.locator('.left h3'))
        async def lattice():await mark(page.locator('.right .lat'))
        async def members():await mark(page.locator('.right table.mini'))
        async def regrade():
            await nav('regrade');await mark(page.locator('.inbar'))
        async def direct():await mark(page.locator('.inbar .in.m'))
        async def formula():await mark(page.locator('.rlbox'))
        async def term(n):
            a=await page.locator('.fml3 .t'+str(n)).bounding_box();b=await page.locator('.fml3 .k'+str(n)).bounding_box()
            await region(a['x']-5,a['y']-5,max(a['width'],b['width'])+10,b['y']+b['height']-a['y']+10)
        async def train():
            await scroll(page.locator('.kpis'),110);await mark(page.locator('#tc'))
        async def exact():await mark(page.locator('.kpi').last)
        async def field():
            await scroll(page.locator('.split'),95)
            r=page.locator('tr.c').filter(has_text='南澳风电出力预测');await table_row(r);await click(r)
            await mark(page.locator('.right .lvu'))
        async def consequences():
            # Both the utility table and the six reasons remain in the same view.
            await mark(page.locator('.right .lvu'))
        async def counts():
            await scroll(page.locator('.kpis'),130);await mark(page.locator('.kpis'))
        async def effects():
            await nav('effect');await scroll(card('全部保护对象一览'),105)
            await mark(card('换模型复测'))
        async def effects_two():
            mat=card('全部保护对象一览')
            await mark(mat.locator('tr').nth(1),mat.locator('tr').nth(2))
        async def residual():await mark(card('全部保护对象一览').locator('tr').nth(3))

        actions={1:lambda:board('intro'),3:lambda:board('aggr'),5:lambda:region(210,575,1180,125),6:lambda:region(210,155,1180,310),
            7:upload,8:catalog,9:roles,10:start_task,11:grade,13:review,14:levels,15:single,17:aggr,
            18:bg,19:ability,20:m_value,23:lambda:mark(page.locator('#vsel')),24:change_k,
            25:combos,27:lattice,28:members,29:regrade,30:direct,31:formula,32:lambda:term(1),33:lambda:term(2),34:lambda:term(3),35:formula,
            36:train,37:exact,38:field,40:consequences,41:counts,42:effects,43:effects_two,44:residual,46:lambda:board('summary'),47:lambda:board('end')}
        await board('intro')
        if not dry:
            await page.evaluate("""()=>{let e=document.createElement('div');e.id='v2-sync';e.style.cssText='position:fixed;inset:0;background:#ff00ff;z-index:2147483647';document.body.append(e)}""")
            await page.wait_for_timeout(650);await page.locator('#v2-sync').evaluate('e=>e.remove()')
        origin=time.monotonic()
        for i,r in enumerate(rows):
            action_start=now()
            if r['id'] in actions:
                await actions[r['id']]()
                await page.wait_for_timeout(200 if dry else 900)
            start=now()
            await page.screenshot(path=str(frames/f'{r["id"]:02d}.png'))
            bmarks=await page.locator('.v2-mark').evaluate_all('(es)=>es.map(e=>({x:e.offsetLeft,y:e.offsetTop,w:e.offsetWidth,h:e.offsetHeight}))')
            items.append(dict(id=r['id'],action_start=action_start,start=start,end=start+r['duration'],scroll=await page.evaluate('scrollY'),marks=bmarks))
            if not dry:
                remaining=r['duration']-(now()-start)
                if remaining>0:await page.wait_for_timeout(remaining*1000)
                gap=.85 if i==len(rows)-1 or rows[i+1]['section']!=r['section'] else .5
                if r['id'] in [6,19,20,27,30,39,41,44]:gap=1.0
                await page.wait_for_timeout(gap*1000)
            (BASE/'work'/('rehearsal_timeline.json' if dry else 'recorded_timeline.json')).write_text(json.dumps(dict(duration=now(),items=items),ensure_ascii=False,indent=2))
            print('SCENE',r['id'],'start',round(start,2),'hold',round(r['duration'],2),flush=True)
        if not dry:await page.wait_for_timeout(1200)
        duration=now()
        (BASE/'work'/('rehearsal_timeline.json' if dry else 'recorded_timeline.json')).write_text(json.dumps(dict(duration=duration,items=items),ensure_ascii=False,indent=2))
        vid=page.video;await ctx.close()
        if vid:(BASE/'work/recording_path.txt').write_text(str(await vid.path()))
        await browser.close()
        (BASE/'work'/('rehearsal_errors.json' if dry else 'browser_errors.json')).write_text(json.dumps(errors,ensure_ascii=False,indent=2))
        if not dry:(BASE/'work/cuts.json').write_text(json.dumps(cuts,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dry',action='store_true');a=p.parse_args();asyncio.run(main(a.dry))
