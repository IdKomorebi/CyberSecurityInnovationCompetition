"""Record the approved 65 passages with stable views and word-timed highlights."""
from pathlib import Path
import argparse, asyncio, difflib, json, time
from playwright.async_api import async_playwright
import boards
from prepare import SPEED

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[5]
URL='http://127.0.0.1:8797'
CHROME='/data1/duhaocun/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell'
CSS='''
html,body,body *{overflow-anchor:none!important}
.v7-mark{position:fixed;border:2.5px solid #db343b;border-radius:11px;pointer-events:none;z-index:9999995;box-sizing:border-box}
.tcard[data-up],.tcards .tcard[data-k^="u2026"]:not([data-k="u20261015234830"]):not([data-k="u20261015234851"]){display:none}
.tcards{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:10px!important}
.tcard{min-height:185px!important;padding:18px!important}
.tcard h3{margin:8px 0!important}.tcard .st{margin-top:12px!important}
'''

def cue_time(row, needle):
    meta=json.loads((BASE/f'audio/{row["id"]:02d}.json').read_text()); sentences={}
    for event in meta['events']:
        sent=event.get('output',{}).get('sentence',{}); words=sent.get('words',[])
        if len(words)>=len(sentences.get(sent.get('index',0),[])): sentences[sent.get('index',0)]=words
    spoken=''; times=[]
    for _,words in sorted(sentences.items()):
        for word in words:
            txt=word['text'];a=word['begin_time']/1000/SPEED;b=word['end_time']/1000/SPEED
            spoken+=txt;times.extend(a+(b-a)*j/max(1,len(txt)) for j in range(len(txt)))
    mapping={}
    for block in difflib.SequenceMatcher(None,row['text'],spoken,autojunk=False).get_matching_blocks():
        for j in range(block.size):mapping[block.a+j]=block.b+j
    idx=row['text'].index(needle)
    near=next((j for j in range(idx,min(idx+16,len(row['text']))) if j in mapping),None)
    t=times[mapping[near]] if near is not None else row['duration']*idx/len(row['text'])
    return max(0,min(row['duration']-.4,t-.25))

async def main(dry=False, start_at=1, end_at=65):
    rows=json.loads((BASE/'work/takes.json').read_text())
    frames=BASE/'work'/('rehearsal' if dry else 'action_frames');frames.mkdir(exist_ok=True)
    items=[];cuts=[];errors=[];events=[];origin=0;extra=0
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
        opts=dict(viewport={'width':1600,'height':800},device_scale_factor=1)
        if not dry:opts.update(record_video_dir=str(BASE/'work/recording'),record_video_size={'width':1600,'height':800})
        ctx=await browser.new_context(**opts);page=await ctx.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.goto(URL+'/frontend/?task=nem&t=2&page=overview',wait_until='networkidle')
        await page.locator('#main .kpis').wait_for();await page.add_style_tag(content=CSS)
        def now():return time.monotonic()-origin-extra
        async def clear():await page.evaluate("document.querySelectorAll('.v7-mark').forEach(e=>e.remove())")
        async def boxes_mark(boxes):
            await clear()
            for b in boxes:assert b and b['y']>=5 and b['y']+b['height']<=799,('Mark outside view',b)
            await page.evaluate('''boxes=>{for(const b of boxes){let e=document.createElement('div');e.className='v7-mark';Object.assign(e.style,{left:(b.x-4)+'px',top:(b.y-4)+'px',width:(b.width+8)+'px',height:(b.height+8)+'px'});document.body.append(e)}}''',boxes)
        async def mark(*locs):await boxes_mark([await loc.first.bounding_box() for loc in locs])
        async def group_mark(loc):
            bs=[await loc.nth(i).bounding_box() for i in range(await loc.count())];assert bs
            x=min(b['x'] for b in bs);y=min(b['y'] for b in bs)
            await boxes_mark([dict(x=x,y=y,width=max(b['x']+b['width'] for b in bs)-x,height=max(b['y']+b['height'] for b in bs)-y)])
        async def click(loc):
            b=await loc.first.bounding_box();assert b
            await page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2,steps=8)
            await loc.first.evaluate('e=>{let y=scrollY;e.click();window.scrollTo({top:y,behavior:"instant"})}')
            await page.mouse.move(215,774,steps=5);await page.wait_for_timeout(350)
        async def scroll(loc,top=110):
            await clear();await loc.first.evaluate('(e,t)=>window.scrollTo({top:Math.max(0,scrollY+e.getBoundingClientRect().top-t),behavior:"smooth"})',top)
            await page.wait_for_timeout(850)
        async def table_row(loc):
            await loc.first.evaluate('''e=>{let p=e.parentElement;while(p&&!p.classList.contains('scroll'))p=p.parentElement;if(p)p.scrollTo({top:p.scrollTop+e.getBoundingClientRect().top-p.getBoundingClientRect().top-p.clientHeight/3,behavior:'smooth'})}''')
            await page.wait_for_timeout(500)
        def card(text):return page.locator('.card').filter(has=page.locator('h3').filter(has_text=text)).first
        async def close_board():await page.evaluate("document.querySelector('#v7-board')?.remove()")
        async def board(kind,stage=None):
            await clear();html=getattr(boards,kind)(stage) if stage is not None else getattr(boards,kind)()
            await page.evaluate('''html=>{let e=document.querySelector('#v7-board');if(!e){e=document.createElement('div');e.id='v7-board';document.body.append(e)}e.innerHTML=html}''',html)
        async def close_modal():
            await clear()
            for sel in ['#wx','#mx','#dx']:
                if await page.locator(sel).count():await page.locator(sel).evaluate('e=>e.click()');await page.wait_for_timeout(200);break
        async def nav(name):
            await clear();await close_board()
            await page.evaluate('(p)=>{S.sel=null;go(p);window.scrollTo({top:0,behavior:"instant"})}',name)
            await page.wait_for_timeout(950)
        async def nem_overview():
            await close_modal();await page.evaluate("()=>{setTask('nem');S.t=2;S.scope='all'}");await nav('overview')
        async def upload():
            await click(page.locator('#new'))
            await page.locator('#nt').fill('PJM 区域电力市场 2025（演示任务）')
            await page.locator('#nf').set_input_files(str(ROOT/'data/upload_examples/01_PJM区域电力市场_2025.xlsx'))
            await page.locator('#nn').fill('美国 PJM 电力市场 2025 年逐小时运行与市场数据。机组总发电量、实际网损、总交换功率及净交换功率需要保护，其余数值列作为候选字段。')
            await mark(page.locator('#nf'))
        async def catalog():
            nonlocal extra
            if dry:
                await page.evaluate("""async()=>{let u=await api('/api/upload?任务=u20261014225125');S.up={id:'u20261014225125',step:2,info:u.信息,prof:u.画像,err:''};useDraft(u);wizard()}""")
            else:
                await clear();await click(page.locator('#wgo'));start=time.monotonic()-origin
                await page.locator('.wtab').wait_for(timeout=300000);spent=time.monotonic()-origin-start
                if spent>2:
                    cuts.append(dict(start=start+1.5,end=start+spent,reason='省略目录起草的后台等待'));extra+=spent-1.5
                (BASE/'work/upload_id.txt').write_text(await page.evaluate('S.up.id'))
            assert await page.evaluate('S.up.draft.模型')!='未使用', 'Catalog model unavailable'
        async def roles():
            for name in ['total_losses','total_gen','gross_actual_interchange_mw','net_actual_interchange_mw']:
                loc=page.locator('.wtab tr').filter(has=page.locator('code').filter(has_text=name)).first
                await loc.locator('select[data-f="公开情况"]').select_option('未公开');await loc.locator('select[data-f="角色"]').select_option('保护对象')
            await page.locator('#wrv').select_option('大模型')
            loc=page.locator('.wtab tr').filter(has=page.locator('code').filter(has_text='total_gen')).first
            await loc.scroll_into_view_if_needed();await page.wait_for_timeout(700)
            await mark(loc.locator('select[data-f="角色"]'),page.locator('#wcnt'))
        async def start_task():
            await clear()
            if dry:await page.evaluate("""async()=>{const u=await api('/api/upload?任务=u20261014225125');S.up.prog=u.进度;S.up.info=u.信息;S.up.step=3;wizard()}""")
            else:await click(page.locator('#wrun'));await page.locator('.wprog').wait_for(timeout=20000)
            await mark(page.locator('.wprog'))
        async def progress_step(n):await mark(page.locator('.wprog>div').nth(n))
        async def grade():await nav('grade1');await mark(page.locator('[data-m="llm"]'),page.locator('[data-m="review"]'))
        async def grade_details():
            r=page.locator('tr.c').filter(has_text='南澳风电出力预测');await table_row(r);await click(r);await scroll(page.locator('.split'),95)
            await mark(page.locator('.right .box').first)
        async def grade_table():await scroll(page.locator('.right .mx'),260);await mark(page.locator('.right .mx'))
        async def grade_levels():await nav('grade1');await mark(page.locator('[data-m="levels"]'))
        async def single():
            await nav('single');await click(page.locator('tr.c').filter(has_text='南澳出清价'));await mark(page.locator('.left h3'))
        async def single_curve():await scroll(page.locator('.split'),100);await mark(page.locator('#cv1'))
        async def aggr_overview():await nav('aggr');await scroll(page.locator('#gb'),140)
        async def gain_rows():
            b=await page.locator('#gb').bounding_box();await boxes_mark([dict(x=b['x']+150,y=b['y']+8,width=b['width']*.62,height=104)])
        async def global_k(k):
            await clear();b=await page.locator(f'#K [data-kt="{k}"]').bounding_box();assert b
            await page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2,steps=8)
            await page.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2);await page.mouse.move(215,774,steps=3);await page.wait_for_timeout(800)
            assert await page.evaluate('S.K')==k;await mark(page.locator('#K'))
        async def budget():
            await clear();await click(page.locator('#kt'));await scroll(page.locator('.kcard'),200);await mark(page.locator('.kcard'))
        async def aggr_detail():
            await clear()
            if await page.evaluate('!!S.kOpen'):await click(page.locator('#kt'))
            r=page.locator('tr.c').filter(has_text='南澳风电出力预测');await table_row(r);await click(r);await scroll(page.locator('.split'),95)
            await mark(page.locator('.left h3'))
        async def local_k(k):
            await clear();b=await page.locator(f'[data-rk="{k}"]').bounding_box();assert b
            await page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2,steps=7)
            await page.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2);await page.mouse.move(215,774,steps=4);await page.wait_for_timeout(650)
            assert await page.evaluate('S.rk')==k;await mark(page.locator('#dec'))
        async def witnesses():
            await scroll(page.locator('.right .subpanel'),110);await click(page.locator('[data-wk="1"]'));await mark(page.locator('[data-wk="1"]'),page.locator('#gc'))
        async def witness_two():await click(page.locator('[data-wk="2"]'));await mark(page.locator('[data-wk="2"]'),page.locator('#gc'))
        async def combos():
            await page.evaluate('()=>{S.ck=4;S.cs=null;S.cfl="全部"}');await nav('combos')
            await page.locator('.right .lat').wait_for(timeout=20000);await mark(page.locator('[data-ck="4"]'))
        async def combo_table():await scroll(page.locator('.split'),100);await mark(page.locator('.left h3'))
        async def lattice_start():
            await click(page.locator('tr.c').first);await scroll(page.locator('.right .lat'),190)
            assert '0.811' in await page.locator('.right .lat').text_content()
            await group_mark(page.locator('.lat g.ok rect'))
        async def lattice_level(n):
            loc=page.locator('.lat g.ok rect')
            if n==2:await group_mark(loc.nth(3).or_(loc.nth(4)).or_(loc.nth(5)))
            else:await mark(page.locator('.lat g.ov rect'))
        async def source_column():
            await scroll(page.locator('.split'),100);await page.locator('.left .scroll').evaluate('e=>e.scrollTop=0')
            loc=page.locator('.left tr.c').filter(has_text='估计').first
            if await loc.count():await table_row(loc)
            cells=page.locator('.left tr.c td:nth-child(6)');bs=[]
            for i in range(await cells.count()):
                b=await cells.nth(i).bounding_box()
                if b and b['y']>145 and b['y']+b['height']<740:bs.append(b)
            if bs:
                x=min(b['x'] for b in bs);y=min(b['y'] for b in bs)
                await boxes_mark([dict(x=x,y=y,width=max(b['width'] for b in bs),height=max(b['y']+b['height'] for b in bs)-y)])
        async def regrade():await nav('regrade');await mark(page.locator('.inbar'))
        async def term(n):
            a=await page.locator('.fml3 .t'+str(n)).bounding_box();b=await page.locator('.fml3 .k'+str(n)).bounding_box()
            await boxes_mark([dict(x=a['x'],y=a['y'],width=max(a['width'],b['width']),height=b['y']+b['height']-a['y'])])
        async def train():await scroll(page.locator('.kpis'),125);await mark(page.locator('#tc'))
        async def wind_grade():
            await scroll(page.locator('.split'),95);r=page.locator('tr.c').filter(has_text='南澳风电出力预测');await table_row(r);await click(r)
            await mark(page.locator('.right .lvu'));content=await page.locator('.right .lvu').inner_text()
            assert '-30.17' in content and '-23.64' in content,content
        async def counts():await scroll(page.locator('.kpis'),130);await mark(page.locator('.kpi').nth(0),page.locator('.kpi').nth(1))
        async def effects():
            await nav('effect');await scroll(card('全部保护对象一览'),105);await mark(card('全部保护对象一览').locator('h3'))
        async def effects_two():await mark(card('全部保护对象一览').locator('tr').nth(1),card('全部保护对象一览').locator('tr').nth(2))
        async def tasks_mark(*keys):await mark(*(page.locator(f'.tcard[data-k="{k}"]') for k in keys))
        async def all_tasks():await nav('tasks');await tasks_mark('nem')
        actions={
            1:lambda:board('intro',1),2:lambda:board('intro',2),3:lambda:board('case',3),4:lambda:board('case',4),5:lambda:board('case',5),
            6:lambda:board('case',6),7:lambda:board('case',7),8:lambda:board('case',8),9:lambda:board('analogy'),10:lambda:board('case',10),
            11:lambda:board('case',11),12:lambda:board('case',12),13:lambda:board('case',13),14:lambda:board('case',14),15:lambda:board('solution'),16:nem_overview,
            17:lambda:nav('tasks'),18:upload,19:start_task,20:lambda:progress_step(0),21:lambda:progress_step(1),22:lambda:progress_step(2),23:lambda:progress_step(3),
            24:nem_overview,25:grade,26:grade_details,27:grade_levels,28:single,29:single_curve,30:lambda:mark(page.locator('.right .box')),
            31:clear,32:aggr_overview,33:gain_rows,34:clear,35:lambda:mark(page.locator('#K')),36:aggr_detail,37:lambda:local_k(0),38:lambda:local_k(1),39:lambda:local_k(2),
            40:lambda:mark(page.locator('#dec .box').last),41:witnesses,42:combos,43:lambda:mark(page.locator('[data-ck="4"]')),44:lattice_start,45:source_column,46:clear,
            47:regrade,48:lambda:mark(page.locator('.inbar .in.m')),49:lambda:mark(page.locator('.rlbox')),50:lambda:term(1),51:lambda:term(2),52:lambda:term(3),
            53:train,54:lambda:mark(page.locator('#tc')),55:lambda:mark(page.locator('.kpi').last),56:lambda:mark(page.locator('#uc')),57:wind_grade,
            58:counts,59:effects,60:lambda:mark(card('换模型复测')),61:effects_two,62:lambda:mark(card('全部保护对象一览').locator('tr').nth(3)),
            63:all_tasks,64:lambda:board('summary'),65:nem_overview}
        def during(row):
            d=row['duration']
            def at(needle,fn):return (cue_time(row,needle),fn,needle)
            cases={
                18:lambda:[at('大模型会自动',catalog),at('人工标注',roles)],
                23:lambda:[(d*.58,lambda:progress_step(4),'效果核对')],
                25:lambda:[(d*.62,lambda:mark(page.locator('[data-m="review"]')),'复核模型')],
                27:lambda:[(d*.3,lambda:click(page.locator('[data-f="保护对象"]')),'三台机组等级')],
                35:lambda:[(1.0,lambda:global_k(0),'K = 0'),at('随 K 增大',lambda:global_k(3)),at('脚本会自动',budget)],
                39:lambda:[at('K 等于 3',lambda:local_k(3))],
                41:lambda:[(d*.48,witness_two,'第二组背景与曲线')],43:lambda:[at('每一行',combo_table)],
                44:lambda:[at('三个凑齐',lambda:lattice_level(3))],
                57:lambda:[at('调到 2 级',lambda:mark(page.locator('.right .lvu tr').nth(2)))],
                62:lambda:[at('系统如实列出',lambda:mark(card('换模型复测')))],
                63:lambda:[at('还有 PJM',lambda:tasks_mark('pjm','ieee30')),at('社区统计',lambda:tasks_mark('community','insurance')),at('钢铁企业',lambda:tasks_mark('u20261015234851','u20261015234830'))],
                65:lambda:[(1.0,lambda:mark(page.locator('.pipe')),'全流程'),at('谢谢观看',lambda:board('end'))]}
            return cases.get(row['id'],lambda:[])()
        await board('intro',1)
        if not dry:
            await page.evaluate("""()=>{let e=document.createElement('div');e.id='v7-sync';e.style.cssText='position:fixed;inset:0;background:#ff00ff;z-index:2147483647';document.body.append(e)}""")
            await page.wait_for_timeout(650);await page.locator('#v7-sync').evaluate('e=>e.remove()')
        origin=time.monotonic()
        if start_at>1:
            assert dry, 'Partial starts are only for scene checks.'
            if 17<=start_at<=18:await close_board();await nav('tasks')
            elif 42<=start_at<47:await close_board();await combos();await combo_table()
            elif 47<=start_at<59:await close_board();await regrade()
            elif 59<=start_at<63:await close_board();await effects()
            elif start_at>=63:await close_board();await all_tasks()
            else:raise ValueError('Unsupported rehearsal start')
        for idx,row in enumerate(rows):
            if row['id']<start_at or row['id']>end_at:continue
            action_start=now()
            if row['id'] in actions:await actions[row['id']]()
            await page.wait_for_timeout(180 if dry else (1250 if row['id'] in [3,16,17,24,25,28,32,36,42,47,59,63,64] else 950))
            start=now();await page.screenshot(path=str(frames/f'{row["id"]:02d}.png'))
            marks=await page.locator('.v7-mark').evaluate_all('(es)=>es.map(e=>({x:e.offsetLeft,y:e.offsetTop,w:e.offsetWidth,h:e.offsetHeight}))')
            items.append(dict(id=row['id'],action_start=action_start,start=start,end=start+row['duration'],scroll=await page.evaluate('scrollY'),marks=marks))
            for j,(t,fn,label) in enumerate(sorted(during(row),key=lambda x:x[0])):
                if not dry:
                    delay=start+t-now()
                    if delay>0:await page.wait_for_timeout(delay*1000)
                await fn();events.append(dict(id=row['id'],label=label,planned=start+t,actual=now()))
                await page.screenshot(path=str(frames/f'{row["id"]:02d}_{j+1}.png'))
            if not dry:
                remaining=start+row['duration']-now()
                if remaining>0:await page.wait_for_timeout(remaining*1000)
                gap=.9 if idx==len(rows)-1 or rows[idx+1]['section']!=row['section'] else .5
                if row['id'] in [6,8,10,12,13,15,30,35,37,38,39,40,44,55,57,58,61,62,64]:gap=1.15
                if row['id']==65:gap=2.4
                await page.wait_for_timeout(gap*1000)
            dest=BASE/'work'/('rehearsal_timeline.json' if dry else 'recorded_timeline.json')
            dest.write_text(json.dumps(dict(duration=now(),items=items),ensure_ascii=False,indent=2))
            print('SCENE',row['id'],'start',round(start,2),'speech',round(row['duration'],2),flush=True)
        if not dry:await page.wait_for_timeout(800)
        dest.write_text(json.dumps(dict(duration=now(),items=items),ensure_ascii=False,indent=2))
        (BASE/'work'/('rehearsal_cues.json' if dry else 'events.json')).write_text(json.dumps(events,ensure_ascii=False,indent=2))
        vid=page.video;await ctx.close()
        if vid:(BASE/'work/recording_path.txt').write_text(str(await vid.path()))
        await browser.close()
        (BASE/'work'/('rehearsal_errors.json' if dry else 'browser_errors.json')).write_text(json.dumps(errors,ensure_ascii=False,indent=2))
        if not dry:(BASE/'work/cuts.json').write_text(json.dumps(cuts,ensure_ascii=False,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--dry',action='store_true');ap.add_argument('--start',type=int,default=1);ap.add_argument('--end',type=int,default=65);args=ap.parse_args();asyncio.run(main(args.dry,args.start,args.end))
