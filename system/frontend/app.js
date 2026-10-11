const TASKS=[["ieee30","电力市场标准算例（行业数据）"],["insurance","医疗保险个人数据（个人信息）"]];
const PAGES=[["总览","任务总览",0],["定级","分类与一次定级",1],["定级","推断验证",1],["定级","字段推断敏感度",1],["定级","二次定级",1],["共享","共享审查与处置",0],["共享","核对与台账",0]];
const S={task:"ieee30",page:2,t:0,step:0,sel:null,timer:null},$=s=>document.querySelector(s);let D=null,charts=[];
const lv=n=>`<span class="lv lv${n}">${n<=4?n+" 级":n==5?"重要":"核心"}</span>`,f2=x=>(+x).toFixed(2);
function chart(el,opt){const c=echarts.init(el);c.setOption(opt);charts.push(c);return c}
window.addEventListener("resize",()=>charts.forEach(c=>c.resize()));
async function load(){D=await (await fetch("../samples/"+S.task+".json")).json();S.t=0;S.step=0;S.sel=null;render()}
function nav(){let h="",g="";PAGES.forEach((p,i)=>{if(p[0]!=g){g=p[0];h+=`<div class="grp">${g=="总览"?"":g+"环节"}</div>`}
 h+=`<a class="${i==S.page?"on":""} ${p[2]?"":"off"}" data-i="${i}"><span class="n">${i+1}</span>${p[1]}${p[2]?"":"<span class='sub'>（待接入）</span>"}</a>`});
 $("#nav").innerHTML=h;document.querySelectorAll("#nav a").forEach(a=>a.onclick=()=>{const i=+a.dataset.i;if(PAGES[i][2]){S.page=i;render()}})}
function render(){clearInterval(S.timer);charts.forEach(c=>c.dispose());charts=[];nav();[null,pGrade1,pInfer,pM,pGrade2][S.page]()}
const cand=()=>D.字段.filter(f=>f.角色=="候选"),sens=()=>D.字段.filter(f=>f.角色=="敏感");

/* ---------- 二、分类与一次定级 ---------- */
function pGrade1(){const fs=D.字段,cur=fs[S.sel??0],objs=["国家安全","经济运行","社会秩序","公共利益","组织权益","个人权益"],degs=["一般危害","严重危害","特别严重危害"];
 const mx=`<table class="mx"><tr><th></th>${degs.map(d=>`<th>${d}</th>`).join("")}</tr>${objs.map(o=>`<tr><th style="text-align:right">${o}</th>${degs.map(d=>`<td class="${cur.影响对象==o&&cur.影响程度==d?"hit":""}">${lv(D.判定表[o][d])}</td>`).join("")}</tr>`).join("")}
 <tr><th style="text-align:right">无危害</th><td colspan="3" class="${cur.影响程度=="无危害"?"hit":""}">${lv(1)}</td></tr></table>`;
 const cl=D.条文.filter(c=>cur.检索到的条文.includes(c.编号));
 $("#main").innerHTML=`<h1>分类与一次定级</h1><p class="lead">逐个字段判断“泄露后影响谁、多严重”，查《${D.规则库.split(" ").slice(1).join(" ")}》的判定表得到初始等级。影响对象和影响程度由大语言模型（${D.大语言模型}）依据检索到的条文给出初判，再经复核确认。</p>
 <div class="row"><div class="card grow2"><h2>字段清单（${fs.length} 个）</h2><table><tr><th>字段</th><th>类别</th><th>公开情况</th><th>影响对象</th><th>影响程度</th><th>一次等级</th><th></th></tr>
 ${fs.map((f,i)=>`<tr class="click ${f==cur?"sel":""}" data-i="${i}"><td><b>${f.中文名}</b></td><td>${f.类别}</td><td>${f.公开情况}</td><td>${f.影响对象}</td><td>${f.影响程度}</td><td>${lv(f.一次等级)}</td><td>${f.复核调整?'<span class="tag b">复核调整</span>':""}${f.角色=="敏感"?'<span class="tag r">敏感数据</span>':""}</td></tr>`).join("")}</table></div>
 <div class="card"><h2>${cur.中文名}：为什么是 ${cur.一次等级<=4?cur.一次等级+" 级":cur.一次等级==5?"重要数据":"核心数据"}</h2><p class="sub">${cur.说明}</p>${mx}
 <p style="margin-top:12px"><span class="tag">模型初判</span>${cur.初判.影响对象} · ${cur.初判.影响程度} → ${lv(cur.初判.等级)}<br><span class="sub">${cur.初判.理由}</span></p>
 ${cur.复核调整?`<p><span class="tag b">复核调整</span>${cur.影响对象} · ${cur.影响程度} → ${lv(cur.一次等级)}<br><span class="sub">${cur.复核理由}</span></p>`:""}
 ${cl.map(c=>`<div class="clause"><b>${c.编号} ${c.标题}</b>　${c.内容}</div>`).join("")}</div></div>`;
 document.querySelectorAll("tr.click").forEach(r=>r.onclick=()=>{S.sel=+r.dataset.i;render()})}

/* ---------- 三、推断验证 ---------- */
function pInfer(){const st=D.阶梯[S.t],cv=D.曲线[S.t],n=st.步骤.length;S.step=Math.min(S.step,n-1);
 $("#main").innerHTML=`<h1>推断验证</h1><p class="lead">替接收方试一遍：用他能拿到的字段训练预测模型，看能把无权获取的数据还原到多准。精度为 0 表示完全推不出，1 表示完全还原；超过判定线即视为可被推出。</p>
 <div class="chips">${D.敏感.map((s,i)=>`<span class="chip ${i==S.t?"on":""}" data-t="${i}">被推断的数据：${s}</span>`).join("")}</div>
 <div class="row"><div class="card grow2"><h2 id="cap"></h2><div class="chips" id="steps"></div><div id="curve" style="height:340px"></div>
 <p class="note">黑线是真实值，红色是接收方还原出来的值（留出数据，未参与训练）。${D.横轴=="时段"?"":"横轴按真实值从小到大排列。"}</p></div>
 <div class="card"><h2>推断精度</h2><div class="big" id="r2"></div><div class="meter"><i id="bar"></i><b style="left:70%"></b><span style="left:70%">判定线 0.7</span></div><p class="sub" id="say"></p>
 <div id="stair" style="height:210px;margin-top:8px"></div></div></div>
 <div class="card"><h2>按一次等级放行时，各类接收方能把无权获取的数据推到多准</h2><table><tr><th>接收方</th><th>被推断的数据</th><th>能拿到的候选字段数</th><th>全部合起来的推断精度</th><th>判定线</th><th>结论</th></tr>
 ${D.接收方能力.map(x=>`<tr><td>${x.接收方}</td><td>${x.敏感数据}</td><td>${x.可见字段数[0]}</td><td><b class="${x.定级前>x.判定线?"red":""}">${f2(x.定级前)}</b></td><td>${x.判定线}</td><td>${x.定级前>x.判定线?'<span class="tag r">越线</span>':'<span class="tag g">未越线</span>'}</td></tr>`).join("")}</table>
 <p class="note">逐字段定级时每个字段单独看都合规，但这张表说明合起来并不安全。共发现 ${D.一次定级下的越线.length} 个最小越线组合，处理见“二次定级”。</p></div>`;
 $("#steps").innerHTML=st.步骤.map((s,i)=>`<span class="chip step" data-s="${i}">${i?"＋ ":""}${s.加入}<span class="sub">（单独 ${f2(s.单独)}）</span></span>`).join("")+`<button class="btn" id="play">▶ 逐步播放</button>`;
 const x=cv.真实.map((_,i)=>i),line=D.横轴=="时段";
 const ch=chart($("#curve"),{animationDuration:500,grid:{left:56,right:16,top:16,bottom:36},tooltip:{trigger:"axis"},xAxis:{type:"category",data:x,name:D.横轴,nameLocation:"middle",nameGap:24,axisLabel:{show:false},axisTick:{show:false}},yAxis:{type:"value",scale:true,splitLine:{lineStyle:{color:"#eef1f5"}}},
  series:[{name:"真实值",type:"line",data:cv.真实,showSymbol:false,lineStyle:{color:"#1b2430",width:2},z:3},{name:"还原值",type:line?"line":"scatter",data:[],showSymbol:!line,symbolSize:5,lineStyle:{color:"#d9483b",width:2},itemStyle:{color:"#d9483b",opacity:.75}}]});
 const sc=chart($("#stair"),{grid:{left:36,right:10,top:20,bottom:50},xAxis:{type:"category",data:st.步骤.map((s,i)=>(i?"＋":"")+s.加入),axisLabel:{interval:0,width:80,overflow:"break"}},yAxis:{type:"value",min:0,max:1,splitLine:{lineStyle:{color:"#eef1f5"}}},
  series:[{type:"bar",barWidth:"46%",data:[],label:{show:true,position:"top",formatter:p=>f2(p.value)},markLine:{symbol:"none",silent:true,lineStyle:{color:"#1b2430",type:"dashed"},label:{formatter:"判定线 0.7",position:"insideEndTop"},data:[{yAxis:.7}]}}]});
 function show(k){S.step=k;const s=st.步骤[k],over=s.精度>.7;document.querySelectorAll(".chip.step").forEach((c,i)=>c.classList.toggle("on",i<=k));
  $("#cap").textContent="接收方拿到："+s.组合.join(" ＋ ");$("#r2").textContent=f2(s.精度);$("#r2").className="big "+(over?"red":"green");
  $("#bar").style.width=s.精度*100+"%";$("#bar").style.background=over?"var(--red)":"var(--green)";
  $("#say").textContent=over?`超过判定线：${st.敏感数据}可以被推出。`:`未到判定线：仅凭这些字段还推不出${st.敏感数据}。`;
  ch.setOption({series:[{},{data:cv.还原[k].值}]});sc.setOption({series:[{data:st.步骤.map((q,i)=>({value:i<=k?q.精度:null,itemStyle:{color:q.精度>.7?"#d9483b":"#9fb3cc",borderRadius:[5,5,0,0]}}))}]})}
 show(S.step);document.querySelectorAll(".chip.step").forEach(c=>c.onclick=()=>{clearInterval(S.timer);show(+c.dataset.s)});
 document.querySelectorAll(".chip[data-t]").forEach(c=>c.onclick=()=>{S.t=+c.dataset.t;S.step=0;render()});
 $("#play").onclick=()=>{clearInterval(S.timer);let k=0;show(0);S.timer=setInterval(()=>{k++;if(k>=n){clearInterval(S.timer);return}show(k)},1600)}}

/* ---------- 四、字段推断敏感度 ---------- */
function pM(){const c=cand(),T=D.敏感,data=[];c.forEach((f,i)=>T.forEach((_,t)=>data.push([t,c.length-1-i,f.M[t]])));const cur=c[S.sel??c.map(f=>Math.max(...f.M)).reduce((b,v,i,a)=>v>a[b]?i:b,0)];
 $("#main").innerHTML=`<h1>字段推断敏感度</h1><p class="lead">把“组合能推多准”落到每个字段头上。字段推断敏感度 M：在接收方已有至多 2 个其他字段的基础上，再拿到这个字段，推断精度最多能提高多少。M 越大，这个字段对推断越关键；达到 0.7 的字段直接与被推断的数据同级。</p>
 <div class="row"><div class="card grow2"><h2>各字段对各项敏感数据的 M（点击一行查看依据）</h2><div id="heat" style="height:${60+c.length*44}px"></div></div>
 <div class="card"><h2>${cur.中文名}</h2>${T.map((s,t)=>`<p><b>对${s}：M = <span class="${cur.M[t]>=.7?"red":""}">${f2(cur.M[t])}</span></b>　${cur.M[t]>=.7?'<span class="tag r">达到直接定级线</span>':""}<br><span class="sub">单独推断 ${f2(cur.单独精度[t])}；${cur.见证[t].length?`在已有“${cur.见证[t].join("、")}”时作用最大`:"单独使用时作用最大"}</span></p>`).join("")}
 <p class="note">M 取各种已有信息下的最大提升，对应国标的“就高从严”；同时记下是哪一个组合，便于复查。</p></div></div>
 <div class="card"><h2>最小越线组合（按一次等级放行时，${D.一次定级下的越线.length} 个）</h2><table><tr><th>接收方</th><th>凑得齐的字段组合</th><th>被推断的数据</th><th>推断精度</th></tr>
 ${D.一次定级下的越线.map(x=>`<tr><td>${x.接收方}</td><td>${x.组合.map(n=>`<span class="tag">${n}</span>`).join(" ")}</td><td>${x.敏感数据}</td><td><b class="red">${f2(x.精度)}</b></td></tr>`).join("")||'<tr><td colspan="4" class="sub">没有</td></tr>'}</table>
 <p class="note">“最小”指去掉其中任何一个字段就不再越线。每个组合都是一条推断路径，二次定级要把它们全部切断。</p></div>`;
 const h=chart($("#heat"),{grid:{left:130,right:30,top:30,bottom:20},tooltip:{formatter:p=>`${c[c.length-1-p.value[1]].中文名} → ${T[p.value[0]]}<br>M = ${f2(p.value[2])}`},xAxis:{type:"category",data:T,position:"top",axisTick:{show:false},axisLine:{show:false}},yAxis:{type:"category",data:c.map(f=>f.中文名).reverse(),axisTick:{show:false},axisLine:{show:false}},
  visualMap:{min:0,max:1,show:false,inRange:{color:["#f3f6fa","#f7d9a8","#e98c4f","#c9392c"]}},series:[{type:"heatmap",data,label:{show:true,formatter:p=>f2(p.value[2])},itemStyle:{borderColor:"#fff",borderWidth:3,borderRadius:6}}]});
 h.on("click",p=>{S.sel=c.length-1-p.value[1];render()})}

/* ---------- 五、二次定级 ---------- */
function pGrade2(){const c=cand(),up=c.filter(f=>f.二次等级>f.一次等级),cur=S.sel!=null&&c[S.sel]?c[S.sel]:(up[0]||c[0]),me=D.对照.find(r=>r.做法=="本系统");
 const why=f=>{if(!f.依据)return`<p class="sub">等级不变。它参与的组合在当前等级方案下都凑不齐或推不过判定线。</p>`;const y=f.依据;
  return(y.直接定级?`<div class="reason"><b>直接定级</b>：对${y.对应敏感数据}的 M 达到 ${f2(Math.max(...f.M))}，基本决定它能否被推出，定为与${y.对应敏感数据}同级。</div>`:`<div class="reason"><b>整体评估</b>：为切断越线组合而上调。</div>`)+
  (y.重新成立的越线组合.length?`<p><b>如果降回 ${f.一次等级} 级，会重新出现 ${y.重新成立的数量} 个越线组合</b>，例如：</p>`+y.重新成立的越线组合.map(x=>`<div class="reason">${x.接收方}用 ${x.组合.map(n=>`<span class="tag">${n}</span>`).join("")} 能把<b>${x.敏感数据}</b>推到 <b class="red">${f2(x.精度)}</b></div>`).join(""):"")};
 $("#main").innerHTML=`<h1>二次定级</h1><p class="lead">把聚合推断算进等级。M 达到 0.7 的字段直接定为与被推断数据同级；其余字段放在一起整体评估，在“切断全部越线组合”和“尽量少调级”之间取最合适的一套等级。每次调级都给出可复查的依据。</p>
 <div class="tiles"><div class="tile"><div class="sub">越线组合</div><div class="v"><span class="red">${D.一次定级下的越线.length}</span><span class="arrow">→</span><span class="green">${D.二次定级后的越线.length}</span></div><div class="sub">一次定级下 → 二次定级后</div></div>
 <div class="tile"><div class="sub">调高等级的字段</div><div class="v">${me.上调字段数}<span class="sub"> / ${c.length} 个</span></div><div class="sub">其余字段保持原等级，照常共享</div></div>
 <div class="tile"><div class="sub">求解方式</div><div style="font-size:15px;margin-top:10px">${D.求解方式}</div></div></div>
 <div class="row"><div class="card grow2"><h2>等级变化（点击字段查看依据）</h2><table><tr><th>字段</th><th>一次等级</th><th></th><th>二次等级</th><th>M（最大）</th><th>处理</th></tr>
 ${c.map((f,i)=>`<tr class="click ${f==cur?"sel":""}" data-i="${i}"><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td><td class="sub">${f.二次等级>f.一次等级?"→":""}</td><td>${f.二次等级>f.一次等级?lv(f.二次等级):'<span class="sub">不变</span>'}</td><td>${f2(Math.max(...f.M))}</td><td>${f.二次等级>f.一次等级?(f.依据.直接定级?'<span class="tag r">直接定级</span>':'<span class="tag b">整体评估上调</span>'):""}</td></tr>`).join("")}</table></div>
 <div class="card"><h2>${cur.中文名}：${cur.二次等级>cur.一次等级?`为什么从 ${cur.一次等级} 级调到 ${cur.二次等级} 级`:"为什么不调"}</h2>${why(cur)}</div></div>
 <div class="row"><div class="card"><h2>调级前后，各类接收方的推断能力</h2><div id="cap2" style="height:${90+D.接收方能力.length*34}px"></div></div>
 <div class="card"><h2>与其他做法比较</h2><table><tr><th>做法</th><th>调高的字段数</th><th>调高的级数合计</th><th>剩余越线组合</th></tr>
 ${D.对照.map(r=>`<tr${r.做法=="本系统"?' class="sel"':""}><td>${r.做法=="本系统"?"<b>本系统</b>":r.做法}</td><td>${r.上调字段数}</td><td>${r.上调级数}</td><td><b class="${r.公众越线组合+r.其他接收方越线组合?"red":"green"}">${r.公众越线组合+r.其他接收方越线组合}</b></td></tr>`).join("")}</table>
 <p class="note">只做逐字段定级：不考虑组合。按单字段相关性上调：单个字段推断精度过线才调。一律上调：凡出现在越线组合里的字段都调到被推断数据的等级。</p></div></div>`;
 document.querySelectorAll("tr.click").forEach(r=>r.onclick=()=>{S.sel=+r.dataset.i;render()});
 const A=D.接收方能力.slice().reverse();chart($("#cap2"),{grid:{left:170,right:40,top:30,bottom:24},legend:{top:0,left:0},tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},xAxis:{type:"value",min:0,max:1,splitLine:{lineStyle:{color:"#eef1f5"}}},yAxis:{type:"category",data:A.map(x=>x.接收方+" → "+x.敏感数据),axisTick:{show:false}},
  series:[{name:"调级前",type:"bar",data:A.map(x=>x.定级前),itemStyle:{color:"#e7a6a0",borderRadius:[0,4,4,0]}},{name:"调级后",type:"bar",data:A.map(x=>x.定级后),itemStyle:{color:"#1f9d6b",borderRadius:[0,4,4,0]},markLine:{symbol:"none",silent:true,lineStyle:{color:"#1b2430",type:"dashed"},label:{formatter:"公众判定线 0.7"},data:[{xAxis:.7}]}}]})}

$("#task").innerHTML=TASKS.map(t=>`<option value="${t[0]}">${t[1]}</option>`).join("");$("#task").onchange=e=>{S.task=e.target.value;load()};
const q=new URLSearchParams(location.search);if(q.get("task"))S.task=q.get("task");if(q.get("page"))S.page=+q.get("page");if(q.get("t"))S.t=+q.get("t");$("#task").value=S.task;
load().then(()=>{if(q.get("t"))S.t=+q.get("t");if(q.get("step")){S.step=+q.get("step")}render()});
