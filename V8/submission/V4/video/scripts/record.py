"""Continuous UI recording on the narration clock. --dry rehearses all actions."""
from pathlib import Path
import argparse,asyncio,json,time
from playwright.async_api import async_playwright

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[3]
URL='http://127.0.0.1:8788'
CHROME='/data1/duhaocun/.cache/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell'
CSS='''
html,body,body *{overflow-anchor:none!important}
#vid-pointer{position:fixed;width:19px;height:19px;border:2px solid #2563eb;background:#bfdbfe80;border-radius:50%;pointer-events:none;z-index:9999998;left:18px;top:770px;transform:translate(-50%,-50%);box-shadow:0 0 0 4px #ffffffa8}
.vid-focus{position:fixed;border:3px solid #2563eb;border-radius:12px;box-shadow:0 0 0 6px #60a5fa24;pointer-events:none;z-index:9999995;transition:all .28s ease}
#vid-cue{position:fixed;left:14px;bottom:17px;width:205px;padding:12px;border:1px solid #a4bce1;border-radius:12px;background:#f2f7fff5;color:#304564;z-index:99990;font:13px/1.65 'Noto Sans CJK SC',sans-serif;box-shadow:0 5px 20px #182f5520;pointer-events:none}
#vid-cue small{display:block;font-size:10px;letter-spacing:.8px;color:#6782a8;margin-bottom:4px}
#vid-lens{position:fixed;left:290px;top:175px;width:640px;padding:12px;border:2px solid #93b4f1;border-radius:16px;background:#fffffff7;box-shadow:0 15px 60px #12356b44;z-index:9999996;pointer-events:none}
#vid-lens span{display:block;font:12px 'Noto Sans CJK SC';color:#64748b;margin-bottom:8px}#vid-lens img{width:100%;display:block;border-radius:9px}
body[data-record-page='grade1'] .left td .sub{display:none}body[data-record-page='grade1'] .left table{font-size:12px}
.tcards .tcard[data-k='u20261014225125'],.tcards .tcard[data-k='u20261014230351'],.tcards .tcard[data-k='u20261014233306']{display:none}
.tcard[data-up]{display:none}
'''

async def main(dry=False):
    tl=json.loads((BASE/'work/timeline.json').read_text());rows=tl['items'];frames=BASE/'work'/('rehearsal' if dry else 'action_frames');frames.mkdir(exist_ok=True)
    events=[];cuts=[];errors=[];extra=0;origin=0;upload_id=None
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=CHROME,args=['--no-sandbox'])
        opts=dict(viewport={'width':1600,'height':800},device_scale_factor=1)
        if not dry:opts.update(record_video_dir=str(BASE/'work/recording'),record_video_size={'width':1600,'height':800})
        ctx=await browser.new_context(**opts);page=await ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        await page.goto(URL+'/frontend/?task=pjm&t=0&page=overview',wait_until='networkidle')
        await page.locator('#main .kpis').wait_for();await page.add_style_tag(content=CSS)
        await page.evaluate('''()=>{for(const id of ['vid-pointer','vid-cue']){let e=document.createElement('div');e.id=id;document.body.append(e)}
          document.addEventListener('mousemove',e=>{let p=document.querySelector('#vid-pointer');p.style.left=e.clientX+'px';p.style.top=e.clientY+'px'})}''')
        source=(ROOT/'V8/submission/V4/figures/src/diagrams.html').read_text()

        async def cue(t,tag='PJM 2025 · 实测结果演示'):
            await page.locator('#vid-cue').evaluate('(e,x)=>{e.replaceChildren();let s=document.createElement("small");s.textContent=x[1];e.append(s,document.createTextNode(x[0]))}',[t,tag])
        async def clear():
            await page.evaluate("document.querySelectorAll('.vid-focus,#vid-lens').forEach(e=>e.remove())")
        async def at_time(t):
            if not dry:
                remain=t+extra-(time.monotonic()-origin)
                if remain>0:await page.wait_for_timeout(remain*1000)
        async def at_phrase(n,needle):
            if dry:return
            data=json.loads((BASE/f'audio/{n:02d}.json').read_text());best=[]
            for e in data['events']:
                ws=e.get('output',{}).get('sentence',{}).get('words',[])
                if len(ws)>len(best):best=ws
            text='';positions=[]
            for w in best:
                text+=w['text'];positions.extend([w['begin_time']/1000]*len(w['text']))
            k=text.find(needle)
            if k>=0:await at_time(rows[n-1]['start']+positions[k]/tl['post_speed']-.12)
        async def focus(loc,color='#2563eb'):
            await clear();box=await loc.first.bounding_box();assert box,'Missing focus target'
            await page.evaluate('''([b,c])=>{let e=document.createElement('div');e.className='vid-focus';Object.assign(e.style,{left:(b.x-5)+'px',top:(b.y-5)+'px',width:(b.width+10)+'px',height:(b.height+10)+'px',borderColor:c});document.body.append(e)}''',[box,color])
        async def lens(loc,label):
            import base64
            b=await loc.first.bounding_box();assert b
            data=await page.screenshot(clip={k:b[k] for k in ['x','y','width','height']})
            await page.evaluate('''([src,t])=>{document.querySelector('#vid-lens')?.remove();let e=document.createElement('div');e.id='vid-lens';let s=document.createElement('span');s.textContent=t;let i=document.createElement('img');i.src=src;e.append(s,i);document.body.append(e)}''',['data:image/png;base64,'+base64.b64encode(data).decode(),label])
        async def move(loc):
            b=await loc.first.bounding_box();assert b
            await page.mouse.move(b['x']+b['width']*.52,b['y']+b['height']*.5,steps=5)
        async def click(loc,preserve=True):
            await move(loc)
            if preserve:await loc.first.evaluate('e=>{const y=scrollY;e.click();window.scrollTo({top:y,behavior:"instant"})}')
            else:await loc.first.evaluate('e=>e.click()')
            await page.wait_for_timeout(80)
        async def scroll(loc,top=98):
            await clear()
            await loc.first.evaluate('(e,t)=>window.scrollTo({top:Math.max(0,scrollY+e.getBoundingClientRect().top-t),behavior:"smooth"})',top)
            await page.wait_for_timeout(750)
        async def row_in_table(loc):
            await loc.first.evaluate('''e=>{let p=e.parentElement;while(p&&!p.classList.contains('scroll'))p=p.parentElement;
              if(p)p.scrollTo({top:p.scrollTop+e.getBoundingClientRect().top-p.getBoundingClientRect().top-p.clientHeight/3,behavior:'smooth'})}''')
            await page.wait_for_timeout(400)
        def txt(s):return page.get_by_text(s,exact=True).first
        def card(s):return page.locator('.card').filter(has=page.locator('h3').filter(has_text=s)).first
        async def nav(p):
            await clear();await board_close();await click(page.locator(f'#nav [data-p="{p}"]'),preserve=False)
            await page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
            await page.evaluate('(p)=>document.body.dataset.recordPage=p',p)
            await page.wait_for_timeout(450)
        async def top():
            await clear();await page.evaluate('window.scrollTo({top:0,behavior:"smooth"})');await page.wait_for_timeout(650)
        async def close_modal():
            await clear()
            for s in ['#wx','#mx','#dx']:
                if await page.locator(s).count():
                    await page.locator(s).evaluate('e=>e.click()');await page.wait_for_timeout(80);break
        async def board_close():await page.evaluate("document.querySelector('#vid-board')?.remove()")
        async def board(kind):
            await clear()
            await page.evaluate('''([kind,source])=>{
              document.querySelector('#vid-board')?.remove();let host=document.createElement('div');host.id='vid-board';
              host.style.cssText='position:fixed;inset:0;background:linear-gradient(145deg,#f7faff,#eaf1ff);z-index:9999990;overflow:hidden';document.body.append(host);
              let sh=host.attachShadow({mode:'open'}),doc=new DOMParser().parseFromString(source,'text/html'),sty=document.createElement('style');
              sty.textContent=doc.querySelector('style').textContent+`:host{--ink:#0f1a2e;--ink2:#334155;--sub:#64748b;--blue:#2563eb;--blue2:#dbeafe;--red:#e5484d;--red2:#fee2e2;--amber:#d97706;--amber2:#fef3c7;--green:#0f9f6e;--green2:#d1fae5;--violet:#7c3aed;--violet2:#ede9fe;--line:#cbd5e1;font-family:'Noto Sans CJK SC',sans-serif;color:#0f1a2e} .fig{margin:0} .reveal{transition:opacity .7s,transform .7s} .eyebrow{position:absolute;top:25px;left:42px;color:#5876a5;font-size:13px;letter-spacing:2px}.active{outline:3px solid #3b82f6;box-shadow:0 0 0 8px #3b82f622}`;sh.append(sty);
              let e=document.createElement('div');e.className='eyebrow';e.textContent='面向聚合推断威胁的数据定级与共享审查系统';sh.append(e);
              if(kind==='opener'){
                let heading=document.createElement('div');heading.style.cssText='position:absolute;top:67px;left:0;width:100%;text-align:center;font-size:32px;font-weight:800';heading.textContent='单独不过线，组合却可能越线';sh.append(heading);
                let sub=document.createElement('div');sub.style.cssText='position:absolute;top:117px;width:100%;text-align:center;color:#64748b;font-size:17px';sub.textContent='PJM 2025 · 实际网损为保护对象 · 社会公众判定线 0.7';sh.append(sub);
                let panel=doc.querySelector('#f_aggr>.row>.box').cloneNode(true);panel.style.cssText='position:absolute;left:400px;top:171px;width:800px;padding:16px 20px;transform:scale(1.05);transform-origin:top center';panel.querySelector(':scope>b').remove();panel.querySelector(':scope>.s').remove();
                panel.querySelectorAll('div.box').forEach(n=>{let y=parseInt(n.style.top);if(y===4||y===150){n.classList.add('reveal');n.style.opacity=0;n.dataset.reveal=y===4?'triple':'pair'}});
                panel.querySelector('svg').style.opacity=0;sh.append(panel);
              } else if(kind==='chart_pjm'||kind==='chart_combos'||kind==='chart_utility'){
                let im=document.createElement('img');im.src='/submission/V4/figures/'+kind+'.png';im.style.cssText='position:absolute;left:45px;top:80px;width:1510px;height:665px;object-fit:contain';sh.append(im);
              } else {
                let f=doc.querySelector('#f_'+kind).cloneNode(true);f.style.cssText+=';position:absolute;left:0;top:0;transform-origin:top left';sh.append(f);
                requestAnimationFrame(()=>{let h=f.getBoundingClientRect().height,sc=Math.min(1520/1600,680/h);f.style.transform='translate('+((1600-1600*sc)/2)+'px,'+((800-h*sc)/2+15)+'px) scale('+sc+')'});
              }
            }''',[kind,source])
            await page.wait_for_timeout(250)
        async def reveal(which):
            await page.evaluate('''w=>{let s=document.querySelector('#vid-board').shadowRoot;s.querySelectorAll('[data-reveal="'+w+'"]').forEach((e,i)=>{e.style.transitionDelay=(i*.24)+'s';e.style.opacity=1});s.querySelector('svg').style.opacity=1}''',which)
        async def board_focus(index,selector='.stage'):
            await page.evaluate('''([i,sel])=>{let s=document.querySelector('#vid-board').shadowRoot;s.querySelectorAll('.active').forEach(e=>e.classList.remove('active'));let e=s.querySelectorAll(sel)[i];if(e)e.classList.add('active')}''',[index,selector])
        async def wait_catalog():
            nonlocal extra
            if await page.locator('.wtab').count():return
            start=time.monotonic()-origin
            await page.locator('.wtab').wait_for(timeout=180000)
            spent=time.monotonic()-origin-start
            if not dry and spent>.6:
                cuts.append(dict(start=start+.3,end=start+spent,reason='实际字段目录起草等待'))
                extra+=spent-.3
        async def upload():
            nonlocal upload_id
            await nav('tasks');await click(page.locator('#new'))
            await page.locator('#nt').fill('PJM 区域电力市场 2025（视频演示）')
            await page.locator('#nf').set_input_files(str(ROOT/'data/upload_examples/01_PJM区域电力市场_2025.xlsx'))
            await page.locator('#nn').fill('美国 PJM 电力市场 2025 年逐小时运行与市场数据')
            await focus(page.locator('#wz'));await move(page.locator('#wgo'))
            await cue('上传入口演示；随后回看既有 PJM 实测任务的字段目录。','表单演示 · 本次不提交数据')
        async def catalog():
            await page.evaluate('''async()=>{let u=await api('/api/upload?任务=u20261014225125');
              S.up={id:'u20261014225125',step:2,info:u.信息,prof:u.画像,err:''};useDraft(u);wizard()}''')
            await cue('这里读取既有上传测试任务的真实目录；示范确认字段角色。','既有任务实测目录回看')
            await focus(page.locator('.wsum'))
        async def roles():
            nonlocal upload_id
            await wait_catalog();upload_id=await page.evaluate('S.up.id')
            (BASE/'work/upload_id.txt').write_text(upload_id)
            for name in ['total_losses','total_gen','gross_actual_interchange_mw','net_actual_interchange_mw']:
                r=page.locator('.wtab tr').filter(has=page.locator('code').filter(has_text=name)).first
                await row_in_table(r)
                await r.locator('select[data-f="角色"]').select_option('保护对象');await page.wait_for_timeout(150)
            await focus(page.locator('.wtab tr').filter(has_text='total_losses'))
            await cue('四项保护对象由使用者确认；目录草稿只作为建议。','既有目录 · 角色确认演示')
        async def progress():
            await close_modal();await page.evaluate("openNew('u20261014225125')")
            await page.locator('.wprog').wait_for();await page.wait_for_timeout(350)
            await cue('上传测试任务的实测完成记录；全流程用时 559 秒，省略计算等待。','实测记录回看 · 非本次新计算')
            await focus(page.locator('.wprog'))
        async def grade():
            await close_modal();await nav('grade1');await click(page.locator('[data-f="保护对象"]'))
            await click(page.locator('tr.c').filter(has_text='实际网损'))
            await focus(page.locator('[data-m="rules"]'))
            await cue('模型判影响对象与程度；等级由国标判定表查出。')
        async def review():
            await top();await click(page.locator('[data-m="review"]'));await page.wait_for_timeout(500)
            r=page.locator('.rvtab tr').filter(has_text='实际网损');await row_in_table(r);await focus(r,'#e29525')
        async def single():
            await close_modal();await nav('single');await cue('只给模型一个候选字段，在未参与训练的数据上测推断精度。')
            await focus(page.locator('.objbar .ob.on'))
        async def single_top():
            await focus(page.locator('.kpis').first)
            for name in ['日前负荷预测','最新负荷预测','日前网损电价分量']:
                r=page.locator('tr.c').filter(has_text=name);await click(r);await page.wait_for_timeout(240 if dry else 450)
            await click(page.locator('tr.c').filter(has_text='日前负荷预测'))
            await focus(page.locator('.kpi').nth(1))
        async def aggr():
            await nav('aggr');await page.wait_for_timeout(500);await cue('集合上定义风险；用 M 把背景下的最大边际提升折算到字段。')
            await focus(page.locator('#gb'))
        async def aggr_detail():
            await scroll(page.locator('.split'))
            await click(page.locator('tr.c').filter(has_text='日前节点边际电价'))
            await focus(page.locator('#dec'))
        async def drag_k():
            await focus(page.locator('#dec'))
            box=await page.locator('#pill').bounding_box();assert box
            x=box['x']+box['width']/2;y=box['y']+box['height']/2
            await page.mouse.move(x,y,steps=15);await page.mouse.down();await page.mouse.move(x,y-112,steps=35);await page.mouse.up()
            assert await page.evaluate('S.rk')==0
            if dry:await page.wait_for_timeout(400)
            else:await at_phrase(26,'有了两个背景字段')
            await page.mouse.down();await page.mouse.move(x,y,steps=35);await page.mouse.up()
            assert await page.evaluate('S.rk')==2
            await focus(page.locator('#dec .box'));await lens(page.locator('#dec .dgrid3'),'当前真实页面 · 单独作用与背景增益')
        async def combo():
            await clear();await click(page.locator('tr.c').filter(has_text='实时网损电价分量'))
            c=page.locator('.cmb').filter(has_text='最新负荷预测').first;await scroll(c,230);await click(c);await focus(c,'#e5484d')
            await cue('三字段合起来为 0.736；去掉任何一个，均回到判定线以下。')
        async def combo_curves():
            await scroll(page.locator('#gc'),330)
            for e in await page.locator('.lgc').all():await move(e);await page.wait_for_timeout(180)
            await focus(page.locator('#gc'))
        async def regrade():
            await nav('regrade');await cue('直接定级 → 强化学习联合评估 → 整体核对；所有保护对象共同决定。')
            await focus(page.locator('.objbar [data-sc="all"]'))
        async def load_upgrade():
            await scroll(page.locator('.split'));await click(page.locator('tr.c').filter(has_text='最新负荷预测'))
            await focus(page.locator('.right .box').first,'#e5484d')
        async def formula():
            await top();await focus(page.locator('.rlbox'))
        async def formula_terms():
            for cls,phrase in [('t1','留在低等级'),('t2','调高等级'),('t3','仍成立')]:
                await at_phrase(37,phrase);await focus(page.locator('.fmlk .'+cls));await page.wait_for_timeout(160)
        async def training():
            await scroll(page.locator('#tc'),180);await focus(page.locator('#tc'))
        async def utility():
            await scroll(page.locator('.split'));await click(page.locator('tr.c').filter(has_text='日前节点边际电价'))
            await focus(page.locator('.right .box').first)
            await lens(page.locator('.right .box').first,'当前真实页面 · 调级前后的效用对比')
        async def exact():
            await top();await focus(page.locator('.kpis').first)
            await cue('15 → 0：最小越线组合全部拆开。强化学习与精确最优差距 0.0%。')
        async def whole():
            await nav('effect');await scroll(card('整体核对'));await focus(card('整体核对'))
            await cue('将接收方可拿到的全部字段合并，再训练并换模型复测。')
        async def effect_top():
            await top();await focus(page.locator('.rcards'))
        async def effect_public():
            await focus(page.locator('.rcard').first,'#0f9f6e');await lens(page.locator('.rcard .vs').first,'当前真实页面 · 社会公众对实际网损的推断精度')
        async def effect_models():
            await scroll(card('换模型复测'));await focus(card('换模型复测'))
        async def residual():
            await top();await click(page.locator('.ob[data-t="1"]'));await focus(page.locator('.rcards'),'#e29525')
            await cue('发电总出力仍存在剩余风险，系统保留越线结果，供后续审查。')
            await at_time(rows[44]['end']-2.7);await board('chart_pjm')
        async def parameters():
            await nav('aggr');await click(page.locator('#guide'));await click(page.locator('[data-gt="1"]'));await focus(page.locator('.dw'))
            await move(page.locator('[data-k="K"]'))
        async def tasks():
            await close_modal();await nav('tasks');await focus(page.locator('.tcards'));await cue('六类真实数据：电力、社区、医疗、企业用能与楼宇传感器。')
        async def pairs():
            await at_phrase(4,'两两组合');await reveal('pair')
        async def grade_table():
            await scroll(page.locator('.right .mx'),200);await focus(page.locator('.right .mx'))
            await lens(page.locator('.right .mx'),'当前真实页面 · 国标判定表及命中位置')

        # One semantic action per utterance; continuous holds fill the remainder.
        actions={
          1:lambda:board('opener'),2:lambda:cue('接收方拿到的是字段集合。'),3:lambda:cue('实际网损：2 级保护对象；社会公众只能拿到 1 级字段。'),
          4:pairs,5:lambda:reveal('triple'),6:lambda:cue('单项均不过线，三项合起来 0.736，超过 0.7。'),7:lambda:cue('在定级时发现聚合推断，并把它计入等级。'),
          8:upload,9:catalog,10:lambda:cue('大模型根据列名与示例值起草字段目录。','既有任务实测目录回看'),11:roles,
          12:lambda:focus(page.locator('.wsum')),13:progress,14:lambda:focus(page.locator('.wsum')),
          15:grade,16:lambda:focus(page.locator('.right .box').first),17:grade_table,18:review,19:lambda:focus(page.locator('#rvl')),
          20:single,21:lambda:focus(page.locator('.right')),22:single_top,
          23:aggr,24:aggr_detail,25:lambda:focus(page.locator('#dec')),26:drag_k,27:lambda:focus(page.locator('#dec .dgrid3')),28:combo,29:combo_curves,
          30:lambda:board('theory'),31:lambda:board_focus(0,'.row:nth-of-type(4) .box'),
          32:regrade,33:lambda:cue('字段 M ≥ 0.7，直接定为对应保护对象的等级。'),34:load_upgrade,35:lambda:cue('同一个字段影响多个保护对象，需要求一整套等级方案。'),
          36:formula,37:formula_terms,38:training,39:utility,40:exact,41:whole,
          42:effect_top,43:effect_public,44:effect_models,45:residual,
          46:parameters,47:tasks,48:lambda:board('chart_combos'),49:lambda:board('chart_utility'),
          50:lambda:board('route'),51:lambda:board_focus(1),52:lambda:board_focus(2),53:lambda:board_focus(3),54:lambda:board_focus(4),55:lambda:nav('overview')}
        await board('opener')
        if not dry:
            await page.evaluate('''()=>{let e=document.createElement('div');e.id='vid-sync';e.style.cssText='position:fixed;inset:0;background:#ff00ff;z-index:2147483647';document.body.append(e)}''')
            await page.wait_for_timeout(650);await page.locator('#vid-sync').evaluate('e=>e.remove()')
        origin=time.monotonic()
        for r in rows:
            at=r['start']-.18
            if not dry:
                remain=at+extra-(time.monotonic()-origin)
                if remain>0:await page.wait_for_timeout(remain*1000)
            await actions[r['id']]()
            await page.wait_for_timeout(160 if dry else 50)
            actual=time.monotonic()-origin-extra
            await page.screenshot(path=str(frames/f'{r["id"]:02d}.png'))
            events.append(dict(id=r['id'],planned=at,actual=actual,section=r['section'],text=r['text'],scroll=await page.evaluate('scrollY')))
            (BASE/'work'/('rehearsal_events.json' if dry else 'events.json')).write_text(json.dumps(events,ensure_ascii=False,indent=2))
            print('ACTION',r['id'],round(actual,2),r['section'],flush=True)
        if not dry:
            remain=tl['duration']+extra-(time.monotonic()-origin)
            if remain>0:await page.wait_for_timeout(remain*1000)
            await page.wait_for_timeout(700)
        vid=page.video;await ctx.close()
        if vid:(BASE/'work/recording_path.txt').write_text(str(await vid.path()))
        await browser.close()
        (BASE/'work'/('rehearsal_errors.json' if dry else 'browser_errors.json')).write_text(json.dumps(errors,ensure_ascii=False,indent=2))
        (BASE/'work/cuts.json').write_text(json.dumps(cuts,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dry',action='store_true');args=p.parse_args();asyncio.run(main(args.dry))
