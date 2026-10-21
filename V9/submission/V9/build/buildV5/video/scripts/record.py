"""Continuous UI recording on the narration clock. --dry rehearses all actions."""
from pathlib import Path
import argparse,asyncio,json,time
from playwright.async_api import async_playwright

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[5]
URL='http://127.0.0.1:8795'
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
        await page.goto(URL+'/frontend/?task=nem&t=2&page=overview',wait_until='networkidle')
        await page.locator('#main .kpis').wait_for();await page.add_style_tag(content=CSS)
        await page.evaluate('''()=>{for(const id of ['vid-pointer','vid-cue']){let e=document.createElement('div');e.id=id;document.body.append(e)}
          document.addEventListener('mousemove',e=>{let p=document.querySelector('#vid-pointer');p.style.left=e.clientX+'px';p.style.top=e.clientY+'px'})}''')

        async def cue(t,tag='NEM 2024 · 内置实测结果'):
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
            import base64
            await clear();await board_close()
            if kind=='intro':
                html="""<div class='eyebrow'>面向聚合推断威胁的数据定级与共享审查系统</div>
                  <h1>单个字段的等级，<br>还不足以说明组合后的风险。</h1>
                  <div class='introcols'><div><small>逐个评估</small><strong>字段自身的敏感程度</strong><p>泄露后影响谁 · 影响多大</p></div><div><small>一起开放</small><strong>字段之间的推断能力</strong><p>能否还原无权获取的数据</p></div></div>
                  <div id='metric'>神经网络推断模型的准确率　｜　阈值 <b>0.7</b></div>"""
            else:
                f=BASE.parent/'img'/('chart_combos.jpg' if kind=='summary' else 'fig_aggr.jpg')
                uri='data:image/jpeg;base64,'+base64.b64encode(f.read_bytes()).decode()
                html=f"<img id='board-img' src='{uri}'><div id='board-caption'></div>"
            await page.evaluate(r"""html=>{let e=document.createElement('div');e.id='vid-board';e.style.cssText='position:fixed;inset:0;z-index:9999990;background:#f4f8ff;color:#10243f;font-family:Noto Sans CJK SC,sans-serif';e.innerHTML=`<style>
              #vid-board .eyebrow{margin:48px 90px;color:#50698d;font-size:18px;letter-spacing:2px}#vid-board h1{font-size:48px;line-height:1.45;margin:40px 90px;font-weight:750}
              #vid-board .introcols{display:flex;gap:30px;margin:10px 90px}#vid-board .introcols>div{padding:24px 32px;background:white;border:1px solid #d8e4f3;border-radius:18px;flex:1}
              #vid-board small{display:block;color:#5a78a0;font-size:16px;margin-bottom:12px}#vid-board strong{font-size:28px}#vid-board p{color:#718198;font-size:20px;margin-bottom:0}
              #metric{margin:42px 90px;font-size:25px;color:#2563eb;padding:18px 25px;border-left:4px solid #2563eb;background:#e5efff}
              #board-img{width:1540px;height:750px;object-fit:contain;position:absolute;left:30px;top:10px}#board-caption{position:absolute;bottom:25px;left:90px;font-size:24px;font-weight:600;color:#244b8c;background:#f4f8fff5;padding:8px 20px}
            </style>`+html;document.body.append(e)}""",html)
            await page.wait_for_timeout(250)
        async def region(x,y,w,h,color='#2563eb'):
            await clear()
            await page.evaluate('''([x,y,w,h,c])=>{let e=document.createElement('div');e.className='vid-focus';Object.assign(e.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px',borderColor:c});document.body.append(e)}''',[x,y,w,h,color])
        async def opener_single():
            await board('aggr');await region(115,492,648,101)
        async def opener_combo():
            await region(115,361,648,101)
            await at_phrase(5,'三项放在一起');await region(348,222,211,101,'#e5484d')
        async def opener_two_views():
            await region(869,145,668,540)
        async def upload():
            await nav('tasks');await click(page.locator('#new'))
            await page.locator('#nt').fill('PJM 区域电力市场 2025（buildV5 演示）')
            await page.locator('#nf').set_input_files(str(ROOT/'data/upload_examples/01_PJM区域电力市场_2025.xlsx'))
            await page.locator('#nn').fill('美国 PJM 电力市场 2025 年逐小时运行与市场数据。确认机组总发电量、实际网损、总交换功率及净交换功率为保护对象，其余数值列为候选字段。')
            await focus(page.locator('#wz'));await move(page.locator('#wgo'))
            await cue('上传数据表，起草字段目录。','新建任务 · 实际操作')
            if not dry:await click(page.locator('#wgo'))
        async def catalog_roles():
            nonlocal extra,upload_id
            await clear()
            if dry:
                await page.evaluate("""async()=>{let u=await api('/api/upload?任务=u20261014225125');S.up={id:'u20261014225125',step:2,info:u.信息,prof:u.画像,err:''};useDraft(u);wizard()}""")
            elif not await page.locator('.wtab').count():
                start=time.monotonic()-origin
                await page.locator('.wtab').wait_for(timeout=240000)
                spent=time.monotonic()-origin-start
                if spent>.6:
                    cuts.append(dict(start=start+.25,end=start+spent,reason='省略实际大模型起草的等待时间'))
                    extra+=spent-.25
            upload_id=await page.evaluate('S.up.id')
            if not dry:(BASE/'work/upload_id.txt').write_text(upload_id)
            for name in ['total_losses','total_gen','gross_actual_interchange_mw','net_actual_interchange_mw']:
                r=page.locator('.wtab tr').filter(has=page.locator('code').filter(has_text=name)).first
                await row_in_table(r)
                await r.locator('select[data-f="公开情况"]').select_option('未公开')
                await r.locator('select[data-f="角色"]').select_option('保护对象')
            await focus(page.locator('#wcnt'))
            await cue('确认保护对象与公开情况；点击开始后，后台自动运行。','新建任务 · 实际操作')
            await at_phrase(8,'之后后台')
            if not dry:
                await clear();await click(page.locator('#wrun'))
                await page.locator('.wprog').wait_for(timeout=15000)
                await focus(page.locator('.wprog'))
        async def grade():
            await close_modal()
            await page.evaluate("()=>{setTask('nem');S.t=2;S.scope='all'}")
            await nav('grade1')
            r=page.locator('tr.c').filter(has_text='南澳风电出力预测');await row_in_table(r);await click(r)
            await focus(page.locator('.right .mx'))
            await cue('依据国标判定影响对象和影响程度，再确定一次等级。')
        async def review():
            await focus(page.locator('.right .box').first)
            await at_phrase(10,'结果可以')
            await click(page.locator('[data-m="review"]'));await page.wait_for_timeout(250)
            r=page.locator('.rvtab tr').filter(has_text='南澳风电出力预测');await row_in_table(r);await focus(r)
        async def levels():
            await close_modal();await nav('overview');await focus(page.locator('.kpis').first)
            await cue('30 个候选字段：1 级；3 台机组出力：2 级。')
        async def single():
            await nav('single');await click(page.locator('tr.c').filter(has_text='南澳出清价'))
            await focus(page.locator('.kpis').first)
            await lens(page.locator('.kpi').nth(1),'当前真实页面 · 最高的单字段推断精度')
            await cue('对 PPCCGT 机组：没有字段能单独越过 0.7。')
        async def select_k(k):
            await clear()
            loc=page.locator(f'[data-rk="{k}"]')
            await move(loc);b=await loc.bounding_box()
            await page.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2)
            await page.wait_for_timeout(220)
            assert await page.evaluate('S.rk')==k
        async def aggr_zero():
            await nav('aggr');await scroll(page.locator('.split'))
            r=page.locator('tr.c').filter(has_text='南澳风电出力预测');await row_in_table(r);await click(r)
            await select_k(0);await focus(page.locator('#dec'))
            await cue('K = 0：只给模型风电预测这一个字段，推断精度 0.183。')
        async def aggr_full():
            await select_k(3);await focus(page.locator('#dec'))
            await cue('M：最有利背景下，新增这个字段带来的最大提升。')
        async def bg_names():await focus(page.locator('#dec .bgline'))
        async def bg_increase():
            await focus(page.locator('#dec'))
            await lens(page.locator('#dec'),'当前真实页面 · 背景 0.223 → 加上风电预测 0.811')
        async def m_value():
            await focus(page.locator('#dec .dgrid3'))
            await lens(page.locator('#dec .dgrid3'),'当前真实页面 · 单独作用 + 背景增益 = M')
            await cue('0.811 − 0.223 = 0.588；单独推断仅 0.183。')
        async def m_compare():
            await clear();await select_k(0);await focus(page.locator('#dec'))
            await at_phrase(18,'所以');await select_k(3);await focus(page.locator('#dec'))
            await cue('空背景也参加比较，因此 M 不低于单独推断能力。')
        async def m_witness():
            await scroll(page.locator('[data-wk="3"]'),370);await focus(page.locator('[data-wk="3"]'))
            await cue('从攻击者视角：寻找让风电预测发挥最大作用的背景知识。')
        async def change_k():
            await scroll(page.locator('#kt'),170);await click(page.locator('#kt'))
            await focus(page.locator('#kch'));await at_phrase(20,'切换')
            await scroll(page.locator('[data-wk="1"]'),190)
            for k in [1,2,3]:
                await click(page.locator(f'[data-wk="{k}"]'));await focus(page.locator('#gc'))
                await page.wait_for_timeout(180 if dry else 650)
        async def combos():
            await nav('combos');await page.wait_for_timeout(700)
            await scroll(page.locator('.split'));await focus(page.locator('.left table').first)
            await cue('具体共享风险：接收方能否凑齐这一组字段。')
        async def combo_count():
            n=await page.evaluate('verifiedCombos().length');assert n==13,n
            await click(page.locator('tr.c').first)
            await focus(page.locator('tr.c').first)
            await cue('PPCCGT｜已重训确认、用于定级：13 个；每个组合都包含风电预测。','重训结果 · 不含页面上的估计候选')
        async def combo_lattice():
            await focus(page.locator('.right .lat'))
            await lens(page.locator('.right .lat'),'当前真实页面 · 单独与两两不过线，三项凑齐越线')
        async def combo_est():
            await clear();await scroll(page.locator('#seg'),180);await focus(page.locator('.cstat'))
            await cue('更大的组合先估计，再对候选组合重新训练核对。')
        async def regrade():
            await nav('regrade');await click(page.locator('[data-sc="all"]'))
            await focus(page.locator('.inbar'))
            await cue('字段 M + 实际越线组合 + 数据使用需求 → 一整套等级方案。')
        async def direct():
            await focus(page.locator('.inbar').first)
            await cue('M ≥ 0.7：直接定为对应保护对象的等级。其余字段由效用函数统一权衡。')
        async def formula():
            await focus(page.locator('.rlbox'));await cue('效用函数：字段风险、使用成本、未拆开的越线组合。')
        async def terms():
            for cls,phrase in [('t1','留在'),('t2','级别越高'),('t3','没有拆开')]:
                await at_phrase(28,phrase);await focus(page.locator('.fml3 .'+cls))
        async def utility_goal():
            await focus(page.locator('.rlbox'));await cue('综合得分越高越好：降低推断风险，同时保留数据共享价值。')
        async def training():
            await scroll(page.locator('#tc'),240);await focus(page.locator('#tc'))
            await cue('采样完整方案 → 效用打分 → 组内比较 → 更新策略。')
        async def exact():
            await scroll(page.locator('.kpis'),180);await focus(page.locator('.kpi').last)
            await lens(page.locator('.kpi').last,'当前真实页面 · 联合评估与精确最优的差距')
        async def field_utility():
            await scroll(page.locator('.split'));r=page.locator('tr.c').filter(has_text='南澳风电出力预测');await row_in_table(r);await click(r)
            await focus(page.locator('.right .box').first)
            await lens(page.locator('.right .box').first,'当前真实页面 · 仅改变风电预测的等级')
            await cue('其余字段等级固定：1 级 −30.17 → 2 级 −23.64；拆开 6 个组合。')
        async def final_counts():
            await top();await focus(page.locator('.kpis'))
            await cue('最终调高 17 个字段；三台机组合计 14 个已确认组合全部拆开。')
        async def effects():
            await nav('effect');await scroll(card('换模型复测'),200);await focus(card('换模型复测'))
            await cue('汇总全部可获取字段，重新训练；两类模型取较高结果。')
        async def effect_two():
            await top();await click(page.locator('.objbar [data-t="0"]'))
            await focus(page.locator('.rcard').first);await lens(page.locator('.rcard .vs').first,'燃煤机组 BW01 · 调级前后')
            await at_phrase(35,'水电机组');await clear();await click(page.locator('.objbar [data-t="1"]'))
            await focus(page.locator('.rcard').first);await lens(page.locator('.rcard .vs').first,'水电机组 TUMUT3 · 调级前后')
        async def residual():
            await clear();await click(page.locator('.objbar [data-t="2"]'));await focus(page.locator('.rcard').first)
            await cue('PPCCGT 仍略高于 0.7：如实保留残余风险，严格模式可继续收紧。')
        async def ending():
            await nav('overview');await cue('面向聚合推断威胁的数据定级与共享审查系统','谢谢观看')
        actions={1:lambda:board('intro'),2:lambda:focus(page.locator('.introcols>div').last),3:lambda:focus(page.locator('#metric')),
          4:opener_single,5:opener_combo,6:opener_two_views,7:upload,8:catalog_roles,9:grade,10:review,11:levels,12:single,
          13:aggr_zero,14:aggr_full,15:bg_names,16:bg_increase,17:m_value,18:m_compare,19:m_witness,20:change_k,
          21:combos,22:combo_count,23:combo_lattice,24:combo_est,25:regrade,26:direct,27:formula,28:terms,29:utility_goal,
          30:training,31:exact,32:field_utility,33:final_counts,34:effects,35:effect_two,36:residual,37:lambda:board('summary'),38:ending}
        await board('intro')
        if not dry:
            await page.evaluate("""()=>{let e=document.createElement('div');e.id='vid-sync';e.style.cssText='position:fixed;inset:0;background:#ff00ff;z-index:2147483647';document.body.append(e)}""")
            await page.wait_for_timeout(650);await page.locator('#vid-sync').evaluate('e=>e.remove()')
        origin=time.monotonic()
        for r in rows:
            at=r['start']-.18;await at_time(at)
            await actions[r['id']]();await page.wait_for_timeout(160 if dry else 50)
            actual=time.monotonic()-origin-extra
            await page.screenshot(path=str(frames/f'{r["id"]:02d}.png'))
            events.append(dict(id=r['id'],planned=at,actual=actual,section=r['section'],text=r['text'],scroll=await page.evaluate('scrollY')))
            (BASE/'work'/('rehearsal_events.json' if dry else 'events.json')).write_text(json.dumps(events,ensure_ascii=False,indent=2))
            print('ACTION',r['id'],round(actual,2),r['section'],flush=True)
        if not dry:await at_time(tl['duration']);await page.wait_for_timeout(700)
        vid=page.video;await ctx.close()
        if vid:(BASE/'work/recording_path.txt').write_text(str(await vid.path()))
        await browser.close()
        (BASE/'work'/('rehearsal_errors.json' if dry else 'browser_errors.json')).write_text(json.dumps(errors,ensure_ascii=False,indent=2))
        if not dry:(BASE/'work/cuts.json').write_text(json.dumps(cuts,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dry',action='store_true');args=p.parse_args();asyncio.run(main(args.dry))
