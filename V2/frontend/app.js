/* Offline frontend. All metrics and plotted values come from V2/samples. */
'use strict';
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const h = escapeHTML;
const fmt = (n, digits = 3) => Number.isFinite(Number(n)) && n != null ? Number(n).toFixed(digits) : '—';
const count = n => Number(n).toLocaleString('zh-CN');
const paths = {
 shield:'M12 3 3.5 6.5v6c0 5 8.5 9 8.5 9s8.5-4 8.5-9v-6L12 3Z M8.5 12l2.5 2.5 4.5-5',
 overview:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
 layers:'m12 3 10 5-10 5L2 8l10-5Zm-9 10 9 4 9-4M3 18l9 4 9-4',
 risk:'M3 19h18M5 15l4-5 5 3 6-9M15 4h5v5',
 nodes:'M8 5h8M6 7v10m12-10v10M8 19h8 M4 3h4v4H4z M16 3h4v4h-4z M4 17h4v4H4z M16 17h4v4h-4z M8 7l8 10',
 tune:'M4 7h16M4 17h16M8 4v6M16 14v6',
 check:'M8 12l3 3 6-7 M20 12v8H4V4h11',
 folder:'M3 6h7l2 2h9v12H3z M3 6V4h7l2 2',
 book:'M12 5C8 2 4 3 2 4v16c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-2-10 1Zm0 0v16',
 arrow:'M4 12h16m-6-6 6 6-6 6', download:'M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5',
 info:'M12 11v6M12 7h.01 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
 lock:'M6 10V7a6 6 0 0 1 12 0v3M4 10h16v11H4z M12 14v3',
 bolt:'m13 2-9 12h7l-1 8 10-13h-8z',people:'M16 21v-3a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v3M20 8a4 4 0 0 1 0 8m2 5v-3M13 6a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
 plus:'M12 4v16M4 12h16', chevron:'m8 4 8 8-8 8', alert:'M12 3 2 21h20L12 3ZM12 9v5m0 3v.1', play:'m8 4 12 8-12 8Z', database:'M20 5c0 2-4 3-8 3S4 7 4 5s4-3 8-3 8 1 8 3Zm0 0v14c0 2-4 3-8 3s-8-1-8-3V5m0 7c0 2 4 3 8 3s8-1 8-3'
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.layers}"/></svg>`;
const tip = text => `<span class="info-tip" tabindex="0" role="img" aria-label="${h(text)}" title="${h(text)}">?</span>`;
const lv = n => `<span class="level l${Number(n)}">${Number(n) <= 4 ? `${Number(n)} 级` : Number(n) === 5 ? '重要数据' : '核心数据'}</span>`;
const tag = (text, cls = '') => `<span class="tag ${cls}">${h(text)}</span>`;
const TASKS = ['ieee30','insurance','community','pjm'];
const META = {
 ieee30:{short:'IEEE 30 节点',name:'电力市场标准算例',icon:'bolt',hint:'节点电价与机组出力，组合推断机组报价',target:2},
 insurance:{short:'医疗保险',name:'医疗保险个人数据',icon:'people',hint:'从个人属性识别医疗费用的推断风险',target:0},
 community:{short:'社区人口统计',name:'社区人口经济统计',icon:'database',hint:'检验多维公共统计数据的组合泄露风险',target:0},
 pjm:{short:'PJM 电力市场',name:'区域电力市场实测数据',icon:'risk',hint:'识别公开信息已知条件下的保护边界',target:0}
};
const PAGES = {
 overview:['任务概览','从数据共享的盲区出发，查看本任务的风险、定级方案与核对结果。','OVERVIEW','overview'],
 grade1:['数据资产与初始定级','按规则库逐字段初判并复核，明确哪些数据可以共享、哪些信息需要保护。','01 / INITIAL CLASSIFICATION','layers'],
 risk:['聚合推断风险','模拟接收方使用已获准的字段，检验是否能推断出权限之外的受保护数据。','02 / INFERENCE RISK','risk'],
 sens:['字段推断敏感度','将组合推断能力分解到字段：在已有信息的基础上，哪个字段带来更大的推断增益。','03 / FIELD SENSITIVITY','nodes'],
 regrade:['二次定级方案','先直接定级，再通过强化学习权衡推断风险与共享成本，形成调整方案。','04 / RECLASSIFICATION','tune'],
 effect:['效果复核与台账','用最终可获取的全部字段重新推断，并以两种模型核对剩余风险。','05 / VERIFICATION','check'],
 tasks:['任务管理','四个内置算例覆盖行业数据、公共数据与个人信息，可切换查看完整结果。','WORKSPACE / TASKS','folder'],
 rules:['规则与共享范围','查看本任务采用的等级映射、接收方权限和规则库摘录。','REFERENCE / RULES','book'],
 params:['推断判定参数','查看当前结果的判定线和敏感度设置；有计算缓存时可调整并重跑。','SETTINGS / THRESHOLDS','tune'],
 policy:['强化学习策略','查看风险与共享成本的权衡方式，以及联合定级的训练设置。','SETTINGS / POLICY','nodes']
};
const STEPS = ['grade1','risk','sens','regrade','effect'];
const STEP_NAMES = ['初始定级','发现风险','定位字段','调整等级','复核效果'];
const S = {task:'ieee30',page:'overview',t:2,r:'关联方',step:0,K:2,sel:null,filter:'全部',kw:'',comboLimit:8,srv:null,params:null,jobTask:null,timer:null};
let D, ALL = {}, charts = [], activeChart = null, lastFocus = null;
const C = {teal:'#168b78',blue:'#7295be',red:'#d17e6d',grid:'#eef1f4',muted:'#8c99a8',ink:'#33475c'};
const candidate = (d=D) => d.字段.filter(f => f.角色 === '候选');
const protectedFields = (d=D) => d.字段.filter(f => f.角色 === '敏感');
const adjusted = (d=D) => candidate(d).filter(f => f.二次等级 > f.一次等级);
const target = () => D.敏感[S.t];
const baseRisk = (row,d=D) => (d.仅凭公开基底可推出 || []).some(x => x.接收方 === row.接收方 && x.敏感数据 === row.敏感数据);
const riskCount = (key,d=D) => d.接收方能力.filter(x => x[key] > x.判定线).length;
const upKind = f => f.二次等级 <= f.一次等级 ? '等级不变' : f.整体核对上调 ? '整体核对' : f.依据?.直接定级 ? '直接定级' : '强化学习调整';
const url = (page,task=S.task) => `?${new URLSearchParams({task,page})}`;
const navLink = (page,label,cls='button') => `<a class="${cls}" href="${url(page)}" data-page="${page}">${label}</a>`;
const panelHead = (title,desc='',right='') => `<div class="panel-head"><div><h2>${title}</h2>${desc ? `<p>${desc}</p>` : ''}</div>${right}</div>`;
const stat = (label,value,note,ic='layers') => `<div class="stat"><div class="stat-top"><span>${label}</span>${icon(ic)}</div><div class="stat-value">${value}</div><div class="stat-note">${note}</div></div>`;
const notice = (title,body='',warning=false) => `<div class="notice ${warning?'warning':''}">${icon(warning?'alert':'info')}<div><strong>${title}</strong>${body?`<p>${body}</p>`:''}</div></div>`;
const next = (title,desc,page,label) => `<div class="next-step"><div><strong>${title}</strong><p>${desc}</p></div>${navLink(page,`${label} ${icon('arrow')}`,'button primary')}</div>`;
const tabs = () => `<div class="tabs" role="group" aria-label="受保护数据">${D.敏感.map((n,i)=>`<button class="tab ${i===S.t?'active':''}" data-target="${i}" aria-pressed="${i===S.t}">${icon('lock')} ${h(n)}</button>`).join('')}</div>`;
const receiverSelect = () => `<label>接收方 <select class="select" id="receiver">${D.接收方.filter(r=>r.级<4).map(r=>`<option ${r.名称===S.r?'selected':''}>${h(r.名称)}</option>`).join('')}</select></label>`;
const optionsBase = {animation:!window.matchMedia('(prefers-reduced-motion: reduce)').matches,animationDuration:450,animationDurationUpdate:250,textStyle:{fontFamily:'"Noto Sans CJK SC", "Microsoft YaHei", sans-serif',fontSize:10,color:C.muted},tooltip:{trigger:'axis',confine:true},grid:{left:45,right:22,top:33,bottom:30}};
function chart(id,options){const el=$(id);if(!el)return null;const c=echarts.init(el);c.setOption({...optionsBase,...options});charts.push(c);return c;}
window.addEventListener('resize',()=>charts.forEach(c=>c.resize()));
function toast(text){$('#toast').textContent=text;$('#toast').classList.add('visible');clearTimeout(S.toastTimer);S.toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),3500);}
function writeURL(push=false){const p=new URLSearchParams({task:S.task,page:S.page});if(['risk','sens'].includes(S.page)){p.set('t',S.t);p.set('r',S.r);}history[push?'pushState':'replaceState'](null,'',`?${p}`);}
function readURL(){const p=new URLSearchParams(location.search);S.task=ALL[p.get('task')]?p.get('task'):Object.keys(ALL)[0];S.page=PAGES[p.get('page')]?p.get('page'):'overview';const t=Number(p.get('t'));S.t=p.has('t')&&Number.isInteger(t)&&t>=0?t:META[S.task]?.target||0;S.r=p.get('r')||'关联方';}
function setTask(id){if(!ALL[id])return;S.task=id;D=ALL[id];S.t=Math.min(META[id]?.target||0,D.敏感.length-1);S.sel=null;S.step=0;S.kw='';S.filter='全部';S.K=Math.min(D.参数.K,D.背景增益.length-1);S.params={...D.参数};S.r='关联方';S.comboLimit=8;render();writeURL(true);}
function go(page){S.page=page;S.sel=null;S.kw='';S.filter='全部';S.comboLimit=8;render();writeURL(true);window.scrollTo(0,0);$('#sidebar').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');}
function render(){
 clearInterval(S.timer);charts.forEach(c=>c.dispose());charts=[];activeChart=null;
 D=ALL[S.task];S.t=Math.min(S.t,D.敏感.length-1);if(!D.接收方.some(r=>r.名称===S.r))S.r=D.接收方[0].名称;
 const p=PAGES[S.page];document.title=`${p[0]} · ${META[S.task]?.short||D.名称} | 数据定级与共享审查`;
 $('#title').textContent=p[0];$('#subtitle').textContent=p[1];$('#eyebrow').textContent=p[2];$('#breadcrumb').textContent=META[S.task]?.short||D.名称;
 $('#mode').textContent=canRun()?'计算模式':'内置结果 · 可交互';
 $('#task-context').innerHTML=`<button class="task-switch" data-page="tasks"><span class="overline">当前审查任务 ${icon('folder')}</span><strong>${h(META[S.task]?.short||D.名称)}</strong><small>${h(D.类别)} · ${count(D.样本数)} 条样本</small></button>`;
 $('#nav').innerHTML=`<div class="nav-label">分析工作流</div>${['overview',...STEPS].map((k,i)=>`<a href="${url(k)}" data-page="${k}" class="${S.page===k?'active':''}" ${S.page===k?'aria-current="page"':''}>${icon(PAGES[k][3])}<span>${k==='grade1'?'数据资产与初始定级':k==='sens'?'字段敏感度':k==='effect'?'效果复核与台账':PAGES[k][0]}</span><span class="nav-count">${i?'0'+i:''}</span></a>`).join('')}<div class="nav-label">工作空间</div><a href="${url('tasks')}" data-page="tasks" class="${S.page==='tasks'?'active':''}">${icon('folder')}任务管理</a><details ${['rules','params','policy'].includes(S.page)||S.settingsOpen?'open':''} id="settings-nav"><summary><span>规则与算法设置</span><span>⌄</span></summary>${['rules','params','policy'].map(k=>`<a href="${url(k)}" data-page="${k}" class="${S.page===k?'active':''}">${icon(PAGES[k][3])}${PAGES[k][0]}</a>`).join('')}</details>`;
 $('#settings-nav').ontoggle=e=>S.settingsOpen=e.target.open;
 $('#workflow').innerHTML=STEPS.includes(S.page)?`<nav class="workflow" aria-label="定级步骤">${STEPS.map((k,i)=>`<a href="${url(k)}" data-page="${k}" class="${S.page===k?'current':''}"><b>${i+1}</b>${STEP_NAMES[i]}</a>`).join('')}</nav>`:'';
 $('#page-actions').innerHTML=S.page==='tasks'?'<button class="button primary" id="import-button">'+icon('plus')+' 导入任务结果</button>':S.page==='overview'?navLink('risk',`${icon('play')} 查看推断过程`,'button primary'):`<button class="button" data-export="csv">${icon('download')} 导出台账</button>`;
 ({overview:pageOverview,tasks:pageTasks,grade1:pageGrade,risk:pageRisk,sens:pageSensitivity,regrade:pageRegrade,effect:pageEffect,rules:pageRules,params:pageParams,policy:pagePolicy})[S.page]();
 $('#main').dataset.ready=S.page;bindCommon();
}
function bindCommon(){
 $$('[data-page]').forEach(e=>e.onclick=event=>{if(event.ctrlKey||event.metaKey)return;event.preventDefault();go(e.dataset.page);});
 $$('[data-task]').forEach(e=>e.onclick=()=>setTask(e.dataset.task));
 $$('[data-target]').forEach(e=>e.onclick=()=>{S.t=Number(e.dataset.target);S.sel=null;S.step=0;S.comboLimit=8;render();writeURL();});
 $$('[data-export]').forEach(e=>e.onclick=()=>exportData(e.dataset.export));
 if($('#receiver'))$('#receiver').onchange=e=>{S.r=e.target.value;S.step=0;S.comboLimit=8;render();writeURL();};
 if($('#import-button'))$('#import-button').onclick=importDialog;
}
function example(d=D){const t=Math.min(META[d.id]?.target||0,d.敏感.length-1);const ladder=d.阶梯[t];const step=ladder?.步骤.at(-1);const names=step?.组合||[];const fieldLevel=Math.max(1,...names.map(n=>d.字段.find(f=>f.中文名===n)?.一次等级||1));const rec=d.接收方.find(r=>r.级>=fieldLevel&&r.级<(protectedFields(d).find(f=>f.中文名===d.敏感[t])?.一次等级||4));const cap=d.接收方能力.find(c=>c.接收方===rec?.名称&&c.敏感数据===d.敏感[t]);return{t,step,names,rec,cap,name:d.敏感[t]};}
function pageOverview(){
 const ex=example(), before=D.一次定级下的越线.length,after=D.二次定级后的越线.length,risks=riskCount('定级后');
 const representative=D.接收方能力.filter(x=>x.接收方===S.r);
 $('#main').innerHTML=`<section class="hero"><div class="hero-top"><div><div class="hero-label">聚合推断风险 · ${h(META[S.task]?.short||D.名称)}</div><h2>单项数据获准共享，<em>组合后仍可能泄露敏感信息。</em></h2><p>在本任务中，检验共享字段对「${h(ex.name)}」的推断能力，并把发现的风险计入等级。</p></div>${tag(D.类别,'good')}</div>
 <div class="evidence-flow"><div class="flow-card"><div class="flow-caption">${icon('layers')}${ex.rec?h(ex.rec.名称)+'原可获取':'推断使用的字段组合'}</div>${ex.names.slice(0,4).map(n=>`<span class="field-pill"><i class="dot"></i>${h(n)} ${lv(D.字段.find(f=>f.中文名===n)?.一次等级||1)}</span>`).join('')}${ex.names.length>4?`<small>等 ${ex.names.length} 个字段</small>`:''}</div><div class="flow-arrow">→</div><div class="flow-card risk"><div class="flow-caption">${icon('lock')}组合推断 · ${h(ex.name)}</div><div class="score number">${fmt(ex.step?.精度)}</div><strong>组合推断 R²</strong><small>${ex.rec?'接收方判定线 '+fmt(ex.rec.判定线,2):'已记录组合的推断精度'}${ex.step?.精度>(ex.rec?.判定线??1)?' · 已越线':''}</small></div><div class="flow-arrow">→</div><div class="flow-card result"><div class="flow-caption">${icon('shield')}重新定级后 · 全部可见字段</div><div class="score number ${ex.cap?.定级后>ex.cap?.判定线?'amber':''}">${fmt(ex.cap?.定级后)}</div><strong>${!ex.cap?'查看各接收方复核结果':ex.cap.定级后>ex.cap.判定线?'仍有推断风险':'该接收方复核未越线'}</strong><small>${ex.cap?h(ex.cap.接收方)+' · 两种模型取较高值':'该组合无对应的低权限接收方'}</small></div></div>
 <div class="hero-bottom"><span>R² 衡量推断效果，越接近 1 越易还原；组合与全字段复核采用不同输入范围。</span>${navLink('risk',`展开推断证据 ${icon('arrow')}`,'text-button')}</div></section>
 <div class="stats">${stat('纳入审查的字段',`${D.字段.length}<small> 个</small>`,`${candidate().length} 个候选共享字段 · ${D.敏感.length} 项保护对象`,'database')}${stat('初始越线组合',`${count(before)}<small> 组</small>`,'按接收方 × 保护对象 × 字段组合计数','risk')}${stat('调整等级的字段',`${adjusted().length}<small> / ${candidate().length}</small>`,'直接定级与强化学习共同确定','tune')}${stat('调级后仍越线的复核项',`<span class="${risks?'amber':'teal'}">${risks}</span><small> / ${D.接收方能力.length}</small>`,`${after} 个已识别组合仍可成立${D.仅凭公开基底可推出.length?' · 含公开基底风险':''}`,'shield')}</div>
 ${D.仅凭公开基底可推出.length?notice('该任务存在仅凭公开信息即可推出的保护对象','候选字段调级无法消除这些风险，已在最终复核中保留显示。',true):''}
 <div class="grid-equal"><section class="panel">${panelHead('按接收方看初始风险','取其可获取的全部字段，分别推断受保护数据。',receiverSelect())}${representative.length?representative.map(x=>`<div class="risk-row"><span>${h(x.敏感数据)}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(0,Math.min(1,x.定级前))*100}%;background:${x.定级前>x.判定线?C.red:'#82b29e'}"></div><i class="threshold" style="left:${x.判定线*100}%"></i></div><strong class="number ${x.定级前>x.判定线?'red':'teal'}">${fmt(x.定级前)}</strong></div>`).join(''):'<div class="empty">该接收方没有待核对的保护对象。</div>'}<div class="mini-legend"><span><i style="background:${C.red}"></i>超过判定线</span><span><i style="background:#82b29e"></i>未超过判定线</span><span>虚线为该接收方的判定线</span></div></section>
 <section class="panel">${panelHead('从规则定级，到推断验证','一条可追溯的分析链路。') }<div class="method-list">${[['01','明确保护边界','规则库初判与复核，建立字段等级和共享范围。','grade1'],['02','发现组合风险','模拟合法接收方推断，定位产生增益的关键字段。','risk'],['03','调整并重新验证','权衡风险与共享成本，复核最终方案并保留证据。','effect']].map(x=>`<div class="method-item"><span class="method-number">${x[0]}</span><div><strong>${x[1]}</strong><p>${x[2]}</p></div><a data-page="${x[3]}" href="${url(x[3])}" aria-label="${x[1]}">${icon('chevron')}</a></div>`).join('')}</div></section></div>
 <section class="panel">${panelHead('跨场景算例','沿用同一套推断验证与定级流程。',navLink('tasks','全部任务 →','text-button'))}<div class="task-strip">${Object.values(ALL).map(d=>`<button class="task-mini ${d.id===S.task?'selected':''}" data-task="${h(d.id)}"><strong>${h(META[d.id]?.short||d.名称)} ${d.id===S.task?'· 当前':''}</strong><small>${h(d.类别)} · ${count(d.样本数)} 条 · ${d.字段.length} 个字段</small></button>`).join('')}</div></section>`;
}
function pageTasks(){
 $('#main').innerHTML=`${notice('选择一个任务，查看从初始定级到效果复核的完整证据','内置结果可直接交互查看。可导入本系统导出的任务结果 JSON；原始数据上传与新任务训练暂未接入。')}<div class="task-cards">${Object.values(ALL).map(d=>`<article class="panel task-card ${d.id===S.task?'selected':''}"><span class="task-icon">${icon(META[d.id]?.icon||'database')}</span>${d.id===S.task?'<span class="task-selected tag good">当前任务</span>':''}<h2>${h(META[d.id]?.name||d.名称)}</h2><p>${h(d.数据说明)}</p><div class="mini-legend"><span>${tag(d.类别)}</span><span>${count(d.样本数)} 条样本</span><span>${candidate(d).length} 个候选字段</span><span>${d.敏感.length} 项保护对象</span></div><footer><span class="small-text ${riskCount('定级后',d)?'amber':'teal'}">复核：${riskCount('定级后',d)} 项仍越线 / ${d.接收方能力.length} 项</span><button class="button ${d.id===S.task?'':'primary'}" data-open-task="${h(d.id)}">${d.id===S.task?'查看当前任务':'进入任务'} ${icon('arrow')}</button></footer></article>`).join('')}</div>`;
 $$('[data-open-task]').forEach(e=>e.onclick=()=>{S.page='overview';setTask(e.dataset.openTask);window.scrollTo(0,0);});
}
function pageGrade(){
 const shown=D.字段.filter(f=>(S.filter==='全部'||(S.filter==='保护对象'?f.角色==='敏感':S.filter==='候选共享'?f.角色==='候选':f.复核调整))&&(!S.kw||[f.中文名,f.字段].some(v=>v.toLowerCase().includes(S.kw.toLowerCase()))));
 const selected=D.字段.find(f=>f.字段===S.sel)&&shown.find(f=>f.字段===S.sel)||shown[0];
 if(selected)S.sel=selected.字段;
 $('#main').innerHTML=`<div class="stats">${stat('数据资产',`${D.字段.length}<small> 个字段</small>`,h(D.类别),'database')}${stat('保护对象',`${D.敏感.length}<small> 项</small>`,'检验能否被低权限接收方推出','lock')}${stat('初判与复核',`<span class="model-name">${h(D.大语言模型.startsWith('deepseek')?'DeepSeek':D.大语言模型)}</span>`,`${h(D.大语言模型)} · ${D.字段.filter(f=>f.复核调整).length} 项修正`,'check')}${stat('规则依据','GB/T <small>43697</small>','结构化规则库 · 影响对象 × 影响程度','book')}</div>
 <div class="grid-2"><section class="panel">${panelHead('初始定级结果','点击字段，在右侧查看该字段对应的初判与复核依据。',tag('一次定级','blue'))}<div class="filterbar"><div class="segmented" role="group" aria-label="字段筛选">${['全部','候选共享','保护对象','已修正'].map(f=>`<button class="${f===S.filter?'active':''}" data-filter="${f}" aria-pressed="${f===S.filter}">${f}</button>`).join('')}</div><div class="search-wrap"><input class="search" id="field-search" aria-label="搜索字段" placeholder="搜索字段名称或编码" value="${h(S.kw)}"></div></div><div class="table-wrap scroll"><table><thead><tr><th>字段名称</th><th>用途</th><th>初始等级</th><th>复核状态</th></tr></thead><tbody>${shown.map(f=>`<tr class="${f===selected?'selected':''}"><td><button class="table-button" data-field="${h(f.字段)}">${h(f.中文名)}</button><span class="table-sub">${h(f.字段)}</span></td><td>${tag(f.角色==='敏感'?'保护对象':f.角色==='候选'?'候选共享':'公开基底',f.角色==='敏感'?'warning':'')}</td><td>${lv(f.一次等级)}</td><td>${tag(f.复核调整?'修正初判':'已复核',f.复核调整?'blue':'good')}</td></tr>`).join('')||'<tr><td colspan="4" class="empty">没有匹配的字段，请调整搜索条件。</td></tr>'}</tbody></table></div><div class="table-summary">显示 ${shown.length} / ${D.字段.length} 个字段 · 公开数据集的等级为本任务场景设定。</div></section>
 <aside class="panel detail-panel">${selected?gradeDetail(selected):'<div class="empty">选择一个字段查看依据。</div>'}</aside></div>
 ${next('逐字段定级之后，还要检查组合产生的风险','接收方能同时拿到多个字段，初始等级无法单独说明组合的推断能力。','risk','查看推断风险')}`;
 $$('[data-filter]').forEach(e=>e.onclick=()=>{S.filter=e.dataset.filter;S.sel=null;render();});
 $$('[data-field]').forEach(e=>e.onclick=()=>{const scroll=$('.table-wrap.scroll').scrollTop;S.sel=e.dataset.field;render();$('.table-wrap.scroll').scrollTop=scroll;});
 $('#field-search').oninput=e=>{S.kw=e.target.value;const pos=e.target.selectionStart;render();$('#field-search').focus();$('#field-search').setSelectionRange(pos,pos);};
}
function gradeDetail(f){
 return `<div class="detail-eyebrow">当前选中字段 · 定级依据</div><h2 class="detail-title">${h(f.中文名)} ${lv(f.一次等级)}</h2><p>${h(f.说明)}</p><div class="detail-grid"><div><span>影响对象</span><strong>${h(f.影响对象)}</strong></div><div><span>影响程度</span><strong>${h(f.影响程度)}</strong></div><div><span>公开情况</span><strong>${h(f.公开情况)}</strong></div><div><span>初判 → 复核后</span><strong>${lv(f.初判?.等级??f.一次等级)} → ${lv(f.一次等级)}</strong></div></div><h3>${f.复核调整?'复核修正说明':'定级理由'}</h3><div class="reason">${h(f.复核调整?f.复核理由:f.初判?.理由||'按本任务规则库复核。')}</div><div class="citation">匹配的规则库条目<br>${(f.检索到的条文||[]).map(n=>tag(n)).join('')}</div><details class="explanation"><summary>查看初判原文与条文摘要</summary><p>${h(f.初判?.理由||'未提供初判原文')}</p>${D.条文.filter(a=>(f.检索到的条文||[]).includes(a.编号)).map(a=>`<p><strong>${h(a.编号)} · ${h(a.标题)}</strong><br>${h(a.内容)}</p>`).join('')}</details>`;
}
function riskMatrix(key='定级前'){
 const receivers=D.接收方.filter(r=>r.级<4);
 return `<div class="table-wrap"><table class="matrix"><thead><tr><th>受保护数据 / 初始等级</th>${receivers.map(r=>`<th>${h(r.名称)}<span class="table-sub">${r.级} 级及以下 · 判定线 ${fmt(r.判定线,2)}</span></th>`).join('')}</tr></thead><tbody>${D.敏感.map((n,t)=>`<tr><td><strong>${h(n)}</strong> ${lv(protectedFields().find(f=>f.中文名===n)?.一次等级)}</td>${receivers.map(r=>{const x=D.接收方能力.find(a=>a.接收方===r.名称&&a.敏感数据===n);return `<td>${!x?'<span class="authorized">本任务允许直接获取</span>':`<button class="matrix-cell ${x[key]>x.判定线?'danger':''} ${baseRisk(x)?'warning':''} ${S.t===t&&S.r===r.名称?'selected':''}" data-cell="${t}" data-receiver="${h(r.名称)}" aria-label="${h(r.名称)}推断${h(n)}，R² ${fmt(x[key])}"><span class="number">${fmt(x[key])}</span><small>${baseRisk(x)?'公开基底风险':x[key]>x.判定线?'越线':'未越线'}</small></button>`}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function pageRisk(){
 const r=D.接收方.find(r=>r.名称===S.r),name=target(),cap=D.接收方能力.find(c=>c.接收方===S.r&&c.敏感数据===name);
 const combos=D.一次定级下的越线.filter(x=>x.敏感数据===name&&x.接收方===S.r).sort((a,b)=>b.精度-a.精度);
 const ladder=D.阶梯[S.t],curve=D.曲线[S.t];
 const allowed=ladder.步骤.map(s=>s.组合.every(n=>n==='仅公开基底'||(D.字段.find(f=>f.中文名===n)?.一次等级??Infinity)<=r.级));
 const maxStep=allowed.lastIndexOf(true);S.step=Math.max(0,Math.min(S.step,maxStep));
 $('#main').innerHTML=`<section class="panel">${panelHead('初始定级后，哪些接收方仍能推断出受保护数据','使用接收方能获取的全部字段；R² 为神经网络与梯度提升树的较高值。',tag(`${riskCount('定级前')} 项越线`,'danger'))}${riskMatrix()}<div class="mini-legend"><span><i style="background:#d99588"></i>超过判定线，存在推断风险</span><span><i style="background:#8eb8a4"></i>当前核对未越线</span><span>点击数值，查看该对象的组合证据</span></div></section>
 <div class="target-bar">${tabs()}${receiverSelect()}</div>
 ${!cap?notice(`${h(S.r)}在本任务中允许直接获取「${h(name)}」`,'该项不属于此接收方的越权推断目标；可切换接收方查看风险证据。'):baseRisk(cap)?notice('该对象仅凭公开基底即可推出','以下组合是在已掌握公开基底的条件下测得；调整候选字段的等级无法消除基底本身的推断风险。',true):''}
 <div class="grid-2"><section class="panel">${panelHead('逐步加入字段，观察推断结果',`${h(S.r)} → ${h(name)} · 初始共享权限`, '<button class="button small" id="play-steps">'+icon('play')+' 自动演示</button>')}
 <div class="step-buttons">${ladder.步骤.map((s,i)=>`<button class="step-button ${i===S.step?'active':''}" data-step="${i}" ${!allowed[i]?'disabled':''} title="${allowed[i]?'查看该累计组合的真实计算结果':'该组合含当前接收方无权获取的字段'}"><b>步骤 ${i+1}${!allowed[i]?' · 权限不足':''}</b>＋ ${h(s.加入)}</button>`).join('')}</div>
 <div class="curve-summary"><span id="curve-caption"></span><span>R² <strong class="number" id="curve-score"></strong></span></div><div class="chart" id="curve-chart" role="img" aria-label="真实值与当前组合的推断值对比"></div><div class="chart-note">${h(D.横轴)} · 展示缓存的样本${D.时间序列?'曲线':'，按真实值排列'}。多分量数据仅画首个分量，R² 为组合在全部分量上的评估值。</div></section>
 <section class="panel">${panelHead('已识别的最小越线组合',`当前接收方与保护对象下共 ${combos.length} 组。`,tip('这些字段共同可用时推断越线，去掉其中任何一个则不再越线。这里的组合数按接收方分别计算。'))}<div style="max-height:445px;overflow:auto">${combos.slice(0,S.comboLimit).map(x=>`<article class="combo"><div><strong>${x.组合.map(h).join(' ＋ ')||'仅公开基底'}</strong><small>${h(S.r)}可同时获取 · 判定线 ${fmt(r.判定线,2)}</small></div><div class="number">${fmt(x.精度)}</div></article>`).join('')||`<div class="empty">${baseRisk(cap||{})?'公开基底已足以推断该对象。':'已核对范围内，未发现该接收方的最小越线组合。'}</div>`}</div>${combos.length>S.comboLimit?`<button class="text-button" id="more-combos">展开其余 ${combos.length-S.comboLimit} 组 ↓</button>`:''}<div class="chart-note">已核对 ${count(D.已核对的组合数)} 个组合；候选组合上限 ${D.组合上限} 个字段。全字段风险与小组合风险需分别核对。</div></section></div>
 ${next('下一步：定位造成推断增益的字段','同一个字段，与不同背景信息组合时，作用可能完全不同。','sens','查看字段敏感度')}`;
 $$('[data-cell]').forEach(e=>e.onclick=()=>{S.t=Number(e.dataset.cell);S.r=e.dataset.receiver;S.step=0;S.comboLimit=8;render();writeURL();});
 if($('#more-combos'))$('#more-combos').onclick=()=>{S.comboLimit=combos.length;render();};
 if(maxStep<0){$('#curve-chart').innerHTML='<div class="empty">记录的推断路径不适用于当前接收方：首步已包含超出其权限的字段。</div>';$('#curve-caption').textContent='请选择其他接收方';$('#curve-score').textContent='—';$('#play-steps').disabled=true;return;}
 activeChart=chart('#curve-chart',{legend:{top:0,right:0,itemWidth:17,itemHeight:8,textStyle:{fontSize:10,color:C.muted}},xAxis:{type:'category',data:curve.真实.map((_,i)=>i+1),boundaryGap:false,axisLabel:{color:C.muted},axisLine:{lineStyle:{color:C.grid}},axisTick:{show:false}},yAxis:{type:'value',scale:true,splitLine:{lineStyle:{color:C.grid}},axisLabel:{fontSize:9}},series:[{name:'真实值',type:'line',data:curve.真实,showSymbol:false,lineStyle:{color:'#7b8fa5',width:1.8},itemStyle:{color:'#7b8fa5'}},{name:'推断值',type:D.时间序列?'line':'scatter',data:[],showSymbol:!D.时间序列,symbolSize:3,lineStyle:{color:C.red,width:1.6},itemStyle:{color:C.red}}]});
 const show=i=>{S.step=i;const s=ladder.步骤[i];$('#curve-caption').textContent=`${s.组合[0]==='仅公开基底'?'仅使用公开基底':`已加入 ${s.组合.length} 个候选字段${D.字段.some(f=>f.角色==='公开基底')?' + 公开基底':''}`} · 判定线 ${fmt(r.判定线,2)}`;$('#curve-score').textContent=fmt(s.精度);$('#curve-score').style.color=s.精度>r.判定线?C.red:C.teal;$$('[data-step]').forEach(e=>e.classList.toggle('active',Number(e.dataset.step)===i));activeChart.setOption({series:[{},{data:curve.还原[i]?.值||[]}]});};
 show(S.step);$$('[data-step]').forEach(e=>e.onclick=()=>{clearInterval(S.timer);$('#play-steps').innerHTML=icon('play')+' 自动演示';show(Number(e.dataset.step));});
 $('#play-steps').onclick=()=>{clearInterval(S.timer);let i=0;show(i);$('#play-steps').textContent='演示中…';S.timer=setInterval(()=>{if(i>=maxStep){clearInterval(S.timer);$('#play-steps').innerHTML=icon('play')+' 重新演示';return;}show(++i);},1300);};
}
function pageSensitivity(){
 const fields=candidate(),snapshots=D.背景增益;S.K=Math.min(S.K,snapshots.length-1);const ti=S.t;
 const order=fields.map((f,i)=>i).sort((a,b)=>snapshots.at(-1).M[b][ti]-snapshots.at(-1).M[a][ti]);
 const current=Math.max(0,fields.findIndex(f=>f.字段===S.sel));if(S.sel===null)S.sel=fields[order[0]].字段;
 const index=S.sel===null?current:Math.max(0,fields.findIndex(f=>f.字段===S.sel));
 $('#main').innerHTML=`${notice('衡量字段在组合中的贡献','字段推断敏感度 M：接收方已有至多 K 个其他字段时，再获得该字段所带来的最大推断增益。K = 0 用于对照单字段情形。')}<div class="target-bar">${tabs()}${tag('定级采用 K = '+D.参数.K,'good')}</div><div class="grid-2"><section class="panel">${panelHead('背景信息越多，字段的作用可能越大','拖动 K，比较各字段的最大推断增益。该交互只查看已有计算结果。',tip('M 是增量贡献，不是最终推断精度。PJM 的所有组合始终包含法定公开基底。'))}<div class="range-control"><label for="sensitivity-k">已有其他字段数上限</label><input type="range" id="sensitivity-k" min="0" max="${snapshots.length-1}" step="1" value="${S.K}" aria-label="背景字段数量上限 K"><strong>K = <span id="k-value">${snapshots[S.K].K}</span></strong></div><div class="sensitivity-list">${order.slice(0,14).map(i=>`<button class="sensitivity-row ${i===index?'selected':''}" data-sens-field="${i}" aria-pressed="${i===index}"><strong>${h(fields[i].中文名)}</strong><span class="bar-track"><span class="baseline" style="width:${snapshots[0].M[i][ti]*100}%"></span><span class="bar-fill" id="sens-bar-${i}" style="display:block"></span><i class="threshold" style="left:${D.参数.直接定级线*100}%"></i></span><span class="number" id="sens-value-${i}"></span></button>`).join('')}</div><div class="mini-legend"><span><i style="background:#57a18b"></i>当前 K 的最大增益</span><span><i style="background:#c0d6cc"></i>K = 0 对照</span><span>虚线：直接定级线 ${D.参数.直接定级线}</span></div>${fields.length>14?'<p class="chart-note">按最大背景范围的敏感度排列前 14 个字段；完整矩阵见下方。</p>':''}</section><aside class="panel detail-panel"><div class="detail-eyebrow">选中字段 → ${h(target())}</div><h2>${h(fields[index].中文名)}</h2><p class="small-text muted">在当前背景范围内的最大推断增益</p><div class="large-value number" id="selected-m"></div><div id="sensitivity-status"></div><div class="chart" id="sensitivity-line" style="height:190px"></div><div class="witness"><span class="muted">达到此增益时，接收方已有的字段</span><p id="witness-fields"></p></div><div class="kv"><span>当前定级方案</span><strong>${lv(fields[index].一次等级)} → ${lv(fields[index].二次等级)}</strong></div><p class="chart-note">拖动 K 仅切换分析视图，不会修改已生成的定级方案。</p></aside></div>
 <section class="panel">${panelHead('字段 × 保护对象：敏感度矩阵',`完整 ${fields.length} 个候选字段，使用定级时记录的 M 值。`)}<div class="table-wrap scroll"><table><thead><tr><th>候选字段</th>${D.敏感.map(n=>`<th>${h(n)}</th>`).join('')}<th>最终等级</th></tr></thead><tbody>${fields.map(f=>`<tr><td><strong>${h(f.中文名)}</strong></td>${f.M.map(m=>`<td style="background:${m>=D.参数.直接定级线?'#fff2ec':m>=.3?'#eff7f3':'#fbfcfd'}" class="number ${m>=D.参数.直接定级线?'red':'teal'}">${fmt(m)}</td>`).join('')}<td>${lv(f.二次等级)}</td></tr>`).join('')}</tbody></table></div></section>${next('依据字段贡献，形成新的等级方案','高敏感度字段先直接定级，其余字段由强化学习联合权衡。','regrade','查看调级方案')}`;
 chart('#sensitivity-line',{grid:{left:33,right:13,top:18,bottom:27},xAxis:{type:'category',data:snapshots.map(s=>'K='+s.K),axisTick:{show:false},axisLine:{lineStyle:{color:C.grid}}},yAxis:{type:'value',min:0,max:1,splitLine:{lineStyle:{color:C.grid}}},series:[{type:'line',data:snapshots.map(s=>s.M[index][ti]),symbolSize:6,itemStyle:{color:C.teal},lineStyle:{width:2},areaStyle:{color:'#edf7f2'},markLine:{silent:true,symbol:'none',label:{show:false},lineStyle:{color:C.red,type:'dashed'},data:[{yAxis:D.参数.直接定级线}]}}]});
 const update=k=>{S.K=k;const s=snapshots[k];$('#k-value').textContent=s.K;order.slice(0,14).forEach(i=>{const m=s.M[i][ti];$('#sens-bar-'+i).style.width=`${Math.max(0,Math.min(m,1))*100}%`;$('#sens-bar-'+i).style.background=m>=D.参数.直接定级线?C.red:'#57a18b';$('#sens-value-'+i).textContent=fmt(m);});const m=s.M[index][ti];$('#selected-m').textContent=fmt(m);$('#selected-m').style.color=m>=D.参数.直接定级线?C.red:C.teal;$('#sensitivity-status').innerHTML=tag(m>=D.参数.直接定级线?'达到直接定级线':'未达到直接定级线',m>=D.参数.直接定级线?'danger':'good');$('#witness-fields').textContent=s.见证[index][ti].join(' ＋ ')||'无需其他候选字段';};
 update(S.K);$('#sensitivity-k').oninput=e=>update(Number(e.target.value));$$('[data-sens-field]').forEach(e=>e.onclick=()=>{S.sel=fields[Number(e.dataset.sensField)].字段;render();});
}
function pageRegrade(){
 const all=candidate().slice().sort((a,b)=>(b.二次等级-b.一次等级)-(a.二次等级-a.一次等级)||Math.max(...b.M)-Math.max(...a.M));const list=all.filter(f=>S.filter!=='仅调整'||f.二次等级>f.一次等级);const f=list.find(f=>f.字段===S.sel)||list[0];if(f)S.sel=f.字段;
 const G=D.GRPO,before=D.一次定级下的越线.length,after=D.二次定级后的越线.length;
 $('#main').innerHTML=`<div class="stats">${stat('上调字段',`${adjusted().length}<small> / ${all.length}</small>`,`${adjusted().filter(f=>f.依据?.直接定级).length} 个字段触发直接定级`,'tune')}${stat('已识别组合的变化',`${count(before)} <small>→</small> <span class="teal">${after}</span>`,'组合被切断，不代表全字段复核通过','nodes')}${stat('策略综合效用',fmt(G.效用,2),`初始方案 ${fmt(G.只做一次定级.效用,2)} · 越接近 0 越好`,'risk')}${stat('最终复核仍越线',`<span class="${riskCount('定级后')?'amber':'teal'}">${riskCount('定级后')}</span><small> 项</small>`,'以最终可见全字段和两种模型复测','shield')}</div>
 <div class="grid-2"><section class="panel">${panelHead('字段等级调整清单','点击字段，查看上调依据和降回原等级时的影响。',`<div class="segmented">${['全部','仅调整'].map(n=>`<button data-change-filter="${n}" class="${S.filter===n?'active':''}">${n}</button>`).join('')}</div>`)}<div class="table-wrap scroll"><table><thead><tr><th>字段</th><th>初始等级</th><th>最终等级</th><th>调整方式</th><th>最大 M</th></tr></thead><tbody>${list.map(x=>`<tr class="${x===f?'selected':''}"><td><button class="table-button" data-regrade-field="${h(x.字段)}">${h(x.中文名)}</button></td><td>${lv(x.一次等级)}</td><td>${lv(x.二次等级)}</td><td>${tag(upKind(x),x.二次等级>x.一次等级?'blue':'')}</td><td class="number">${fmt(Math.max(...x.M))}</td></tr>`).join('')||'<tr><td colspan="5" class="empty">没有调整的字段。</td></tr>'}</tbody></table></div></section><aside class="panel detail-panel">${f?regradeDetail(f):'<div class="empty">没有调整记录。</div>'}</aside></div>
 <section class="panel">${panelHead('强化学习如何权衡风险与共享成本','综合效用由多项惩罚构成；各项值以当前算例记录为准。',navLink('policy','策略设置 →','text-button'))}<div class="utility">${Object.entries(G.效用构成).map(([k,v])=>`<div><span>${h(k)}</span><strong class="number">${fmt(v,2)}</strong></div>`).join('')}</div><div class="chart" id="training-chart" role="img" aria-label="强化学习训练综合效用曲线"></div><details class="explanation"><summary>查看求解与精确参照说明</summary><p>求解方法：${h(D.求解方式)}。训练 ${D.参数.steps} 步，每步采样 ${D.参数.group} 套方案；严格模式${G.严格模式?'开启':'关闭'}。${G.参照最优!=null?`策略效用 ${fmt(G.效用)}，参照最优 ${fmt(G.参照最优)}（${h(G.参照最优求法)}）。`:`${h(G.参照最优求法)}。`} ${G.最终效用!=null?`经最终处理后的效用为 ${fmt(G.最终效用)}，与训练策略效用分开记录。`:''}</p></details></section>
 ${next('调级方案需要独立核对，不能仅凭组合数判定效果','复核接收方最终能拿到的全部字段，并保留仍然越线的项目。','effect','查看最终效果')}`;
 const tr=G.训练曲线;chart('#training-chart',{legend:{top:0,right:0,itemWidth:15,textStyle:{fontSize:10}},grid:{left:55,right:20,top:36,bottom:28},xAxis:{type:'category',data:tr.map(x=>x.步),axisLine:{lineStyle:{color:C.grid}},axisTick:{show:false},name:'训练步',nameLocation:'middle',nameGap:23},yAxis:{type:'value',scale:true,splitLine:{lineStyle:{color:C.grid}}},series:[{name:'组内平均效用',type:'line',data:tr.map(x=>x.组内平均),showSymbol:false,lineStyle:{width:2,color:C.teal},itemStyle:{color:C.teal},areaStyle:{color:'#f0f7f3'}},{name:'组内最好效用',type:'line',data:tr.map(x=>x.组内最好),showSymbol:false,lineStyle:{width:1.5,color:C.blue},itemStyle:{color:C.blue}}]});
 $$('[data-change-filter]').forEach(e=>e.onclick=()=>{S.filter=e.dataset.changeFilter;S.sel=null;render();});$$('[data-regrade-field]').forEach(e=>e.onclick=()=>{const top=$('.table-wrap.scroll').scrollTop;S.sel=e.dataset.regradeField;render();$('.table-wrap.scroll').scrollTop=top;});
}
function regradeDetail(f){
 const reason=f.依据,changed=f.二次等级>f.一次等级;
 return `<div class="detail-eyebrow">当前选中字段 · 调整依据</div><h2 class="detail-title">${h(f.中文名)}</h2><p>${lv(f.一次等级)}　→　${lv(f.二次等级)}　${tag(upKind(f),changed?'blue':'')}</p><div class="reason">${!changed?'当前方案保留初始等级。该字段的贡献已纳入联合评估。':reason?.直接定级?`对「${h(reason.对应敏感数据)}」的敏感度达到直接定级线 ${D.参数.直接定级线}，按保护目标等级上调。`:f.整体核对上调?`整体核对发现「${h(f.整体核对上调.接收方)}」仍可推断「${h(f.整体核对上调.敏感数据)}」，继续调整该字段。`:'强化学习在整套等级方案中联合权衡推断风险与共享成本，选择上调该字段。'}</div>${changed?`<h3>若降回原等级</h3><p class="small-text muted">记录中将重新成立 ${reason?.重新成立的数量??0} 个越线组合。</p>${(reason?.重新成立的越线组合||[]).slice(0,4).map(x=>`<div class="kv"><div>${h(x.接收方)} → ${h(x.敏感数据)}<div class="small-text">${x.组合.map(h).join(' ＋ ')}</div></div><strong class="number red">${fmt(x.精度)}</strong></div>`).join('')}${!(reason?.重新成立的越线组合||[]).length?'<p class="chart-note">未记录单独恢复此字段后的最小组合；可结合整体核对和联合策略判断。</p>':''}`:''}<div class="citation">最大字段敏感度 M = ${fmt(Math.max(...f.M))}<br>等级上调会缩小可共享范围，具体影响见效果复核。</div>`;
}
function pageEffect(){
 const before=riskCount('定级前'),after=riskCount('定级后'),rows=D.换模型复测;
 $('#main').innerHTML=`<section class="result-head ${after?'warning':''}">${icon(after?'alert':'shield')}<div><h2>${after?`最终复核仍有 ${after} 项推断越线，需继续处理。`:'当前已核对的接收方与保护对象均未越线。'}</h2><p>${before} 项初始越线 → ${after} 项最终越线 · ${rows.length} 组模型复测 · ${D.二次定级后的越线.length} 个已识别越线组合仍可成立</p></div></section>
 <div class="grid-2"><section class="panel">${panelHead('全字段推断能力：初始定级 → 二次定级','所有接收方与受保护对象均显示，包括公开基底风险。')}<div id="effect-chart" style="height:${Math.max(300,D.接收方能力.length*44+60)}px" role="img" aria-label="各接收方调级前后推断精度与判定线"></div></section><div class="stack"><section class="panel">${panelHead('共享范围的变化','只统计候选共享字段；公开基底始终可见。')}<div class="table-wrap"><table><thead><tr><th>接收方</th><th>初始可获取</th><th>最终可获取</th></tr></thead><tbody>${D.接收方.map(r=>`<tr><td>${h(r.名称)}</td><td class="number">${candidate().filter(f=>f.一次等级<=r.级).length}</td><td class="number"><strong>${candidate().filter(f=>f.二次等级<=r.级).length}</strong></td></tr>`).join('')}</tbody></table></div></section><section class="panel">${panelHead('结果与证据导出','保留字段等级、规则依据和核对结果。')}<div class="stack"><button class="button primary" data-export="csv">${icon('download')} 导出字段定级台账 · CSV</button><button class="button" data-export="json">${icon('download')} 导出完整任务结果 · JSON</button></div><p class="chart-note">台账记录初始与最终等级；完整结果包含风险组合、推断曲线和复核记录，可在任务管理中重新导入。</p></section><section class="panel">${panelHead('验证范围','结论限定在当前数据、权限和已核对模型内。')}<div class="kv"><span>已核对的字段组合</span><strong>${count(D.已核对的组合数)}</strong></div><div class="kv"><span>最大候选组合规模</span><strong>${D.组合上限} 个字段</strong></div><div class="kv"><span>最终全字段模型复测</span><strong>${rows.length} 组</strong></div><p class="chart-note">未越线表示当前实测低于判定线，不表示所有未知推断方法都无法还原。</p></section></div></div>
 ${D.仅凭公开基底可推出.length?notice('公开信息带来的保护边界',`「${[...new Set(D.仅凭公开基底可推出.map(x=>x.敏感数据))].map(h).join('、')}」仅凭公开基底即可推断。此类风险无法通过上调候选字段等级消除，需重新审视保护目标与发布策略。`,true):''}
 <section class="panel">${panelHead('两种模型复测明细','对最终可获取的全部字段重新训练，任一模型越线即记录为风险。')}<div class="table-wrap"><table><thead><tr><th>接收方</th><th>受保护数据</th><th>神经网络 R²</th><th>梯度提升树 R²</th><th>判定线</th><th>复核结论</th></tr></thead><tbody>${rows.map(x=>{const bad=Math.max(x.神经网络,x.梯度提升树)>x.判定线;return `<tr><td>${h(x.接收方)}</td><td><strong>${h(x.敏感数据)}</strong></td><td class="number ${x.神经网络>x.判定线?'red':''}">${fmt(x.神经网络)}</td><td class="number ${x.梯度提升树>x.判定线?'red':''}">${fmt(x.梯度提升树)}</td><td class="number">${fmt(x.判定线,2)}</td><td>${tag(baseRisk(x)?'公开基底风险':bad?'仍越线':'未越线',baseRisk(x)?'warning':bad?'danger':'good')}</td></tr>`;}).join('')}</tbody></table></div>${D.快速估计?`<details class="explanation"><summary>快速估计与重训核对记录</summary><p>快速估计 ${count(D.快速估计.估计的组合数)} 个组合，重新训练核对 ${count(D.快速估计.重新训练核对的组合数)} 个。平均绝对误差 ${fmt(D.快速估计.平均绝对误差)}；抽查被筛除组合 ${D.快速估计.随机抽查数} 个，其中实际越线 ${D.快速估计.抽查中被筛掉却实际越线的} 个。最终效果以本页全字段重训复测为准。</p></details>`:''}</section>
 ${D.二次定级后的越线.length?`<section class="panel section-gap">${panelHead('剩余越线组合')}<div class="table-wrap scroll"><table><thead><tr><th>接收方</th><th>保护对象</th><th>组合</th><th>R²</th></tr></thead><tbody>${D.二次定级后的越线.map(x=>`<tr><td>${h(x.接收方)}</td><td>${h(x.敏感数据)}</td><td class="wrap-cell">${x.组合.map(h).join(' ＋ ')}</td><td>${fmt(x.精度)}</td></tr>`).join('')}</tbody></table></div></section>`:''}`;
 const A=D.接收方能力.slice().reverse();chart('#effect-chart',{grid:{left:window.innerWidth<700?125:170,right:37,top:32,bottom:24},legend:{top:0,right:0,textStyle:{fontSize:10},itemWidth:12,itemHeight:8},xAxis:{type:'value',min:0,max:Math.max(1,...A.map(x=>x.定级前),...A.map(x=>x.定级后)),splitLine:{lineStyle:{color:C.grid}}},yAxis:{type:'category',data:A.map(x=>x.接收方+'\n'+x.敏感数据),axisTick:{show:false},axisLine:{show:false},axisLabel:{fontSize:10,lineHeight:15,width:150,overflow:'truncate'}},series:[{name:'初始定级',type:'bar',data:A.map(x=>x.定级前),barWidth:8,itemStyle:{color:'#dfbeb3',borderRadius:[0,3,3,0]}},{name:'二次定级',type:'bar',data:A.map(x=>({value:x.定级后,itemStyle:{color:x.定级后>x.判定线?C.red:C.teal}})),barWidth:8,label:{show:true,position:'right',fontSize:9,formatter:p=>fmt(p.value,2)},itemStyle:{borderRadius:[0,3,3,0]}},{name:'判定线',type:'scatter',symbol:'rect',symbolSize:[2,26],data:A.map(x=>x.判定线),itemStyle:{color:'#6b7f8b'},z:5}]});
}
function pageRules(){
 $('#main').innerHTML=`${notice('本任务的定级依据与权限映射','规则库依据 GB/T 43697 整理；公开数据集中的字段等级是场景化示例，接收方按本任务设定的等级范围获取字段。')}<section class="panel">${panelHead('等级决定共享范围','在本任务中，接收方可获取其授权级别及以下的数据。')}<div class="table-wrap"><table><thead><tr><th>等级</th><th>共享范围</th><th>任务中的接收方</th><th>初始字段数</th><th>最终字段数</th></tr></thead><tbody>${D.等级表.map(l=>`<tr><td>${lv(l.级)}</td><td class="wrap-cell">${h(l.共享范围)}</td><td>${h(l.接收方)}</td><td>${D.字段.filter(f=>f.一次等级===l.级).length}</td><td>${D.字段.filter(f=>f.二次等级===l.级).length}</td></tr>`).join('')}</tbody></table></div></section><div class="grid-equal section-gap"><section class="panel">${panelHead('影响对象 × 影响程度','本任务规则库中的等级映射。')}<div class="table-wrap"><table><thead><tr><th>影响对象</th>${['一般危害','严重危害','特别严重危害'].map(x=>`<th>${x}</th>`).join('')}</tr></thead><tbody>${['国家安全','经济运行','社会秩序','公共利益','组织权益','个人权益'].map(k=>`<tr><td>${k}</td>${['一般危害','严重危害','特别严重危害'].map(j=>`<td>${lv(D.判定表[k][j])}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="chart-note">核心、重要、一般数据由影响对象与程度判定；一般数据在本规则库中进一步映射到 1–4 级。</p></section><section class="panel">${panelHead('接收方的推断判定线','仅检验其无权直接获取的保护对象。')}<div class="table-wrap"><table><thead><tr><th>接收方</th><th>可获取等级</th><th>判定线 R²</th></tr></thead><tbody>${D.接收方.map(r=>`<tr><td>${h(r.名称)}</td><td>≤ ${r.级} 级</td><td class="number">${fmt(r.判定线,2)}</td></tr>`).join('')}</tbody></table></div><p class="chart-note">判定线是本系统的实验参数，不是国家标准规定的数值。</p>${navLink('params','查看判定参数 →','text-button')}</section></div><section class="panel">${panelHead('规则库条目','展开查看本项目整理的条文摘要。')}${D.条文.map(x=>`<details class="explanation"><summary>${h(x.编号)}　${h(x.标题)}</summary><p>${h(x.内容)}</p></details>`).join('')}</section>`;
}
const PARAMS={
 '公众判定线':['公众推断判定线','社会公众可见字段的推断 R² 超过该值时记为越线。',.5,.95,.05],
 '其他判定线':['其他接收方判定线','关联方与授权对象采用此阈值。',.5,.95,.05],
 'K':['背景字段数上限 K','计算字段推断敏感度时，考虑至多 K 个已有候选字段。',0,2,1],
 '直接定级线':['直接定级线','字段敏感度 M 达到此值时，按保护目标的等级直接定级。',.5,.95,.05],
 'beta':['安全收益权重 β','提高权重，更倾向于上调存在较高推断贡献的字段。',0,10,.5],
 'lam':['安全收益衰减 λ','字段每上调一级时，剩余风险项的衰减速度。',.1,3,.1],
 'eta':['共享成本权重 η','提高权重，对收紧字段共享范围的成本更加敏感。',0,10,.5],
 'sigma':['共享成本增长 σ','连续上调多个等级时的成本增长速度。',.1,2,.1],
 'rho':['组合风险惩罚 ρ','对仍可成立的越线组合施加惩罚。',0,20,.5],
 'rho_w':['整体推断惩罚 ρw','对全部可见字段仍能推断越线的情况施加惩罚。',0,20,.5],
 'steps':['训练步数','强化学习更新的步数。',50,2000,50],
 'group':['每步采样方案数','每步比较的一组完整定级方案的数量。',16,512,16]
};
function canRun(){return Boolean(S.srv?.完整方式&&S.srv?.可重跑?.includes(S.task));}
function paramRow(k){const [label,desc,min,max,step]=PARAMS[k];return `<div class="kv"><label for="param-${k}">${label} ${tip(desc)}</label><input id="param-${k}" data-param="${k}" type="number" value="${Number(S.params[k])}" min="${min}" max="${max}" step="${step}" ${!canRun()||S.srv?.作业?.状态==='运行中'?'disabled':''}></div>`;}
function runBar(){const job=S.srv?.作业,busy=job?.状态==='运行中';return `<div class="next-step" style="margin:0 0 22px"><div><strong>${busy?'正在运行任务：'+h(META[job.任务]?.short||job.任务):canRun()?'当前任务可修改参数并重新计算':'当前为结果查看模式'}</strong><p>${busy?'计算完成后刷新对应任务的结果。':canRun()?'重跑当前任务的二次定级与复核，将更新该任务的结果文件。':'未检测到当前任务的计算缓存，参数只读；可交互查看全部已生成的结果。'}</p><p id="parameter-status" role="status">${job?.状态==='失败'?'上次重跑失败：'+h(job.日志||'请检查服务日志'):''}</p></div><div class="actions"><button class="button" id="reset-params" ${!canRun()||busy?'disabled':''}>恢复</button><button class="button primary" id="run-params" ${!canRun()||busy?'disabled':''}>${busy?'运行中…':'应用并重跑'}</button></div></div>`;}
function pageParams(){
 $('#main').innerHTML=`${runBar()}<div class="grid-equal"><section class="panel">${panelHead('判断推断是否越线','这些参数比较的是推断效果 R²，越大代表还原效果越强。')}${paramRow('公众判定线')}${paramRow('其他判定线')}</section><section class="panel">${panelHead('定位字段的增量贡献','这些参数作用于字段敏感度 M，和推断效果 R² 含义不同。')}${paramRow('K')}${paramRow('直接定级线')}</section></div>${notice('参数含义与查看范围','字段敏感度页的 K 滑块仅浏览已缓存的背景增益；这里的 K 则决定重跑定级采用的背景规模。')}<section class="panel">${panelHead('当前任务的核对范围')}<div class="kv"><span>候选共享字段</span><strong>${candidate().length} 个</strong></div><div class="kv"><span>已核对的组合</span><strong>${count(D.已核对的组合数)} 个</strong></div><div class="kv"><span>组合规模上限</span><strong>${D.组合上限} 个候选字段</strong></div></section>`;bindParams();
}
function pagePolicy(){
 $('#main').innerHTML=`${runBar()}<div class="grid-equal"><section class="panel">${panelHead('安全与可用性的权衡','综合效用由风险收益与各类成本共同决定。')}${['beta','lam','eta','sigma'].map(paramRow).join('')}</section><section class="panel">${panelHead('对残留推断风险的惩罚','可以权衡风险与成本；严格模式进一步约束越线情况。')}${['rho','rho_w'].map(paramRow).join('')}<div class="kv"><label for="strict">严格模式 ${tip('开启后按求解器的硬条件和整体核对进一步调整字段；最终是否仍越线，以效果复核结果为准。')}</label><input id="strict" data-param="严格模式" type="checkbox" ${S.params.严格模式?'checked':''} ${!canRun()||S.srv?.作业?.状态==='运行中'?'disabled':''}></div></section></div><div class="grid-equal"><section class="panel">${panelHead('组相对策略优化 · GRPO','对同一任务采样多套等级方案，比较综合效用并更新策略。')}${['steps','group'].map(paramRow).join('')}</section><section class="panel">${panelHead('当前方案的记录','训练策略与最终核对结果分别展示。')}<div class="kv"><span>策略综合效用</span><strong>${fmt(D.GRPO.效用)}</strong></div><div class="kv"><span>初始等级方案的效用</span><strong>${fmt(D.GRPO.只做一次定级.效用)}</strong></div><div class="kv"><span>最终方案的效用</span><strong>${fmt(D.GRPO.最终效用)}</strong></div>${navLink('regrade','查看训练过程 →','text-button')}</section></div>`;bindParams();
}
function bindParams(){
 $$('[data-param]').forEach(e=>e.oninput=()=>{S.params[e.dataset.param]=e.type==='checkbox'?e.checked:Number(e.value);$('#parameter-status').textContent='参数已修改，尚未应用。';});
 $('#reset-params').onclick=()=>{S.params={...D.参数};render();};
 $('#run-params').onclick=async()=>{
  for(const [key,[label,desc,min,max]] of Object.entries(PARAMS)){const value=S.params[key];if(!Number.isFinite(value)||value<min||value>max||(['K','steps','group'].includes(key)&&!Number.isInteger(value))){toast(`${label}应在 ${min}–${max} 范围内${['K','steps','group'].includes(key)?'，且为整数':''}`);return;}}
  const task=S.task;$('#run-params').disabled=true;$('#parameter-status').textContent='正在提交计算任务…';
  try{const response=await fetch('/api/rerun',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({任务:task,参数:S.params})});const result=await response.json();if(!response.ok||result.错误)throw Error(result.错误||'任务提交失败');S.jobTask=task;S.srv.作业={状态:'运行中',任务:task};render();pollJob();}catch(e){toast(e.message);if($('#run-params'))$('#run-params').disabled=false;if($('#parameter-status'))$('#parameter-status').textContent=e.message;}
 };
}
async function pollJob(){
 clearTimeout(S.pollTimer);
 try{const response=await fetch('/api/status');if(!response.ok)throw Error('状态接口暂不可用');S.srv=await response.json();const job=S.srv.作业;
  if(job.状态==='运行中'){S.pollTimer=setTimeout(pollJob,2000);return;}
  if(job.状态==='完成'){const task=S.jobTask||job.任务;const result=await fetch(`../samples/${encodeURIComponent(task)}.json?${Date.now()}`);if(!result.ok)throw Error('结果刷新失败');const data=await result.json();validateTask(data);ALL[task]=data;if(S.task===task){D=data;S.params={...data.参数};S.sel=null;render();}toast('计算完成，已更新任务结果。');}
  else if(job.状态==='失败'){toast('计算失败，请在参数页查看服务返回信息。');render();}S.jobTask=null;
 }catch(e){toast('暂时无法刷新计算状态，将自动重试。');S.pollTimer=setTimeout(pollJob,5000);}
}
function download(name,content,type){const objectURL=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=objectURL;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(objectURL),1000);}
function csvCell(value){let s=String(value??'');if(/^[=+@\t\r]/.test(s)||(/^-/.test(s)&&!Number.isFinite(Number(s))))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';}
function exportData(type){
 if(type==='json')download(`${D.id}_完整任务结果.json`,JSON.stringify(D,null,2),'application/json;charset=utf-8');
 else{const rows=[['字段编码','字段名称','类别','角色','初始等级','最终等级','调整方式','影响对象','影响程度','最大敏感度M','初判复核调整','复核理由','说明'],...D.字段.map(f=>[f.字段,f.中文名,f.类别,f.角色,f.一次等级,f.二次等级,upKind(f),f.影响对象,f.影响程度,f.M?Math.max(...f.M):'',f.复核调整?'是':'否',f.复核理由,f.说明])];download(`${D.id}_字段定级台账.csv`,'\ufeff'+rows.map(r=>r.map(csvCell).join(',')).join('\r\n'),'text/csv;charset=utf-8');}
 toast(type==='json'?'已导出完整任务结果。':'已导出字段定级台账。');
}
function openDialog(content){lastFocus=document.activeElement;$('#dialog').innerHTML=content;$('#dialog').showModal();$$('[data-close-dialog]').forEach(e=>e.onclick=()=>$('#dialog').close());}
$('#dialog').addEventListener('close',()=>{if(lastFocus?.isConnected)lastFocus.focus();});
$('#dialog').addEventListener('click',e=>{if(e.target===$('#dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
function guide(){openDialog(`<div class="dialog-head"><h2 id="dialog-title">快速了解这套系统</h2><button class="icon-button" data-close-dialog aria-label="关闭导览">×</button></div><p>系统检查数据在获准共享后，是否会因多个字段组合而泄露权限之外的信息，并将推断风险计入字段等级。</p><div class="method-list">${[['1','先看一个具体风险','在“推断风险”中选择接收方和保护对象，逐步加入字段，观察真实值与推断值。'],['2','理解等级为什么改变','初始定级查看规则与复核依据；字段敏感度查看背景信息如何改变单个字段的贡献；二次定级查看调整依据。'],['3','最后看是否有效','效果复核用两种模型重新训练，展示剩余风险及共享范围变化，并可导出台账。']].map(x=>`<div class="method-item"><span class="method-number">${x[0]}</span><div><strong>${x[1]}</strong><p>${x[2]}</p></div></div>`).join('')}</div><div class="reason"><strong>三个概念</strong><p>候选共享字段：准备提供给接收方的数据。<br>保护对象：希望避免被低权限接收方推断的数据。<br>R² 与 M：前者衡量推断效果，后者衡量某字段带来的最大增益。R² 不是分类准确率，M 也不是泄露概率。</p></div><button class="button primary" id="guide-start">从推断过程开始 ${icon('arrow')}</button>`);$('#guide-start').onclick=()=>{$('#dialog').close();go('risk');};}
// Reject malformed imports before they can replace any visible task.
function validateTask(d){
 const fail=()=>{throw Error('任务结果格式不完整。请导入本系统导出的完整任务 JSON，而非原始数据或普通表格。');};
 const isNum=n=>typeof n==='number'&&Number.isFinite(n),isString=s=>typeof s==='string';
 const arrayKeys=['字段','敏感','候选','接收方','等级表','条文','阶梯','曲线','背景增益','接收方能力','一次定级下的越线','二次定级后的越线','换模型复测','仅凭公开基底可推出'];
 if(!d||typeof d!=='object'||!isString(d.id)||!isString(d.名称)||!isString(d.类别)||!isString(d.数据说明)||!isNum(d.样本数)||!isNum(d.已核对的组合数)||!isNum(d.组合上限)||arrayKeys.some(k=>!Array.isArray(d[k]))||!d.字段.length||!d.敏感.length||!d.背景增益.length||!d.参数||!d.判定表||!d.GRPO)fail();
 if(!d.字段.every(f=>f&&isString(f.字段)&&isString(f.中文名)&&Number.isInteger(f.一次等级)&&f.一次等级>=1&&f.一次等级<=6&&Number.isInteger(f.二次等级)&&f.二次等级>=1&&f.二次等级<=6&&['候选','敏感','公开基底'].includes(f.角色)))fail();
 if(new Set(d.字段.map(f=>f.字段)).size!==d.字段.length||new Set(d.字段.map(f=>f.中文名)).size!==d.字段.length)fail();
 const candidates=d.字段.filter(f=>f.角色==='候选');if(!candidates.length||d.敏感.some(n=>!d.字段.some(f=>f.中文名===n&&f.角色==='敏感'))||candidates.some(f=>!Array.isArray(f.M)||f.M.length!==d.敏感.length||!f.M.every(isNum)))fail();
 if(!d.接收方.length||d.接收方.some(r=>!isString(r.名称)||!isNum(r.级)||!isNum(r.判定线)))fail();
 if(Object.keys(PARAMS).some(k=>!isNum(d.参数[k]))||!Array.isArray(d.GRPO.训练曲线)||!d.GRPO.效用构成||!d.GRPO.只做一次定级||!isNum(d.GRPO.效用))fail();
 if(d.GRPO.训练曲线.some(x=>!['步','组内平均','组内最好'].every(k=>isNum(x[k]))))fail();
 const fields=new Set(d.字段.map(f=>f.中文名));
 if(d.字段.some(f=>f.角色==='公开基底'))fields.add('仅公开基底');
 if(d.阶梯.length!==d.敏感.length||d.曲线.length!==d.敏感.length)fail();
 d.敏感.forEach((n,i)=>{const st=d.阶梯[i],cv=d.曲线[i];if(!st||st.敏感数据!==n||!Array.isArray(st.步骤)||!st.步骤.length||!cv||cv.敏感数据!==n||!Array.isArray(cv.真实)||!cv.真实.every(isNum)||!Array.isArray(cv.还原)||cv.还原.length!==st.步骤.length)fail();st.步骤.forEach((s,j)=>{if(!Array.isArray(s.组合)||s.组合.some(x=>!fields.has(x))||!isNum(s.精度)||!isString(s.加入)||!Array.isArray(cv.还原[j].值)||cv.还原[j].值.length!==cv.真实.length||!cv.还原[j].值.every(isNum))fail();});});
 d.背景增益.forEach(s=>{if(!Number.isInteger(s.K)||!Array.isArray(s.M)||s.M.length!==candidates.length||!Array.isArray(s.见证)||s.见证.length!==candidates.length)fail();s.M.forEach((m,i)=>{if(!Array.isArray(m)||m.length!==d.敏感.length||!m.every(isNum)||!Array.isArray(s.见证[i])||s.见证[i].length!==d.敏感.length||s.见证[i].some(w=>!Array.isArray(w)||!w.every(isString)))fail();});});
 for(const key of ['接收方能力','换模型复测','仅凭公开基底可推出','一次定级下的越线','二次定级后的越线'])d[key].forEach(x=>{if(!x||!d.接收方.some(r=>r.名称===x.接收方)||!d.敏感.includes(x.敏感数据))fail();if(key.includes('越线')&&(!Array.isArray(x.组合)||!x.组合.every(n=>fields.has(n))||!isNum(x.精度)))fail();if(key==='接收方能力'&&!['定级前','定级后','判定线'].every(k=>isNum(x[k])))fail();if(key==='换模型复测'&&!['神经网络','梯度提升树','判定线'].every(k=>isNum(x[k])))fail();});
 for(const k of ['国家安全','经济运行','社会秩序','公共利益','组织权益','个人权益'])if(!d.判定表[k]||!['一般危害','严重危害','特别严重危害'].every(j=>isNum(d.判定表[k][j])))fail();
 d.字段.forEach(f=>{if(f.检索到的条文!==undefined&&(!Array.isArray(f.检索到的条文)||!f.检索到的条文.every(isString)))fail();if(f.依据){if(!Array.isArray(f.依据.重新成立的越线组合)||!isNum(f.依据.重新成立的数量)||f.依据.重新成立的越线组合.some(x=>!Array.isArray(x.组合)||!x.组合.every(isString)||!isNum(x.精度)))fail();}});
}
function importDialog(){
 openDialog(`<div class="dialog-head"><h2 id="dialog-title">导入任务结果</h2><button class="icon-button" data-close-dialog aria-label="关闭导入窗口">×</button></div><p>载入本系统导出的完整结果 JSON，即可查看字段等级、推断路径与效果复核。导入结果仅保留在当前浏览器页面，刷新后需重新导入。</p><div class="file-drop">${icon('folder')}<strong> 选择完整任务结果文件</strong><input type="file" accept=".json,application/json" id="import-file" aria-label="选择任务结果 JSON"><span class="small-text muted">JSON 格式 · 最大 30 MB</span></div><p id="import-message" role="status"></p><p>原始数据上传与新任务训练尚未接入，此入口不执行模型训练。</p>`);
 $('#import-file').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>30*1024*1024)throw Error('文件超过 30 MB，请选择较小的完整任务结果。');const d=JSON.parse(await file.text());validateTask(d);d.id='imported'+Date.now();ALL[d.id]=d;S.page='overview';$('#dialog').close();setTask(d.id);toast('任务结果已载入当前页面。');}catch(err){$('#import-message').textContent=err instanceof SyntaxError?'无法解析 JSON，请检查文件格式。':err.message;$('#import-message').className='red';}};
}
async function boot(){
 $('#brand-mark').innerHTML=icon('shield');$('#help-button').onclick=guide;$('#menu-toggle').onclick=()=>{const open=$('#sidebar').classList.toggle('open');$('#menu-toggle').setAttribute('aria-expanded',String(open));};
 document.addEventListener('click',e=>{if(window.innerWidth<=700&&!e.target.closest('#sidebar,#menu-toggle')){$('#sidebar').classList.remove('open');$('#menu-toggle').setAttribute('aria-expanded','false');}});
 const results=await Promise.allSettled(TASKS.map(async key=>{const r=await fetch(`../samples/${key}.json`);if(!r.ok)throw Error(`${key} 读取失败`);const d=await r.json();validateTask(d);ALL[key]=d;}));
 const failures=results.filter(r=>r.status==='rejected');
 if(!Object.keys(ALL).length){$('#title').textContent='无法载入任务结果';$('#main').innerHTML=notice('算例数据未能加载','请通过项目服务打开此页面，确认 samples 目录中存在完整结果文件。',true)+'<button class="button" id="retry-load">重新加载</button>';$('#retry-load').onclick=()=>location.reload();console.error(failures.map(f=>f.reason.message).join('; '));return;}
 // Keep the task order stable even when fetches complete in a different order.
 ALL=Object.fromEntries(TASKS.filter(k=>ALL[k]).map(k=>[k,ALL[k]]));
 try{const r=await fetch('/api/status');if(r.ok)S.srv=await r.json();}catch(e){/* Static serving still supports all result exploration. */}
 readURL();D=ALL[S.task];S.t=Math.min(S.t,D.敏感.length-1);S.params={...D.参数};S.K=Math.min(D.参数.K,D.背景增益.length-1);render();writeURL();
 if(failures.length){toast(`${failures.length} 个任务未能载入，其余任务可正常查看。`);console.error(failures.map(f=>f.reason.message).join('; '));}
 if(S.srv?.作业?.状态==='运行中'){S.jobTask=S.srv.作业.任务;pollJob();}
 window.addEventListener('popstate',()=>{readURL();D=ALL[S.task];S.params={...D.参数};S.sel=null;S.step=0;S.filter='全部';S.kw='';render();});
}
boot().catch(e=>{console.error(e);$('#main').innerHTML=notice('页面载入失败','请刷新重试，或检查服务与任务结果是否完整。',true);});
