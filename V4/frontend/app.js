/* 数据定级与共享审查系统 · V4 界面。只读取 ../samples/ 下已算好的任务文件；完整方式下可调参数重跑。 */
const TASKS = ["ieee30", "pjm", "community", "insurance"];
const PATHS = {
  shield: "M12 3 3.5 6.5v6c0 5 8.5 9 8.5 9s8.5-4 8.5-9v-6L12 3Z M8.5 12l2.5 2.5 4.5-5", overview: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  layers: "m12 3 10 5-10 5L2 8l10-5Zm-9 10 9 4 9-4M3 18l9 4 9-4", risk: "M3 19h18M5 15l4-5 5 3 6-9M15 4h5v5",
  nodes: "M8 5h8M6 7v10m12-10v10M8 19h8 M4 3h4v4H4z M16 3h4v4h-4z M4 17h4v4H4z M16 17h4v4h-4z M8 7l8 10", tune: "M4 7h16M4 17h16M8 4v6M16 14v6",
  check: "M8 12l3 3 6-7 M20 12v8H4V4h11", folder: "M3 6h7l2 2h9v12H3z M3 6V4h7l2 2", book: "M12 5C8 2 4 3 2 4v16c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-2-10 1Zm0 0v16",
  arrow: "M4 12h16m-6-6 6 6-6 6", download: "M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5", lock: "M6 10V7a6 6 0 0 1 12 0v3M4 10h16v11H4z M12 14v3", play: "m8 4 12 8-12 8Z",
  link: "M10 14a4 4 0 0 0 6 0l3-3a4 4 0 0 0-6-6l-1 1 M14 10a4 4 0 0 0-6 0l-3 3a4 4 0 0 0 6 6l1-1", target: "M12 2v4M12 18v4M2 12h4M18 12h4 M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z" };
const icon = n => `<svg class="icon" viewBox="0 0 24 24"><path d="${PATHS[n]}"/></svg>`;
const PAGES = [
  ["", "tasks", "任务管理", "folder", "选择或新建定级任务"],
  ["", "overview", "总体概览", "overview", "当前任务的定级结果与风险变化"],
  ["定级流程", "grade1", "一次定级", "layers", "依据国家标准，由大语言模型逐字段判定初始等级"],
  ["定级流程", "single", "单字段推断风险", "risk", "每个字段单独能把保护对象推到多准"],
  ["定级流程", "aggr", "聚合推断风险", "nodes", "加入背景字段后推断能力的增加，以及字段推断敏感度"],
  ["定级流程", "regrade", "二次定级", "tune", "把聚合推断计入等级"],
  ["定级流程", "effect", "定级效果", "check", "调级前后的推断风险与核对"]];
const S = { task: "ieee30", page: "overview", t: 0, K: 2, sel: null, filter: "全部", kw: "", recv: 1, gi: 0, guide: null, gtab: 0, P: null, srv: { 完整方式: false, 可重跑: [], 作业: { 状态: "空闲" } } };
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
let D = null, ALL = {}, charts = [];
const LVN = n => n <= 4 ? n + " 级" : n == 5 ? "重要" : "核心", lv = n => `<span class="lv lv${n}">${LVN(n)}</span>`, f2 = x => (+x).toFixed(2), f3 = x => (+x).toFixed(3);
const q = t => `<span class="q" data-tip="${t}">?</span>`;
const C = { blue: "#2563eb", red: "#e5484d", green: "#12a36d", amber: "#e08a1e", ink: "#1a2233", grid: "#eef1f6", gray: "#8c98ad" };
function chart(el, opt) { const c = echarts.init(el); c.setOption(Object.assign({ textStyle: { fontFamily: "Noto Sans CJK SC, Microsoft YaHei, sans-serif" } }, opt)); charts.push(c); return c }
window.addEventListener("resize", () => charts.forEach(c => c.resize()));
const cand = (d = D) => d.字段.filter(f => f.角色 == "候选"), sens = (d = D) => d.字段.filter(f => f.角色 == "敏感"), T = () => sens()[S.t], SH = () => D.展示[T().中文名];
const RECV3 = () => D.接收方.filter(r => r.级 <= 3), rline = c => D.接收方.find(r => r.级 == c).判定线, rname = c => D.接收方.find(r => r.级 == c).名称;
const upKind = f => f.二次等级 <= f.一次等级 ? "" : f.依据 && f.依据.直接定级 ? "直接定级" : f.整体核对上调 ? "整体核对" : "联合评估";
const kindTag = k => k ? `<span class="tag ${k == "直接定级" ? "r" : k == "整体核对" ? "a" : "b"}">${k}</span>` : "";
const capOf = (r, tn) => D.接收方能力.find(x => x.接收方 == r && x.敏感数据 == tn);
const isRes = (r, tn) => (D.仅凭公开基底可推出 || []).some(x => x.接收方 == r && x.敏感数据 == tn);
const overCells = k => D.接收方能力.filter(x => x[k] > x.判定线 && !isRes(x.接收方, x.敏感数据)).length;
const hasBase = () => D.字段.some(f => f.角色 == "公开基底");
const recvTags = l => RECV3().filter(r => r.级 >= l).map(r => `<span class="rtag">${r.名称}</span>`).join("") || '<span class="sub">仅内部</span>';
const kpi = (ic, cls, k, v, d) => `<div class="kpi"><div class="ic ${cls}">${ic}</div><div><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div></div>`;
const TIP = {
  V: "推断精度：用接收方可获取的字段训练预测模型，在未参与训练的数据上的拟合优度 R²。0 为无法推断，1 为完全还原。",
  line: "判定线：推断精度超过该值即视为保护对象可被推出。社会公众 0.7，其他接收方 0.8。",
  combo: "最小越线组合：某类接收方可同时获取、且推断精度超过判定线的字段组合；去掉其中任一字段即不再越线。",
  M: "字段推断敏感度 M：在已有至多 K 个其他字段（背景）的基础上，再获得该字段，推断精度的最大提升。取值 0 至 1。",
  direct: "直接定级：M 不低于直接定级线的字段，定为与被推断数据同级。",
  whole: "整体核对：联合评估之后，对每类接收方可获取的全部字段重新训练（神经网络与梯度提升树取较高）。仍越线时沿“逐个撤出”走完整条路径，取综合效用最高的位置，再逐个尝试放回。",
  grpo: "组相对策略优化：每一步对同一任务采样一组完整的等级方案，以组内相对优势更新策略。综合效用 = 安全收益 + 可用性成本 − 聚合推断惩罚 − 整体推断惩罚，各项为扣分，越接近 0 越好。",
  base: "公开基底：法定公开、所有接收方均已掌握的字段，在推断中始终可见，不参与调级。" };

/* ---------------- 启动与框架 ---------------- */
async function boot() {
  await Promise.all(TASKS.map(async k => { try { ALL[k] = await (await fetch("../samples/" + k + ".json?" + Date.now())).json() } catch (e) { } }));
  try { S.srv = await (await fetch("/api/status")).json() } catch (e) { }
  const P = new URLSearchParams(location.search); ["task", "page"].forEach(k => P.get(k) && (S[k] = P.get(k))); ["t", "K", "sel", "recv", "gi"].forEach(k => P.get(k) != null && (S[k] = +P.get(k)));
  if (P.get("guide")) S.guide = S.page; setTask(S.task, true);
}
function setTask(k, keep) { S.task = k; D = ALL[k]; S.P = Object.assign({}, D.参数); if (!keep) { S.t = 0; S.sel = null; S.gi = 0 } S.t = Math.min(S.t, D.敏感.length - 1); S.K = Math.min(S.K, D.背景增益.length - 1); render() }
function go(p) { S.page = p; S.sel = null; S.gi = 0; render() }
function render() {
  charts.forEach(c => c.dispose()); charts = []; const p = PAGES.find(p => p[1] == S.page), c = cand();
  let h = "", g = null, no = 0;
  PAGES.forEach(x => { if (x[0] != g) { g = x[0]; if (g) h += `<div class="grp"><span>${g}</span></div>` } h += `<a class="${x[1] == S.page ? "on" : ""}" data-p="${x[1]}">${icon(x[3])}<span>${x[2]}</span>${x[0] ? `<b>0${++no}</b>` : ""}</a>` });
  $("#nav").innerHTML = h; $$("#nav a").forEach(a => a.onclick = () => go(a.dataset.p)); $("#logo").innerHTML = icon("shield");
  $("#cur").innerHTML = `<div class="l"><span>当前任务</span><a>切换</a></div><div class="n">${D.名称}</div><div class="m">${D.类别} · ${c.length} 个候选字段 · ${D.敏感.length} 项保护对象</div>`; $("#cur").onclick = () => go("tasks");
  $("#foot").innerHTML = `规则库：GB/T 43697<br>初判模型：${D.大语言模型}<br>${S.srv.完整方式 ? "完整方式 · 可重跑" : "演示方式 · 只读"}`;
  $("#crumb").innerHTML = S.page == "tasks" ? "" : `<b>${D.名称}</b>${p[0] ? " / " + p[0] : ""}`; $("#title").textContent = p[2]; $("#subtitle").textContent = p[4];
  $("#guide").innerHTML = `${icon("book")}导览与参数`; $("#guide").onclick = () => { S.guide = S.page; S.gtab = 0; drawer() };
  ({ tasks: pTasks, overview: pOverview, grade1: pGrade1, single: pSingle, aggr: pAggr, regrade: pRegrade, effect: pEffect })[S.page]();
  drawer();
}
const objBar = (note = "") => `<div class="objbar"><span class="lab">${icon("target")}保护对象</span>${sens().map((f, i) => `<span class="chip ${i == S.t ? "on" : ""}" data-t="${i}">${f.中文名} ${LVN(f.一次等级)}</span>`).join("")}<span class="note">${note || `“${T().中文名}”为 ${LVN(T().一次等级)}，不得被${RECV3().filter(r => r.级 < T().一次等级).map(r => r.名称).join("、") || "—"}推出`}</span></div>`;
const bindObj = () => $$(".chip[data-t]").forEach(a => a.onclick = () => { S.t = +a.dataset.t; S.sel = null; S.gi = 0; render() });

/* ---------------- 导览抽屉：页面说明 + 参数调整 ---------------- */
const GUIDE = {
  tasks: ["选择一个内置任务，或新建任务。每个任务包含一份数据、字段目录（字段名、中文名、类别、公开情况、说明）和若干项保护对象。", []],
  overview: ["一页看完当前任务：五个步骤各自的结果，以及各类接收方对每项保护对象的推断精度在一次定级与二次定级下的变化。", []],
  grade1: ["一次定级只看字段自身：泄露后影响谁（影响对象）、多严重（影响程度），查国标判定表得到等级。<br>影响对象与影响程度由大语言模型依据检索到的国标条文给出初判，再经人工复核；复核改动保留初判与理由。<br>左侧选中一行，右侧显示这一行的判定依据。", []],
  single: ["接收方只拿到一个字段时，能把保护对象推到多准。<br>表中每个候选字段都标出它的一次等级、哪些接收方可以获取、单独的推断精度。点击一行，下方显示该字段的推断值与真实值。<br>最下面是每类接收方把可获取的全部字段合起来的推断精度，这是一次定级下真正的风险。", ["公众判定线", "其他判定线"]],
  aggr: ["同一个字段，在接收方已经掌握其他字段（背景）时，作用可能大得多。<br>对每个字段，取至多 K 个背景字段，比较“只有背景”和“背景加该字段”的推断精度，差值的最大值就是字段推断敏感度 M。<br>M 达到直接定级线的字段，直接定为与保护对象同级。", ["K", "直接定级线"]],
  regrade: ["二次定级分三步：M 达到直接定级线的直接定级；其余字段由组相对策略优化整体确定等级，在安全收益、可用性成本、聚合推断惩罚、整体推断惩罚之间权衡；最后整体核对用重新训练的结果复查。<br>可以按保护对象查看与它相关的字段和调级原因。", ["beta", "lam", "eta", "sigma", "rho", "rho_w", "steps", "group", "严格模式"]],
  effect: ["调级前后，各类接收方合并全部可获取字段的推断精度对比；仍越线的项如实列出。换用梯度提升树复测，以排除只对一种模型成立的结论。", ["rho_w", "严格模式"]] };
const PDEF = { 公众判定线: ["社会公众判定线", 0.05, 0.5, 0.95, TIP.line], 其他判定线: ["其他接收方判定线", 0.05, 0.5, 0.95, TIP.line], K: ["背景字段数上限 K", 1, 0, 2, TIP.M], 直接定级线: ["直接定级线", 0.05, 0.5, 0.95, TIP.direct],
  beta: ["安全收益系数 β", 0.5, 0, 10, "越大越倾向于上调 M 高的字段。"], lam: ["安全收益衰减 λ", 0.1, 0.1, 3, "每上调一级，该字段剩余风险的衰减速度。"], eta: ["可用性成本系数 η", 0.5, 0, 10, "越大越不愿意上调。"], sigma: ["可用性成本增长 σ", 0.1, 0.1, 2, "连续上调多级时成本的增长速度。"],
  rho: ["聚合推断惩罚 ρ", 0.5, 0, 20, "每个仍成立的越线组合扣 ρ × 超出判定线的幅度 ÷ 0.1。"], rho_w: ["整体推断惩罚 ρw", 0.5, 0, 20, "各接收方合并全部字段后超出判定线的部分，每超出 0.1 扣 ρw 分；推断精度来自重新训练。"],
  steps: ["训练步数", 50, 50, 2000, "策略更新的次数。"], group: ["每组方案数", 16, 16, 512, "每一步对同一任务采样的完整等级方案数量。"], 严格模式: ["严格模式", 0, 0, 1, "开启后不允许保留越线，一直调到各接收方不越线。"] };
const canRun = () => S.srv.完整方式 && S.srv.可重跑.includes(S.task), dirty = () => JSON.stringify(S.P) != JSON.stringify(D.参数);
function drawer() {
  if (!S.guide) { $("#drawer").innerHTML = ""; return }
  const [txt, keys] = GUIDE[S.guide], j = S.srv.作业, busy = j.状态 == "运行中";
  const rules = `<h4>等级与接收方</h4><table><tr><th>等级</th><th>可获取的接收方</th><th>判定线</th></tr>${RECV3().map(r => `<tr><td>${[1, 2, 3].filter(l => l <= r.级).map(lv).join(" ")}</td><td>${r.名称}</td><td>${r.判定线}</td></tr>`).join("")}<tr><td>${lv(4)}</td><td>内部受控范围</td><td>—</td></tr><tr><td>${lv(5)} ${lv(6)}</td><td>不对外</td><td>—</td></tr></table>`;
  const body = S.gtab == 0 ? `<p>${txt}</p>${["overview", "grade1", "single"].includes(S.guide) ? rules : ""}` :
    keys.length ? `<div class="box b" style="margin-bottom:12px"><div class="sub">${busy ? `正在重跑“${j.任务}”，完成后自动刷新…` : !canRun() ? "当前为演示方式或该任务没有缓存，参数只读。" : dirty() ? "参数已修改，尚未生效。" : "当前结果即按下列参数计算。重跑只重做二次定级及之后的步骤。"}${j.状态 == "失败" ? ` <span class="red">上次重跑失败</span>` : ""}</div></div>` +
      keys.map(k => { const d = PDEF[k]; return k == "严格模式" ? `<div class="kv"><span>${d[0]} ${q(d[4])}</span><span><label><input type="checkbox" data-k="${k}" ${S.P[k] ? "checked" : ""}> ${S.P[k] ? "开启" : "关闭"}</label></span></div>` :
        `<div class="kv"><span>${d[0]} ${q(d[4])}</span><span><input class="search" style="width:90px;text-align:right" type="number" data-k="${k}" value="${S.P[k]}" step="${d[1]}" min="${d[2]}" max="${d[3]}">${S.P[k] != D.参数[k] ? ' <span class="tag a">已改</span>' : ""}</span></div>` }).join("") +
      `<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:16px"><button class="btn o" id="rst" ${dirty() ? "" : "disabled"}>恢复</button><button class="btn" id="run" ${canRun() && !busy ? "" : "disabled"}>${busy ? "运行中…" : "应用并重跑"}</button></div>` : `<p class="sub">本页没有可调的参数。${S.guide == "grade1" ? "一次定级的规则来自国标判定表。" : ""}</p>`;
  $("#drawer").innerHTML = `<div class="mask" id="dm"></div><div class="dw"><div class="dh"><h3>${PAGES.find(p => p[1] == S.guide)[2]}</h3><span class="x" id="dx">×</span></div><div class="tabs">${["页面说明", "参数调整"].map((n, i) => `<a class="${i == S.gtab ? "on" : ""}" data-gt="${i}">${n}</a>`).join("")}</div><div class="db">${body}</div></div>`;
  $("#dm").onclick = $("#dx").onclick = () => { S.guide = null; drawer() }; $$("[data-gt]").forEach(a => a.onclick = () => { S.gtab = +a.dataset.gt; drawer() });
  $$("[data-k]").forEach(e => { if (!canRun()) e.disabled = true; e.onchange = () => { S.P[e.dataset.k] = e.type == "checkbox" ? e.checked : +e.value; drawer() } });
  if ($("#rst")) { $("#rst").onclick = () => { S.P = Object.assign({}, D.参数); drawer() };
    $("#run").onclick = async () => { const r = await (await fetch("/api/rerun", { method: "POST", body: JSON.stringify({ 任务: S.task, 参数: S.P }) })).json(); if (r.错误) return alert(r.错误); S.srv.作业 = { 状态: "运行中", 任务: S.task }; drawer(); poll() } }
}
function poll() {
  clearInterval(S.pt); S.pt = setInterval(async () => { try { S.srv = await (await fetch("/api/status")).json() } catch (e) { return }
    if (S.srv.作业.状态 != "运行中") { clearInterval(S.pt); if (S.srv.作业.状态 == "完成") { ALL[S.task] = await (await fetch("../samples/" + S.task + ".json?" + Date.now())).json(); setTask(S.task, true) } else drawer() } }, 2000);
}

/* ---------------- 任务管理 ---------------- */
function pTasks() {
  $("#main").innerHTML = `<div class="tcards">${TASKS.filter(k => ALL[k]).map(k => { const d = ALL[k], c = cand(d); return `<div class="tcard ${k == S.task ? "on" : ""}" data-k="${k}"><div style="display:flex;justify-content:space-between"><span class="tag b">${d.类别}</span>${k == S.task ? '<span class="tag g">当前任务</span>' : ""}</div>
    <h3 style="margin-top:8px">${d.名称}</h3><div class="sub">${d.数据说明.slice(0, 70)}…</div><div class="st"><div><b>${d.样本数}</b>样本</div><div><b>${d.字段.length}</b>字段</div><div><b>${d.敏感.length}</b>保护对象</div><div><b>${c.filter(f => f.二次等级 > f.一次等级).length}</b>调高</div></div></div>` }).join("")}
   <div class="tcard new" id="new"><div class="plus">＋</div><div style="margin-top:6px;font-weight:600">新建任务</div><div class="sub">上传数据表与字段目录</div></div></div>`;
  $$(".tcard[data-k]").forEach(a => a.onclick = () => { S.page = "overview"; setTask(a.dataset.k) });
  $("#new").onclick = () => { $("#modal").innerHTML = `<div class="mask"><div class="dlg"><h3>新建定级任务</h3><label>任务名称</label><input placeholder="例如：某业务系统数据定级"><label>数据文件（CSV，每列一个字段）</label><input type="file"><label>字段目录（字段名、中文名、类别、公开情况、说明）</label><input type="file">
     <label>规则库</label><select><option>GB/T 43697 数据安全技术 数据分类分级规则</option></select><p class="sub" style="margin-top:12px">新建任务需在完整方式下运行（需要显卡）：<code>python V4/scripts/build_samples.py</code>。当前界面只能查看内置任务。</p><div class="act"><button class="btn o" id="mc">取消</button><button class="btn" disabled>开始定级</button></div></div></div>`; $("#mc").onclick = () => $("#modal").innerHTML = "" };
}

/* ---------------- 总体概览 ---------------- */
function capMatrix(mode) {
  const rs = RECV3(); return `<table><tr><th>保护对象</th><th>等级</th>${rs.map(r => `<th style="text-align:center">${r.名称}<br><span class="sub">判定线 ${r.判定线}</span></th>`).join("")}</tr>${sens().map((f, i) => `<tr><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td>${rs.map(r => { const x = capOf(r.名称, f.中文名);
    if (!x) return `<td style="text-align:center"><span class="cellv n">有权获取</span></td>`; const o = v => v > x.判定线;
    return `<td style="text-align:center">${mode == "both" ? `<span class="cellv ${o(x.定级前) ? "r" : "g"}">${f2(x.定级前)}</span> <span class="sub">→</span> <span class="cellv ${o(x.定级后) ? "r" : "g"}">${f2(x.定级后)}</span>` : `<span class="cellv ${o(x.定级前) ? "r" : "g"}">${f2(x.定级前)}</span>`}${isRes(r.名称, f.中文名) ? ` ${q("仅凭法定公开的信息即可推出，调整候选字段的等级不起作用。")}` : ""}</td>` }).join("")}</tr>`).join("")}</table>`;
}
function pOverview() {
  const c = cand(), up = c.filter(f => f.二次等级 > f.一次等级), b0 = overCells("定级前"), b1 = overCells("定级后");
  const steps = [["一次定级", `${D.字段.length} 个字段`, "grade1", "layers"], ["单字段推断风险", `${c.filter(f => f.单独精度.some(v => v > .7)).length} 个字段单独超过 0.7`, "single", "risk"], ["聚合推断风险", `${c.filter(f => Math.max(...f.M) >= D.参数.直接定级线).length} 个字段 M 达到直接定级线`, "aggr", "nodes"], ["二次定级", `调高 ${up.length} 个`, "regrade", "tune"], ["定级效果", b1 ? `${b1} 处仍越线` : "无越线", "effect", "check"]];
  $("#main").innerHTML = `<div class="kpis">${kpi("字", "b", "字段", D.字段.length, `候选 ${c.length} · 保护对象 ${D.敏感.length}${hasBase() ? " · 公开基底 " + (D.字段.length - c.length - D.敏感.length) : ""}`)}
   ${kpi("险", "r", "越线的“接收方 × 保护对象” " + q(TIP.V + " " + TIP.line), `<span class="red">${b0}</span> <small>→</small> <span class="${b1 ? "red" : "green"}">${b1}</span>`, "一次定级 → 二次定级")}
   ${kpi("组", "a", "最小越线组合 " + q(TIP.combo), `<span class="red">${D.一次定级下的越线.length}</span> <small>→</small> <span class="green">${D.二次定级后的越线.length}</span>`, `组合规模 ≤ ${D.组合上限}`)}
   ${kpi("调", "b", "调高等级的字段", `${up.length} <small>/ ${c.length}</small>`, `其余 ${c.length - up.length} 个保持原等级`)}</div>
  <div class="pipe">${steps.map((s, i) => `<div class="p" style="cursor:pointer" data-go="${s[2]}"><span class="no">${icon(s[3])}</span><div><div class="a">${i + 1}. ${s[0]}</div><div class="b">${s[1]}</div></div></div>${i < steps.length - 1 ? '<div class="ar">›</div>' : ""}`).join("")}</div>
  <div class="row"><div class="card f2"><h3>各接收方对保护对象的推断精度：一次定级 → 二次定级 ${q(TIP.V)}<span class="r"><span class="legend"><span><i style="background:var(--red2)"></i>超过判定线</span><span><i style="background:var(--green2)"></i>未超过</span></span></span></h3>${capMatrix("both")}</div>
   <div class="card"><h3>候选字段的等级分布</h3><div id="c1" style="height:250px"></div></div></div>
  <div class="card"><h3>任务说明</h3><div class="sub" style="font-size:13px">${D.数据说明}</div></div>`;
  $$("[data-go]").forEach(a => a.onclick = () => go(a.dataset.go));
  const cnt = k => [1, 2, 3, 4].map(l => c.filter(f => f[k] == l).length);
  chart($("#c1"), { grid: { left: 36, right: 12, top: 34, bottom: 28 }, legend: { top: 0, right: 0, itemWidth: 12, itemHeight: 8 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "category", data: ["1 级", "2 级", "3 级", "4 级"], axisTick: { show: false } }, yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: C.grid } } },
    series: [{ name: "一次定级", type: "bar", data: cnt("一次等级"), itemStyle: { color: "#b9c7de", borderRadius: [4, 4, 0, 0] }, barGap: "10%", label: { show: true, position: "top", fontSize: 11, color: "#8a96aa" } }, { name: "二次定级", type: "bar", data: cnt("二次等级"), itemStyle: { color: C.blue, borderRadius: [4, 4, 0, 0] }, label: { show: true, position: "top", fontSize: 11 } }] });
}

/* ---------------- ① 一次定级：左表右依据 ---------------- */
function pGrade1() {
  const all = D.字段, fl = { 全部: f => 1, 候选字段: f => f.角色 == "候选", 保护对象: f => f.角色 == "敏感", 复核调整: f => f.复核调整 }, fs = all.filter(fl[S.filter]).filter(f => !S.kw || (f.中文名 + f.字段).includes(S.kw));
  if (S.sel == null || !fs.includes(all[S.sel])) S.sel = fs.length ? all.indexOf(fs[0]) : 0;
  const f = all[S.sel], rowNo = fs.indexOf(f) + 1, objs = ["国家安全", "经济运行", "社会秩序", "公共利益", "组织权益", "个人权益"], degs = ["一般危害", "严重危害", "特别严重危害"], cl = D.条文.filter(c => f.检索到的条文.includes(c.编号)), nfix = all.filter(x => x.复核调整).length;
  $("#main").innerHTML = `<div class="pipe"><div class="p"><span class="no">${icon("book")}</span><div><div class="a">规则库</div><div class="b">GB/T 43697 · ${D.条文.length} 条条文 · 判定表</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">${icon("nodes")}</span><div><div class="a">大语言模型初判</div><div class="b">${D.大语言模型} · 检索条文后判断影响对象与程度</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">${icon("check")}</span><div><div class="a">人工复核</div><div class="b">${nfix} 个字段调整，保留初判与理由</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">${icon("layers")}</span><div><div class="a">一次等级</div><div class="b">${[1, 2, 3, 4, 5, 6].map(l => [l, all.filter(x => x.一次等级 == l).length]).filter(x => x[1]).map(x => `${LVN(x[0])} ${x[1]}`).join(" · ")}</div></div></div></div>
   <div class="split"><div class="left card"><h3>字段定级结果<span class="r" style="display:flex;gap:10px;align-items:center"><input class="search" id="kw" placeholder="搜索字段" value="${S.kw}"><span class="chips">${Object.keys(fl).map(k => `<span class="chip ${k == S.filter ? "on" : ""}" data-f="${k}">${k} ${all.filter(fl[k]).length}</span>`).join("")}</span></span></h3>
    <div class="scroll" style="max-height:calc(100vh - 290px);overflow-x:visible"><table><tr><th>#</th><th>字段</th><th>角色</th><th>公开情况</th><th>影响对象</th><th>影响程度</th><th>一次等级</th><th>可获取的接收方</th></tr>
    ${fs.map((x, k) => { const i = all.indexOf(x); return `<tr class="c ${i == S.sel ? "pick" : ""}" data-i="${i}"><td class="sub">${k + 1}</td><td><b>${x.中文名}</b> <span class="sub">${x.字段}</span></td><td>${x.角色 == "敏感" ? '<span class="tag r">保护对象</span>' : x.角色 == "公开基底" ? `<span class="tag">公开基底</span>` : "候选"}</td><td>${x.公开情况}</td><td>${x.影响对象}</td><td>${x.影响程度}</td><td>${lv(x.一次等级)} ${x.复核调整 ? '<span class="tag b">复核</span>' : ""}</td><td>${recvTags(x.一次等级)}</td></tr>` }).join("")}</table></div></div>
   <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${rowNo} 行</div><h3 style="font-size:17px">${f.中文名}<span class="r">${f.字段}</span></h3><div class="sub" style="margin-top:-6px">${f.说明}</div>
    <div class="box b" style="margin:12px 0"><div class="kv"><span>判定结果</span><span>${f.影响对象} · ${f.影响程度} → ${lv(f.一次等级)}</span></div><div class="kv"><span>可获取的接收方</span><span>${recvTags(f.一次等级)}</span></div></div>
    <h3>模型初判${f.复核调整 ? " 与复核" : ""}</h3><div class="kv"><span>${D.大语言模型}</span><span>${f.初判.影响对象} · ${f.初判.影响程度} → ${lv(f.初判.等级)}</span></div><div class="sub">${f.初判.理由}</div>
    ${f.复核调整 ? `<div class="kv" style="margin-top:6px"><span><span class="tag b">复核调整</span></span><span>${f.影响对象} · ${f.影响程度} → ${lv(f.一次等级)}</span></div><div class="sub">${f.复核理由}</div>` : ""}
    <h3 style="margin-top:14px">判定表位置</h3><table class="mx"><tr><th></th>${degs.map(d => `<th>${d.replace("危害", "")}</th>`).join("")}</tr>${objs.map(o => `<tr><th style="text-align:right">${o}</th>${degs.map(d => `<td class="${f.影响对象 == o && f.影响程度 == d ? "hit" : ""}">${lv(D.判定表[o][d])}</td>`).join("")}</tr>`).join("")}<tr><th style="text-align:right">无危害</th><td colspan="3" class="${f.影响程度 == "无危害" ? "hit" : ""}">${lv(1)}</td></tr></table>
    <h3 style="margin-top:14px">检索到的国标条文</h3>${cl.map(c => `<div class="kv"><span>${c.编号}</span><span>${c.标题} ${q(c.内容)}</span></div>`).join("")}</div></div>`;
  $$("tr.c").forEach(r => r.onclick = () => { S.sel = +r.dataset.i; render() }); $$("[data-f]").forEach(a => a.onclick = () => { S.filter = a.dataset.f; S.sel = null; render() });
  $("#kw").onchange = e => { S.kw = e.target.value.trim(); S.sel = null; render() };
  const pr = $("tr.pick"); if (pr) pr.scrollIntoView({ block: "nearest" });
}

/* ---------------- ② 单字段推断风险 ---------------- */
const curveOpt = (series, h) => ({ grid: { left: 58, right: 16, top: 30, bottom: 26 }, legend: { top: 0, right: 0 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: SH().真实.map((_, i) => i), name: D.横轴, nameLocation: "middle", nameGap: 8, axisLabel: { show: false }, axisTick: { show: false } }, yAxis: { type: "value", scale: true, splitLine: { lineStyle: { color: C.grid } } },
  series: [{ name: "真实值", type: "line", data: SH().真实, showSymbol: false, lineStyle: { color: C.gray, width: 2 }, itemStyle: { color: C.gray }, z: 2 }].concat(series.map(s => ({ name: s[0], type: D.时间序列 ? "line" : "scatter", data: s[1], showSymbol: !D.时间序列, symbolSize: 4, lineStyle: { color: s[2], width: 1.6 }, itemStyle: { color: s[2], opacity: .8 }, z: 3 }))) });
function relLine(f) { const rs = RECV3().filter(r => f.一次等级 <= r.级 && T().一次等级 > r.级); return rs.length ? Math.min(...rs.map(r => r.判定线)) : null }
function pSingle() {
  const sh = SH(), c = cand(), rows = c.map(f => ({ f, x: sh.单字段.find(s => s.字段 == f.中文名), line: relLine(f) })).sort((a, b) => b.x.精度 - a.x.精度);
  if (S.sel == null || !rows[S.sel]) S.sel = 0; const cur = rows[S.sel], over = rows.filter(r => r.line != null && r.x.精度 > r.line);
  const RA = sh.接收方全部.filter(x => !x.有权获取), ri = Math.max(0, RA.findIndex(x => x.接收方 == rname(S.recv))), rcur = RA[ri];
  $("#main").innerHTML = objBar() + `<div class="kpis">${kpi("单", over.length ? "r" : "g", "单独即可推出的字段", over.length, over.length ? over.slice(0, 3).map(r => r.f.中文名).join("、") : "没有字段单独超过判定线")}
     ${kpi("高", "a", "单字段最高推断精度", f3(rows[0].x.精度), rows[0].f.中文名 + (hasBase() ? "（含公开基底）" : ""))}
     ${kpi("合", RA.some(x => x.精度 > rline(D.接收方.find(r => r.名称 == x.接收方).级)) ? "r" : "g", "合并全部可获取字段后的最高精度", RA.length ? f3(Math.max(...RA.map(x => x.精度))) : "—", "一次定级下，见页面下方")}</div>
   <div class="split"><div class="left card"><h3>每个候选字段单独推断“${T().中文名}” ${q(TIP.V + (hasBase() ? " 本任务的推断都包含公开基底。" + TIP.base : ""))}<span class="r">点击一行查看推断曲线</span></h3>
     <div class="scroll" style="max-height:470px;overflow-x:visible"><table class="list-pick"><tr><th>#</th><th>字段</th><th>一次等级</th><th>可获取的接收方</th><th style="width:30%">单独推断精度</th><th>结论</th></tr>
     ${rows.map((r, k) => `<tr class="c ${k == S.sel ? "pick" : ""}" data-i="${k}"><td class="sub">${k + 1}</td><td><b>${r.f.中文名}</b></td><td>${lv(r.f.一次等级)}</td><td>${recvTags(r.f.一次等级)}</td>
       <td><div class="hbar"><div class="bar"><i style="width:${r.x.精度 * 100}%;background:${r.line != null && r.x.精度 > r.line ? C.red : C.blue}"></i>${r.line != null ? `<b style="left:${r.line * 100}%"></b>` : ""}</div><b class="num">${f3(r.x.精度)}</b></div></td>
       <td>${r.line == null ? '<span class="tag">无越权接收方</span>' : r.x.精度 > r.line ? '<span class="tag r">单独可推出</span>' : '<span class="tag g">单独推不出</span>'}</td></tr>`).join("")}</table></div>
     <div class="sub" style="margin-top:6px">竖线为可获取该字段、但无权获取保护对象的接收方的判定线。</div></div>
    <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${S.sel + 1} 行</div><h3 style="font-size:17px">${cur.f.中文名}<span class="r">${lv(cur.f.一次等级)}</span></h3>
     <div class="box ${cur.line != null && cur.x.精度 > cur.line ? "r" : "b"}"><div class="sub">单独推断“${T().中文名}”的精度</div><div class="big ${cur.line != null && cur.x.精度 > cur.line ? "red" : ""}">${f3(cur.x.精度)}</div><div class="sub">${cur.line == null ? "能获取该字段的接收方都有权获取保护对象" : "判定线 " + cur.line}</div></div>
     <div class="kv" style="margin-top:8px"><span>可获取的接收方</span><span>${recvTags(cur.f.一次等级)}</span></div><div class="kv"><span>说明</span><span class="sub" style="text-align:right;max-width:220px">${cur.f.说明}</span></div></div></div>
   <div class="card"><h3>推断值与真实值：仅凭“${cur.f.中文名}”<span class="r">${D.时间序列 ? "留出数据的前 240 个时段" : "留出数据，按真实值排序"}</span></h3><div id="cv1" style="height:230px"></div></div>
   <div class="card"><h3>合并全部可获取字段：各接收方对“${T().中文名}”的推断 ${q("按一次定级放行时，每类无权获取保护对象的接收方，把可获取的全部字段合起来训练推断模型。精度取神经网络与梯度提升树中较高者；曲线来自神经网络。")}
     <span class="r">${RA.length ? `<span class="seg">${RA.map((x, k) => `<a class="${k == ri ? "on" : ""}" data-r="${D.接收方.find(r => r.名称 == x.接收方).级}">${x.接收方}</a>`).join("")}</span>` : ""}</span></h3>
    ${RA.length ? `<div class="row"><div style="flex:0 0 280px"><table><tr><th>接收方</th><th>字段数</th><th>精度</th></tr>${RA.map(x => { const l = rline(D.接收方.find(r => r.名称 == x.接收方).级); return `<tr><td>${x.接收方}</td><td class="num">${x.可获取字段数}</td><td class="num"><b class="${x.精度 > l ? "red" : "green"}">${f3(x.精度)}</b></td></tr>` }).join("")}</table></div><div style="flex:1"><div id="cv2" style="height:230px"></div></div></div>` : `<div class="empty">所有接收方都有权获取该保护对象</div>`}</div>`;
  bindObj(); $$("tr.c").forEach(r => r.onclick = () => { S.sel = +r.dataset.i; render() }); $$("[data-r]").forEach(a => a.onclick = () => { S.recv = +a.dataset.r; render() });
  chart($("#cv1"), curveOpt([["推断值（" + cur.f.中文名 + "）", cur.x.值, C.red]]));
  if (rcur && rcur.值.length) chart($("#cv2"), curveOpt([[rcur.接收方 + "的推断值", rcur.值, C.red]]));
}

/* ---------------- ③ 聚合推断风险：背景增益与字段敏感度 ---------------- */
function pAggr() {
  const sh = SH(), G = sh.背景增益.slice().sort((a, b) => (Math.max(...b.M) - b.M[0]) - (Math.max(...a.M) - a.M[0]) || Math.max(...b.M) - Math.max(...a.M)), Ks = D.背景增益, Kmax = Ks.length - 1, c = cand(), t = S.t; S.gi = Math.min(S.gi, Math.max(0, G.length - 1)); const g = G[S.gi];
  const combos = D.一次定级下的越线.filter(x => x.敏感数据 == T().中文名), order = c.map((f, i) => i).sort((a, b) => Ks[Kmax].M[b][t] - Ks[Kmax].M[a][t]).slice(0, 14), nK = g ? g.M.length : 0;
  const gainRows = g ? g.M.map((m, k) => `<div class="gainrow"><span class="kk">K = ${k}</span><span class="tx">${g.背景[k].length ? "背景：" + g.背景[k].join("、") : "无背景（单独）"}</span>
     <div class="tr"><i class="bg" style="width:${g.背景精度[k] * 100}%"></i><i class="ad" style="left:${g.背景精度[k] * 100}%;width:${Math.max(0, g.合并精度[k] - g.背景精度[k]) * 100}%"></i><span class="ln" style="left:70%"></span></div>
     <span class="mv">${f2(g.背景精度[k])} → <span class="${g.合并精度[k] > .7 ? "red" : ""}">${f2(g.合并精度[k])}</span></span><span class="mv" style="width:88px">M = <span class="${m >= D.参数.直接定级线 ? "red" : ""}">${f2(m)}</span></span></div>`).join("") : "";
  $("#main").innerHTML = objBar() + `<div class="step3"><div class="s"><div class="k">单独推断（K = 0）</div><div class="v">${g ? f2(g.合并精度[0]) : "—"}</div><div class="sub">${g ? g.字段 : ""}</div></div><div class="ar">›</div>
     <div class="s"><div class="k">背景字段单独的推断（K = ${nK - 1}）</div><div class="v">${g ? f2(g.背景精度[nK - 1]) : "—"}</div><div class="sub">${g && g.背景[nK - 1].length ? g.背景[nK - 1].join("、") : "无"}</div></div><div class="ar">›</div>
     <div class="s"><div class="k">背景 + 该字段</div><div class="v ${g && g.合并精度[nK - 1] > .7 ? "red" : ""}">${g ? f2(g.合并精度[nK - 1]) : "—"}</div><div class="sub">加入后提高 ${g ? f2(g.合并精度[nK - 1] - g.背景精度[nK - 1]) : "—"}</div></div><div class="ar">=</div>
     <div class="s" style="border-top:3px solid ${g && Math.max(...g.M) >= D.参数.直接定级线 ? C.red : C.blue}"><div class="k">字段推断敏感度 M ${q(TIP.M)}</div><div class="v ${g && Math.max(...g.M) >= D.参数.直接定级线 ? "red" : ""}">${g ? f3(Math.max(...g.M)) : "—"}</div><div class="sub">直接定级线 ${D.参数.直接定级线}</div></div></div>
   <div class="split"><div class="left card"><h3>背景字段对“${g ? g.字段 : ""}”的放大作用<span class="r">灰色为只有背景字段时的推断精度，红色为加入该字段后的增加量</span></h3>${gainRows || '<div class="empty">无</div>'}
     <h3 style="margin-top:16px">推断值与真实值：只有背景 vs 背景加“${g ? g.字段 : ""}”</h3><div id="gc" style="height:230px"></div></div>
    <div class="right card"><h3>选择字段<span class="r">按“加背景后的增加量”排序</span></h3><table class="list-pick"><tr><th>字段</th><th>单独</th><th>增加</th><th>M</th></tr>${G.map((x, k) => `<tr class="c ${k == S.gi ? "pick" : ""}" data-g="${k}"><td><b>${x.字段}</b></td><td class="num">${f2(x.M[0])}</td><td class="num"><b class="${Math.max(...x.M) - x.M[0] > .1 ? "red" : ""}">+${f2(Math.max(...x.M) - x.M[0])}</b></td><td class="num"><b class="${Math.max(...x.M) >= D.参数.直接定级线 ? "red" : ""}">${f2(Math.max(...x.M))}</b></td></tr>`).join("")}</table></div></div>
   <div class="row"><div class="card f2"><h3>全部候选字段的推断敏感度<span class="r">拖动 K：接收方已有的背景字段数上限</span></h3><div style="display:flex;gap:16px;align-items:center"><div style="flex:1"><input type="range" id="K" min="0" max="${Kmax}" step="1" value="${S.K}"><div class="kval">${Ks.map(k => `<span>K = ${k.K}</span>`).join("")}</div></div><div class="box b" style="min-width:190px"><div class="sub">达到直接定级线</div><div style="font-size:20px;font-weight:700" id="kd"></div></div></div>
     <div id="gb" style="height:${50 + order.length * 24}px"></div></div>
    <div class="card"><h3>聚合后越线的字段组合 ${q(TIP.combo)}<span class="r">${combos.length} 个</span></h3><div class="scroll" style="max-height:${70 + order.length * 24}px"><table><tr><th>接收方</th><th>字段组合</th><th>精度</th></tr>${combos.slice(0, 80).map(x => `<tr><td>${x.接收方}</td><td>${x.组合.map(n => `<span class="tag">${n}</span>`).join("")}</td><td class="num"><b class="red">${f3(x.精度)}</b></td></tr>`).join("") || `<tr><td colspan="3" class="empty">${isRes("社会公众", T().中文名) ? "仅凭公开基底即可推出，不依赖候选字段的组合" : "没有越线组合"}</td></tr>`}</table></div></div></div>`;
  bindObj(); $$("tr.c[data-g]").forEach(r => r.onclick = () => { S.gi = +r.dataset.g; render() });
  if (g) chart($("#gc"), curveOpt([["只有背景（" + (g.背景[nK - 1].join("、") || "无") + "）", g.曲线.背景.length ? g.曲线.背景 : SH().真实.map(() => null), "#9fb3d4"], ["背景 + " + g.字段, g.曲线.合并, C.red]]));
  const bar = chart($("#gb"), { grid: { left: 150, right: 50, top: 6, bottom: 22 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", inverse: true, data: order.map(i => c[i].中文名), axisTick: { show: false }, axisLabel: { fontSize: 11 } },
    series: [{ type: "bar", data: [], barWidth: 12, label: { show: true, position: "right", fontSize: 11, formatter: p => f2(p.value) }, itemStyle: { borderRadius: [0, 3, 3, 0] }, markLine: { symbol: "none", silent: true, lineStyle: { color: C.red, type: "dashed" }, label: { formatter: "直接定级线", fontSize: 11 }, data: [{ xAxis: D.参数.直接定级线 }] }, animationDurationUpdate: 500 }] });
  const show = K => { S.K = K; const m = Ks[K].M; $("#kd").innerHTML = `${c.filter((_, i) => m[i][t] >= D.参数.直接定级线).length} 个字段`; bar.setOption({ series: [{ data: order.map(i => ({ value: m[i][t], itemStyle: { color: m[i][t] >= D.参数.直接定级线 ? C.red : C.blue } })) }] }) };
  show(S.K); $("#K").oninput = e => show(+e.target.value);
}

/* ---------------- ④ 二次定级：按保护对象 ---------------- */
function pRegrade() {
  const c = cand(), up = c.filter(f => f.二次等级 > f.一次等级), G = D.GRPO, t = S.t, nk = k => up.filter(f => upKind(f) == k).length;
  const gap = G.参照最优 != null ? Math.abs((G.效用 - G.参照最优) / (G.参照最优 || 1)) * 100 : null;
  const list = c.slice().sort((a, b) => ((b.二次等级 > b.一次等级) - (a.二次等级 > a.一次等级)) || b.M[t] - a.M[t]).filter((f, k) => k < 30 || f.二次等级 > f.一次等级);
  if (S.sel == null || !list[S.sel]) S.sel = 0; const cur = list[S.sel], k = upKind(cur), y = cur.依据, w = cur.整体核对上调;
  const combosT = D.一次定级下的越线.filter(x => x.敏感数据 == T().中文名).length, combosT2 = D.二次定级后的越线.filter(x => x.敏感数据 == T().中文名).length;
  const why = !k ? `<div class="empty">等级不变。</div>` : (k == "直接定级" ? `<div class="box r"><b>直接定级</b> ${q(TIP.direct)}<div class="sub">对“${y.对应敏感数据}”的 M = ${f3(Math.max(...cur.M))}，达到直接定级线 ${D.参数.直接定级线}</div></div>` : k == "联合评估" ? `<div class="box b"><b>联合评估上调</b> ${q(TIP.grpo)}<div class="sub">在整套等级方案中权衡后上调；对“${T().中文名}”的 M = ${f3(cur.M[t])}</div></div>` : "") +
    (w ? `<div class="box" style="background:var(--amber2);margin-top:8px"><b>整体核对上调</b> ${q(TIP.whole)}<div class="sub">保持原等级时，${w.接收方}可获取的全部字段对“${w.敏感数据}”的推断精度为 <b class="red">${f3(w.精度)}</b>${w.上调后 != null ? `，上调后 ${f3(w.上调后)}` : ""}</div></div>` : "") +
    (y && y.重新成立的越线组合.length ? `<h3 style="margin-top:14px">若降回 ${LVN(cur.一次等级)}，重新成立的越线组合<span class="r">${y.重新成立的数量} 个</span></h3>` + y.重新成立的越线组合.map(x => `<div class="kv"><span>${x.接收方} → ${x.敏感数据}</span><span>${x.组合.map(n => `<span class="tag">${n}</span>`).join("")} <b class="red num">${f2(x.精度)}</b></span></div>`).join("") : "");
  $("#main").innerHTML = objBar(`与“${T().中文名}”相关：越线组合 ${combosT} → ${combosT2}`) + `<div class="pipe"><div class="p"><span class="no">1</span><div><div class="a">直接定级 ${q(TIP.direct)}</div><div class="b">${nk("直接定级")} 个字段</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">2</span><div><div class="a">联合评估（GRPO） ${q(TIP.grpo)}</div><div class="b">${nk("联合评估")} 个字段上调</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">3</span><div><div class="a">整体核对 ${q(TIP.whole)}</div><div class="b">${nk("整体核对")} 个字段追加上调</div></div></div></div>
   <div class="kpis">${kpi("调", "a", "调高等级的字段", `${up.length} <small>/ ${c.length}</small>`, `直接定级 ${nk("直接定级")} · 联合评估 ${nk("联合评估")} · 整体核对 ${nk("整体核对")}`)}
    ${kpi("组", "g", "越线组合切断比例", `${(G.切断比例 * 100).toFixed(1)}%`, `${D.一次定级下的越线.length} → ${D.二次定级后的越线.length} 个`)}
    ${kpi("效", "b", "综合效用 " + q(TIP.grpo), f2(G.最终效用 ?? G.效用), `只做一次定级 ${f2(G.只做一次定级.效用)}`)}
    ${kpi("优", gap != null && gap < 1 ? "g" : "a", "联合评估与精确最优的差距", gap == null ? "—" : gap.toFixed(1) + "%", G.参照最优 != null ? `精确最优 ${f2(G.参照最优)}（${G.参照最优求法}）` : "未求得参照解")}</div>
   <div class="split"><div class="left card"><h3>字段调整明细<span class="r">按对“${T().中文名}”的 M 排序；已调高的字段在前</span></h3><div class="scroll" style="max-height:470px;overflow-x:visible"><table><tr><th>#</th><th>字段</th><th>一次等级</th><th>二次等级</th><th>调整方式</th><th>对“${T().中文名}”的 M</th></tr>
    ${list.map((f, i) => `<tr class="c ${i == S.sel ? "pick" : ""}" data-i="${i}"><td class="sub">${i + 1}</td><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td><td>${f.二次等级 > f.一次等级 ? lv(f.二次等级) : '<span class="sub">不变</span>'}</td><td>${kindTag(upKind(f))}</td><td class="num"><b class="${f.M[t] >= D.参数.直接定级线 ? "red" : ""}">${f3(f.M[t])}</b></td></tr>`).join("")}</table></div></div>
   <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${S.sel + 1} 行</div><h3 style="font-size:17px">${cur.中文名}<span class="r">${lv(cur.一次等级)} → ${lv(cur.二次等级)}</span></h3>${why}</div></div>
   <div class="row"><div class="card f2"><h3>联合评估的训练过程 ${q(TIP.grpo)}<span class="r">每步采样 ${D.参数.group} 套完整等级方案</span></h3><div id="tc" style="height:220px"></div></div>
    <div class="card"><h3>综合效用的构成</h3><div id="uc" style="height:220px"></div></div></div>`;
  bindObj(); $$("tr.c").forEach(r => r.onclick = () => { S.sel = +r.dataset.i; render() });
  const cu = G.训练曲线; chart($("#tc"), { grid: { left: 56, right: 20, top: 30, bottom: 36 }, legend: { top: 0, right: 0 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: cu.map(x => x.步), name: "训练步", nameLocation: "middle", nameGap: 24 }, yAxis: { type: "value", scale: true, name: "效用", splitLine: { lineStyle: { color: C.grid } } },
    series: [{ name: "组内平均", type: "line", data: cu.map(x => x.组内平均), showSymbol: false, lineStyle: { color: C.blue, width: 2 }, itemStyle: { color: C.blue } }, { name: "组内最好", type: "line", data: cu.map(x => x.组内最好), showSymbol: false, lineStyle: { color: "#9db8ee", width: 1.5 }, itemStyle: { color: "#9db8ee" } }].concat(G.参照最优 != null ? [{ name: "精确最优", type: "line", data: cu.map(() => G.参照最优), showSymbol: false, lineStyle: { color: C.green, type: "dashed", width: 1.5 }, itemStyle: { color: C.green } }] : []) });
  const a = G.只做一次定级.构成, b = G.效用构成, ks = ["安全收益", "可用性成本", "聚合推断惩罚", "整体推断惩罚"].filter(x => x in b), col = ["#7fa2e8", "#e6a532", "#e5484d", "#9b5de5"];
  chart($("#uc"), { grid: { left: 96, right: 30, top: 30, bottom: 24 }, legend: { top: 0, right: 0, itemWidth: 12, itemHeight: 8 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "value", splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", data: ["二次定级", "只做一次定级"], axisTick: { show: false } },
    series: ks.map((x, i) => ({ name: x, type: "bar", stack: "u", data: [b[x], a[x]], itemStyle: { color: col[i] }, barWidth: 26 })) });
}

/* ---------------- ⑤ 定级效果 ---------------- */
function pEffect() {
  const A = D.接收方能力.filter(x => !isRes(x.接收方, x.敏感数据)).slice().reverse(), R = D.换模型复测, res = D.仅凭公开基底可推出 || [], b0 = overCells("定级前"), b1 = overCells("定级后");
  const bad = R.filter(x => Math.max(x.神经网络, x.梯度提升树) > x.判定线 && !isRes(x.接收方, x.敏感数据)), mx = k => A.length ? Math.max(...A.map(x => x[k])) : 0;
  $("#main").innerHTML = `<div class="kpis">${kpi("险", b1 ? "r" : "g", "越线的“接收方 × 保护对象”", `<span class="red">${b0}</span> <small>→</small> <span class="${b1 ? "red" : "green"}">${b1}</span>`, "一次定级 → 二次定级")}
    ${kpi("降", "g", "最高推断精度 " + q(TIP.V), `<span class="red">${f2(mx("定级前"))}</span> <small>→</small> <span class="${mx("定级后") > .7 ? "amber" : "green"}">${f2(mx("定级后"))}</span>`, "各接收方对无权获取的数据")}
    ${kpi("测", bad.length ? "r" : "g", "换模型复测", bad.length ? `${bad.length} 处越线` : "通过", `${R.length} 组，神经网络与梯度提升树`)}
    <div class="kpi"><div class="ic b">${icon("download")}</div><div><div class="k">定级台账</div><button class="btn" id="exp" style="margin-top:4px">导出 CSV</button></div></div></div>
   <div class="row"><div class="card f2"><h3>各接收方合并全部可获取字段的推断精度：调级前 → 调级后<span class="r"><span class="legend"><span><i style="background:#f1b4b4"></i>一次定级</span><span><i style="background:${C.green}"></i>二次定级</span><span><i style="background:${C.ink};width:2px"></i>判定线</span></span></span></h3><div id="wc" style="height:${70 + A.length * 30}px"></div></div>
    <div class="card"><h3>整体核对 ${q(TIP.whole)}</h3>${D.整体核对.length ? `<table><tr><th>接收方</th><th>核对前</th><th>撤出</th><th>放回</th><th>核对后</th></tr>${D.整体核对.map(r => `<tr><td>${r.接收方}</td><td class="num"><b class="${r.核对前推断精度 > rline(D.接收方.find(x => x.名称 == r.接收方).级) ? "red" : ""}">${f3(r.核对前推断精度)}</b></td><td class="num">${r.撤出字段数}</td><td class="num">${r.放回字段数}</td><td class="num"><b class="${r.核对后推断精度 > rline(D.接收方.find(x => x.名称 == r.接收方).级) ? "amber" : "green"}">${f3(r.核对后推断精度)}</b></td></tr>`).join("")}</table>` : `<div class="empty">联合评估后各接收方均未越线，无需追加调整。</div>`}
     <h3 style="margin-top:16px">各接收方可获取的候选字段数</h3><table><tr><th>接收方</th><th>一次定级</th><th>二次定级</th></tr>${RECV3().map(r => `<tr><td>${r.名称}</td><td class="num">${cand().filter(f => f.一次等级 <= r.级).length}</td><td class="num"><b>${cand().filter(f => f.二次等级 <= r.级).length}</b></td></tr>`).join("")}</table>
     ${res.length ? `<div class="box" style="background:var(--amber2);margin-top:12px"><b>调级无法解决的项</b> ${q(TIP.base)}<div class="sub">${[...new Set(res.map(x => x.敏感数据))].join("、")}仅凭法定公开的信息即可推出，需由数据主管方另行评估。</div></div>` : ""}</div></div>
   <div class="card"><h3>换模型复测<span class="r">任一模型超过判定线即视为越线</span></h3><div class="scroll" style="max-height:330px"><table><tr><th>接收方</th><th>保护对象</th><th>调级前（神经网络 / 梯度提升树）</th><th>调级后（神经网络 / 梯度提升树）</th><th>判定线</th><th>结论</th></tr>
     ${R.map(x => { const o = Math.max(x.神经网络, x.梯度提升树) > x.判定线, r = isRes(x.接收方, x.敏感数据); return `<tr><td>${x.接收方}</td><td>${x.敏感数据}</td><td class="num">${x.调级前神经网络 != null ? f3(x.调级前神经网络) + " / " + f3(x.调级前梯度提升树) : "—"}</td><td class="num">${f3(x.神经网络)} / ${f3(x.梯度提升树)}</td><td class="num">${x.判定线}</td><td>${r ? `<span class="tag a">公开基底可推出</span>` : o ? '<span class="tag r">越线</span>' : '<span class="tag g">未越线</span>'}</td></tr>` }).join("")}</table></div></div>`;
  chart($("#wc"), { grid: { left: 200, right: 40, top: 8, bottom: 24 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", data: A.map(x => x.接收方 + " → " + x.敏感数据), axisTick: { show: false }, axisLabel: { fontSize: 11.5 } },
    series: [{ name: "一次定级", type: "bar", data: A.map(x => x.定级前), itemStyle: { color: "#f1b4b4", borderRadius: [0, 3, 3, 0] }, barWidth: 9, label: { show: true, position: "right", fontSize: 10, color: "#c97b7b", formatter: p => f2(p.value) } }, { name: "二次定级", type: "bar", data: A.map(x => ({ value: x.定级后, itemStyle: { color: x.定级后 > x.判定线 ? C.red : C.green } })), itemStyle: { borderRadius: [0, 3, 3, 0] }, barWidth: 9, label: { show: true, position: "right", fontSize: 10, formatter: p => f2(p.value) } }, { name: "判定线", type: "scatter", symbol: "rect", symbolSize: [2, 26], data: A.map(x => x.判定线), itemStyle: { color: C.ink }, z: 5 }] });
  $("#exp").onclick = () => { const rows = [["字段", "中文名", "类别", "角色", "公开情况", "影响对象", "影响程度", "一次等级", "二次等级", "调整方式", "最大M", "复核调整"]].concat(D.字段.map(f => [f.字段, f.中文名, f.类别, f.角色, f.公开情况, f.影响对象, f.影响程度, f.一次等级, f.二次等级, f.角色 == "候选" ? upKind(f) : "", f.M ? Math.max(...f.M) : "", f.复核调整 ? "是" : ""].map(v => `"${String(v).replace(/"/g, '""')}"`)));
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["﻿" + rows.map(r => r.join(",")).join("\n")], { type: "text/csv" })); a.download = D.id + "_定级台账.csv"; a.click() };
}
boot();
