/* 数据定级与共享审查系统 · V5 界面。只读取 ../samples/ 下已算好的任务文件；完整方式下可调参数重跑。 */
const TASKS = ["ieee30", "pjm", "community", "insurance"];
const PATHS = {
  shield: "M12 3 3.5 6.5v6c0 5 8.5 9 8.5 9s8.5-4 8.5-9v-6L12 3Z M8.5 12l2.5 2.5 4.5-5", overview: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  layers: "m12 3 10 5-10 5L2 8l10-5Zm-9 10 9 4 9-4M3 18l9 4 9-4", risk: "M3 19h18M5 15l4-5 5 3 6-9M15 4h5v5",
  nodes: "M8 5h8M6 7v10m12-10v10M8 19h8 M4 3h4v4H4z M16 3h4v4h-4z M4 17h4v4H4z M16 17h4v4h-4z M8 7l8 10", tune: "M4 7h16M4 17h16M8 4v6M16 14v6",
  check: "M8 12l3 3 6-7 M20 12v8H4V4h11", folder: "M3 6h7l2 2h9v12H3z M3 6V4h7l2 2", book: "M12 5C8 2 4 3 2 4v16c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-2-10 1Zm0 0v16",
  download: "M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5", link: "M10 14a4 4 0 0 0 6 0l3-3a4 4 0 0 0-6-6l-1 1 M14 10a4 4 0 0 0-6 0l-3 3a4 4 0 0 0 6 6l1-1",
  target: "M12 2v4M12 18v4M2 12h4M18 12h4 M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z", bot: "M12 3v3 M5 8h14v11H5z M9 13h.01M15 13h.01 M9 16h6", users: "M16 21v-3a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v3M20 8a4 4 0 0 1 0 8m2 5v-3M13 6a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z", plus: "M12 4v16M4 12h16", flask: "M9 3h6M10 3v6L4 19a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2l-6-10V3" };
const icon = n => `<svg class="icon" viewBox="0 0 24 24"><path d="${PATHS[n]}"/></svg>`;
const PAGES = [
  ["", "tasks", "任务管理", "folder", "选择或新建定级任务"],
  ["", "overview", "总体概览", "overview", "当前任务的定级结果与风险变化"],
  ["定级流程", "grade1", "一次定级", "layers", "依据国家标准，由大语言模型逐字段判定初始等级"],
  ["定级流程", "single", "单字段推断风险", "risk", "每个字段单独能把保护对象推到多准"],
  ["定级流程", "aggr", "聚合推断风险", "nodes", "已掌握背景字段时，字段的推断能力会被放大多少"],
  ["定级流程", "regrade", "二次定级", "tune", "把聚合推断计入等级"],
  ["定级流程", "effect", "定级效果", "check", "调级前后，各接收方对保护对象的推断能力"]];
const S = { task: "ieee30", page: "overview", t: 0, K: 2, sel: null, filter: "全部", afilter: "全部", kw: "", guide: null, gtab: 0, P: null, srv: { 完整方式: false, 可重跑: [], 作业: { 状态: "空闲" } } };
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
let D = null, ALL = {}, charts = [];
const LVN = n => n <= 4 ? n + " 级" : n == 5 ? "重要" : "核心", lv = n => `<span class="lv lv${n}">${LVN(n)}</span>`, f2 = x => (+x).toFixed(2), f3 = x => (+x).toFixed(3);
const q = t => `<span class="q" data-tip="${t}">?</span>`;
const C = { blue: "#2563eb", red: "#e5484d", green: "#0f9f6e", amber: "#d97706", ink: "#0f1a2e", grid: "rgba(120,140,175,.18)", gray: "#7c8aa5", lite: "#94a8c8" };
function chart(el, opt) { const c = echarts.init(el); c.setOption(Object.assign({ textStyle: { fontFamily: "Noto Sans CJK SC, Microsoft YaHei, sans-serif", color: "#2a3852" } }, opt)); charts.push(c); return c }
window.addEventListener("resize", () => charts.forEach(c => c.resize()));
const cand = (d = D) => d.字段.filter(f => f.角色 == "候选"), sens = (d = D) => d.字段.filter(f => f.角色 == "敏感"), T = () => sens()[S.t], SH = () => D.展示[T().中文名];
const RECV3 = () => D.接收方.filter(r => r.级 <= 3), rline = c => D.接收方.find(r => r.级 == c).判定线, rlev = n => D.接收方.find(r => r.名称 == n).级;
const rt = (name, c) => `<span class="rt rt${c}">${name}</span>`;
const recvTags = l => RECV3().filter(r => r.级 >= l).map(r => rt(r.名称, r.级)).join("") || rt("仅内部", 4);
const upKind = f => f.二次等级 <= f.一次等级 ? "" : f.依据 && f.依据.直接定级 ? "直接定级" : f.整体核对上调 ? "整体核对" : "联合评估";
const kindTag = k => k ? `<span class="tag ${k == "直接定级" ? "r" : k == "整体核对" ? "a" : "b"}">${k}</span>` : "";
const capOf = (r, tn) => D.接收方能力.find(x => x.接收方 == r && x.敏感数据 == tn);
const isRes = (r, tn) => (D.仅凭公开基底可推出 || []).some(x => x.接收方 == r && x.敏感数据 == tn);
const overCells = k => D.接收方能力.filter(x => x[k] > x.判定线 && !isRes(x.接收方, x.敏感数据)).length;
const hasBase = () => D.字段.some(f => f.角色 == "公开基底");
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
  const P = new URLSearchParams(location.search); ["task", "page"].forEach(k => P.get(k) && (S[k] = P.get(k))); ["t", "K", "sel"].forEach(k => P.get(k) != null && (S[k] = +P.get(k)));
  if (P.get("guide")) S.guide = S.page; if (P.get("modal")) S.modal = P.get("modal"); setTask(S.task, true);
}
function setTask(k, keep) { S.task = k; D = ALL[k]; S.P = Object.assign({}, D.参数); if (!keep) { S.t = 0; S.sel = null } S.t = Math.min(S.t, D.敏感.length - 1); S.K = Math.min(S.K, D.背景增益.length - 1, 2); render(true) }
function go(p) { S.page = p; S.sel = null; render(true) }
function render(top) {
  const keep = top ? null : { y: window.scrollY, s: Object.fromEntries($$("[data-sk]").map(e => [e.dataset.sk, e.scrollTop])) };    // 记住滚动位置，避免点选后跳回顶部
  charts.forEach(c => c.dispose()); charts = []; const p = PAGES.find(p => p[1] == S.page), c = cand();
  let h = "", g = null, no = 0;
  PAGES.forEach(x => { if (x[0] != g) { g = x[0]; if (g) h += `<div class="grp">${g}</div>` } h += `<a class="${x[1] == S.page ? "on" : ""}" data-p="${x[1]}">${icon(x[3])}<span>${x[2]}</span>${x[0] ? `<b>0${++no}</b>` : ""}</a>` });
  $("#nav").innerHTML = h; $$("#nav a").forEach(a => a.onclick = () => go(a.dataset.p)); $("#logo").innerHTML = icon("shield");
  $("#cur").innerHTML = `<div class="l"><span>当前任务</span><a>切换</a></div><div class="n">${D.名称}</div><div class="m">${D.类别} · ${c.length} 个候选字段 · ${D.敏感.length} 项保护对象</div>`; $("#cur").onclick = () => go("tasks");
  $("#foot").innerHTML = `规则库　GB/T 43697<br>初判模型　${D.大语言模型}<br>${S.srv.完整方式 ? "完整方式 · 可重跑" : "演示方式 · 只读"}`;
  $("#crumb").innerHTML = S.page == "tasks" ? "" : `<b>${D.名称}</b>${p[0] ? " / " + p[0] : ""}`; $("#title").textContent = p[2]; $("#subtitle").textContent = p[4];
  $("#guide").innerHTML = `${icon("book")}本页导览与参数`; $("#guide").onclick = () => { S.guide = S.page; S.gtab = 0; drawer() };
  ({ tasks: pTasks, overview: pOverview, grade1: pGrade1, single: pSingle, aggr: pAggr, regrade: pRegrade, effect: pEffect })[S.page]();
  drawer(); modal();
  if (keep) { $$("[data-sk]").forEach(e => { if (keep.s[e.dataset.sk] != null) e.scrollTop = keep.s[e.dataset.sk] }); window.scrollTo(0, keep.y) } else window.scrollTo(0, 0);
}
const objBar = (extra = "") => { const t = T(), no = RECV3().filter(r => r.级 < t.一次等级);
  return `<div class="objbar"><span class="lab">${icon("target")}先选保护对象</span>${sens().map((f, i) => `<span class="ob ${i == S.t ? "on" : ""}" data-t="${i}">${f.中文名} ${lv(f.一次等级)}</span>`).join("")}
   <span class="note">${extra || (no.length ? `不得被 ${no.map(r => rt(r.名称, r.级)).join("")} 推出` : "所有接收方均有权获取")}</span></div>` };
const bindObj = () => $$(".ob[data-t]").forEach(a => a.onclick = () => { S.t = +a.dataset.t; S.sel = null; render() });
const pick = (sel, fn) => $$(sel).forEach(r => r.onclick = () => { fn(r); render() });

/* ---------------- 导览抽屉 ---------------- */
const GUIDE = {
  tasks: { q: "要对哪一份数据定级？", flow: [["folder", "选任务", "四个内置任务"], ["plus", "或新建", "上传数据与字段目录"]], how: ["每个任务有一份数据、一份字段目录和若干项保护对象。", "点卡片切换任务，各页面随之更新。"], terms: [], keys: [] },
  overview: { q: "这份数据定级前后，风险变了多少？", flow: [["layers", "一次定级", "看字段本身"], ["risk", "推断风险", "单字段与聚合"], ["tune", "二次定级", "计入聚合推断"], ["check", "定级效果", "调级前后对比"]],
    how: ["上方四个数字：字段数、越线情形、越线组合、调高的字段数。", "中间五个步骤卡片可点击，直接进入对应页面。", "下方表格是每类接收方对每项保护对象的推断精度，红色为越线，箭头左右分别是一次定级和二次定级。"], terms: [["推断精度", TIP.V], ["判定线", TIP.line]], keys: [] },
  grade1: { q: "每个字段本身该定几级？", flow: [["book", "检索国标条文", "GB/T 43697"], ["bot", "大模型初判", "影响对象与程度"], ["users", "人工复核", "改动留痕"], ["layers", "查判定表", "得到一次等级"]],
    how: ["上方四个步骤卡片可点击，弹窗查看规则库、模型、复核与等级分布的详情。", "左侧大表是全部字段的定级结果；选中一行，右侧面板显示这一行的判定依据。", "接收方标签表示哪些接收方按这个等级可以拿到该字段。"], terms: [["影响对象", "国家安全、经济运行、社会秩序、公共利益、组织权益、个人权益。"], ["影响程度", "无危害、一般危害、严重危害、特别严重危害。"]], keys: [] },
  single: { q: "只拿到一个字段，能把保护对象推到多准？", flow: [["target", "选保护对象", "页面顶部"], ["risk", "逐个字段推断", "单独训练模型"], ["eye", "看推断曲线", "推断值与真实值"]],
    how: ["先在顶部选保护对象。", "表中每一行是一个候选字段：它的等级、谁能拿到、单独推断的精度，竖线是相关接收方的判定线。", "点击一行，右侧显示该字段单独推断的曲线。灰线为真实值，红色为推断值。"], terms: [["推断精度", TIP.V], ["判定线", TIP.line]], keys: ["公众判定线", "其他判定线"] },
  aggr: { q: "已经掌握一些背景字段时，再拿到这个字段会多危险？", flow: [["target", "选保护对象", "页面顶部"], ["nodes", "找最佳背景", "至多 K 个字段"], ["risk", "比较两次推断", "有无该字段"], ["shield", "得到 M", "推断敏感度"]],
    how: ["最上方是全部字段的推断敏感度总览，拖动玻璃滑块改变 K（接收方已有的背景字段数上限）。", "左表每行是一个字段：灰色是单独推断的精度，红色延伸到“有背景时加入该字段”的精度，M 是两者之间的最大提升。", "点击一行，右侧逐级展示在哪些背景下该字段的作用被放大，以及推断曲线。"], terms: [["字段推断敏感度 M", TIP.M], ["直接定级线", TIP.direct], ["越线组合", TIP.combo]], keys: ["K", "直接定级线"] },
  regrade: { q: "为把聚合推断计入等级，要调高哪些字段？", flow: [["shield", "直接定级", "M 达到直接定级线"], ["bot", "联合评估", "强化学习整体权衡"], ["check", "整体核对", "重新训练复查"]],
    how: ["上半部分是与所选保护对象有关的调整：越线组合的变化、相关字段的调级和原因。", "下半部分是整套等级方案：效用和训练过程是所有保护对象共同决定的，切换保护对象时不变。", "左表选中字段，右侧显示调级原因，以及如果降回原级会重新出现哪些越线组合。"], terms: [["综合效用", TIP.grpo], ["整体核对", TIP.whole]], keys: ["beta", "lam", "eta", "sigma", "rho", "rho_w", "steps", "group", "严格模式"] },
  effect: { q: "调级之后，各接收方还能推出这个保护对象吗？", flow: [["target", "选保护对象", "页面顶部"], ["users", "按接收方对比", "调级前后"], ["flask", "换模型复测", "两种模型取高"]],
    how: ["三张接收方卡片：划线数字是一次定级下的推断精度，大数字是二次定级后的，竖线是判定线。", "下方一览表给出全部保护对象的对比；整体核对记录与换模型复测在最后。"], terms: [["推断精度", TIP.V], ["整体核对", TIP.whole], ["公开基底", TIP.base]], keys: ["rho_w", "严格模式"] } };
const PDEF = { 公众判定线: ["社会公众判定线", 0.05, 0.5, 0.95, TIP.line], 其他判定线: ["其他接收方判定线", 0.05, 0.5, 0.95, TIP.line], K: ["背景字段数上限 K", 1, 0, 2, TIP.M], 直接定级线: ["直接定级线", 0.05, 0.5, 0.95, TIP.direct],
  beta: ["安全收益系数 β", 0.5, 0, 10, "越大越倾向于上调 M 高的字段。"], lam: ["安全收益衰减 λ", 0.1, 0.1, 3, "每上调一级，该字段剩余风险的衰减速度。"], eta: ["可用性成本系数 η", 0.5, 0, 10, "越大越不愿意上调。"], sigma: ["可用性成本增长 σ", 0.1, 0.1, 2, "连续上调多级时成本的增长速度。"],
  rho: ["聚合推断惩罚 ρ", 0.5, 0, 20, "每个仍成立的越线组合扣 ρ × 超出判定线的幅度 ÷ 0.1。"], rho_w: ["整体推断惩罚 ρw", 0.5, 0, 20, "各接收方合并全部字段后超出判定线的部分，每超出 0.1 扣 ρw 分；推断精度来自重新训练。"],
  steps: ["训练步数", 50, 50, 2000, "策略更新的次数。"], group: ["每组方案数", 16, 16, 512, "每一步对同一任务采样的完整等级方案数量。"], 严格模式: ["严格模式", 0, 0, 1, "开启后不允许保留越线，一直调到各接收方不越线。"] };
const canRun = () => S.srv.完整方式 && S.srv.可重跑.includes(S.task), dirty = () => JSON.stringify(S.P) != JSON.stringify(D.参数);
function drawer() {
  if (!S.guide) { $("#drawer").innerHTML = ""; return }
  const G = GUIDE[S.guide], pg = PAGES.find(p => p[1] == S.guide), j = S.srv.作业, busy = j.状态 == "运行中";
  const intro = `<div class="qcard"><div class="k">本页回答</div><div class="t">${G.q}</div></div>
    <h4>${icon("nodes")}流程</h4><div class="flow">${G.flow.map((f, i) => `${i ? '<div class="ar">›</div>' : ""}<div class="n">${icon(f[0])}<b>${f[1]}</b>${f[2]}</div>`).join("")}</div>
    <h4>${icon("eye")}怎么读这一页</h4><div class="how">${G.how.map((x, i) => `<span class="i">${i + 1}</span><span>${x}</span>`).join("")}</div>
    ${G.terms.length ? `<h4>${icon("book")}术语</h4><div class="terms">${G.terms.map(x => `<div class="term"><b>${x[0]}</b>${x[1]}</div>`).join("")}</div>` : ""}
    ${["overview", "grade1"].includes(S.guide) ? `<h4>${icon("users")}等级与接收方</h4><table><tr><th>接收方</th><th>可获取的等级</th><th>判定线</th></tr>${RECV3().map(r => `<tr><td>${rt(r.名称, r.级)}</td><td>${[1, 2, 3].filter(l => l <= r.级).map(lv).join(" ")}</td><td class="num">${r.判定线}</td></tr>`).join("")}<tr><td>${rt("内部受控范围", 4)}</td><td>${[1, 2, 3, 4].map(lv).join(" ")}</td><td>—</td></tr></table>` : ""}`;
  const params = G.keys.length ? `<div class="box ${busy ? "a" : ""}" style="margin-bottom:12px"><span class="sub">${busy ? `正在重跑“${j.任务}”，完成后自动刷新…` : !canRun() ? "当前为演示方式或该任务没有缓存，参数只读。" : dirty() ? "参数已修改，尚未生效。" : "当前结果即按下列参数计算。重跑只重做二次定级及之后的步骤。"}</span>${j.状态 == "失败" ? ` <span class="red">上次重跑失败</span>` : ""}</div>` +
    G.keys.map(k => { const d = PDEF[k]; return k == "严格模式" ? `<div class="kv"><span>${d[0]} ${q(d[4])}</span><span><label><input type="checkbox" data-k="${k}" ${S.P[k] ? "checked" : ""}> ${S.P[k] ? "开启" : "关闭"}</label></span></div>` :
      `<div class="kv"><span>${d[0]} ${q(d[4])}</span><span><input class="search" style="width:96px;text-align:right" type="number" data-k="${k}" value="${S.P[k]}" step="${d[1]}" min="${d[2]}" max="${d[3]}">${S.P[k] != D.参数[k] ? ' <span class="tag a">已改</span>' : ""}</span></div>` }).join("") +
    `<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:16px"><button class="btn o" id="rst" ${dirty() ? "" : "disabled"}>恢复</button><button class="btn" id="run" ${canRun() && !busy ? "" : "disabled"}>${busy ? "运行中…" : "应用并重跑"}</button></div>` : `<div class="empty">本页没有可调的参数。${S.guide == "grade1" ? "一次定级的规则来自国标判定表。" : ""}</div>`;
  $("#drawer").innerHTML = `<div class="mask" id="dm" style="background:rgba(15,26,46,.18)"></div><div class="dw"><div class="dh"><span class="no">${icon(pg[3])}</span><div><h3>${pg[2]}</h3><div class="sub">${pg[4]}</div></div><span class="x" id="dx">×</span></div>
    <div class="tabs">${["页面说明", "参数调整"].map((n, i) => `<a class="${i == S.gtab ? "on" : ""}" data-gt="${i}">${n}</a>`).join("")}</div><div class="db">${S.gtab == 0 ? intro : params}</div></div>`;
  $("#dm").onclick = $("#dx").onclick = () => { S.guide = null; drawer() }; $$("[data-gt]").forEach(a => a.onclick = () => { S.gtab = +a.dataset.gt; drawer() });
  $$("[data-k]").forEach(e => { if (!canRun()) e.disabled = true; e.onchange = () => { S.P[e.dataset.k] = e.type == "checkbox" ? e.checked : +e.value; drawer() } });
  if ($("#rst")) { $("#rst").onclick = () => { S.P = Object.assign({}, D.参数); drawer() };
    $("#run").onclick = async () => { const r = await (await fetch("/api/rerun", { method: "POST", body: JSON.stringify({ 任务: S.task, 参数: S.P }) })).json(); if (r.错误) return alert(r.错误); S.srv.作业 = { 状态: "运行中", 任务: S.task }; drawer(); poll() } }
}
function poll() {
  clearInterval(S.pt); S.pt = setInterval(async () => { try { S.srv = await (await fetch("/api/status")).json() } catch (e) { return }
    if (S.srv.作业.状态 != "运行中") { clearInterval(S.pt); if (S.srv.作业.状态 == "完成") { ALL[S.task] = await (await fetch("../samples/" + S.task + ".json?" + Date.now())).json(); setTask(S.task, true) } else drawer() } }, 2000);
}

/* ---------------- 弹窗（一次定级的四个步骤） ---------------- */
function modal() {
  if (!S.modal) { $("#modal").innerHTML = ""; return }
  const all = D.字段, objs = ["国家安全", "经济运行", "社会秩序", "公共利益", "组织权益", "个人权益"], degs = ["一般危害", "严重危害", "特别严重危害"], cnt = (k, arr) => arr.map(v => [v, all.filter(f => f.初判[k] == v).length]).filter(x => x[1]);
  const matrix = `<table class="mx"><tr><th></th>${degs.map(d => `<th>${d}</th>`).join("")}</tr>${objs.map(o => `<tr><th style="text-align:right">${o}</th>${degs.map(d => `<td>${lv(D.判定表[o][d])}</td>`).join("")}</tr>`).join("")}<tr><th style="text-align:right">无危害</th><td colspan="3">${lv(1)}</td></tr></table>`;
  const ex = all[S.sel ?? 0] || all[0], fix = all.filter(f => f.复核调整);
  const body = {
    rules: [icon("book"), "规则库：GB/T 43697《数据安全技术 数据分类分级规则》", `<div class="row" style="margin-top:12px"><div><h4>判定表（影响对象 × 影响程度）</h4>${matrix}<p class="sub">国标第 6 章表 1 给出核心、重要、一般三档；一般数据按附录 H.1 细分为 1 至 4 级。</p></div>
      <div><h4>等级与共享范围</h4><table>${D.等级表.map(l => `<tr><td>${lv(l.级)}</td><td>${l.共享范围}</td></tr>`).join("")}</table></div></div>
      <h4>入库的条文（${D.条文.length} 条）</h4><table><tr><th>编号</th><th>标题</th><th>内容</th></tr>${D.条文.map(c => `<tr><td class="num"><b>${c.编号}</b></td><td>${c.标题}</td><td class="sub" style="font-size:12.5px">${c.内容}</td></tr>`).join("")}</table>`],
    llm: [icon("bot"), `大语言模型初判：${D.大语言模型}`, `<div class="row" style="margin-top:12px"><div class="box"><div class="sub">判定字段</div><div class="big">${all.length}</div><div class="sub">每个字段调用一次，结果缓存，不重复调用</div></div>
      <div class="box"><div class="sub">检索方式</div><b>按字符二元组重合度取最相关的 4 条条文</b><div class="sub">判定表（6.5 表 1）必定入选</div></div><div class="box"><div class="sub">输出</div><b>影响对象、影响程度、个人信息类型、依据条文、理由</b><div class="sub">温度 0，结构化输出</div></div></div>
      <h4>提示词要点</h4><div class="box" style="font-size:12.5px;line-height:1.8">依据《数据安全技术 数据分类分级规则》判断：该数据一旦泄露，最主要的影响对象和影响程度。影响对象只能取六类之一，影响程度只能取四档之一；已对外公开发布的数据，影响程度取“无危害”；若属于个人信息，另外判断是敏感个人信息还是一般个人信息。输出依据条文编号和不超过 60 字的理由。</div>
      <div class="row"><div><h4>初判的影响对象分布</h4>${cnt("影响对象", objs).map(x => `<div class="kv"><span>${x[0]}</span><span class="num">${x[1]}</span></div>`).join("")}</div><div><h4>初判的影响程度分布</h4>${cnt("影响程度", ["无危害", ...degs]).map(x => `<div class="kv"><span>${x[0]}</span><span class="num">${x[1]}</span></div>`).join("")}</div></div>
      <h4>示例：${ex.中文名}</h4><div class="box"><div class="kv"><span>检索到的条文</span><span>${ex.检索到的条文.join("、")}</span></div><div class="kv"><span>初判</span><span>${ex.初判.影响对象} · ${ex.初判.影响程度} → ${lv(ex.初判.等级)}</span></div><div class="sub">${ex.初判.理由}</div></div>`],
    review: [icon("users"), `人工复核：调整 ${fix.length} 个字段`, `<p class="sub">复核时逐条检查模型初判，与复核判断不一致的以复核为准，初判与理由都保留。</p>${fix.length ? `<table><tr><th>字段</th><th>模型初判</th><th>复核结果</th><th>理由</th></tr>${fix.map(f => `<tr><td><b>${f.中文名}</b></td><td>${f.初判.影响对象} · ${f.初判.影响程度} → ${lv(f.初判.等级)}</td><td>${f.影响对象} · ${f.影响程度} → ${lv(f.一次等级)}</td><td class="sub" style="font-size:12.5px">${f.复核理由}</td></tr>`).join("")}</table>` : `<div class="empty">本任务没有复核调整。</div>`}`],
    levels: [icon("layers"), "一次等级分布", `<div id="mlv" style="height:260px;margin-top:8px"></div><table>${[1, 2, 3, 4, 5, 6].map(l => [l, all.filter(f => f.一次等级 == l)]).filter(x => x[1].length).map(x => `<tr><td>${lv(x[0])}</td><td class="num"><b>${x[1].length}</b></td><td>${recvTags(x[0])}</td><td class="sub" style="font-size:12.5px">${x[1].slice(0, 6).map(f => f.中文名).join("、")}${x[1].length > 6 ? " 等" : ""}</td></tr>`).join("")}</table>`] }[S.modal];
  $("#modal").innerHTML = `<div class="mask" id="mm"><div class="dlg" onclick="event.stopPropagation()"><h2><span class="pipe"><span class="no">${body[0]}</span></span>${body[1]}<span class="x" id="mx">×</span></h2>${body[2]}</div></div>`;
  $("#mm").onclick = $("#mx").onclick = () => { S.modal = null; modal() };
  if (S.modal == "levels") { const ls = [1, 2, 3, 4, 5, 6].filter(l => all.some(f => f.一次等级 == l)), col = ["", "#16a34a", "#2563eb", "#d97706", "#ea580c", "#dc2626", "#7f1d1d"];
    chart($("#mlv"), { tooltip: {}, grid: { left: 40, right: 20, top: 20, bottom: 30 }, xAxis: { type: "category", data: ls.map(LVN) }, yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: C.grid } } }, series: [{ type: "bar", barWidth: 38, data: ls.map(l => ({ value: all.filter(f => f.一次等级 == l).length, itemStyle: { color: col[l], borderRadius: [6, 6, 0, 0] } })), label: { show: true, position: "top" } }] }) }
}

/* ---------------- 任务管理 ---------------- */
function pTasks() {
  $("#main").innerHTML = `<div class="tcards">${TASKS.filter(k => ALL[k]).map(k => { const d = ALL[k], c = cand(d); return `<div class="tcard ${k == S.task ? "on" : ""}" data-k="${k}"><div style="display:flex;justify-content:space-between"><span class="tag b">${d.类别}</span>${k == S.task ? '<span class="tag g">当前任务</span>' : ""}</div>
    <h3>${d.名称}</h3><div class="sub">${d.数据说明.slice(0, 70)}…</div><div class="st"><div><b>${d.样本数}</b>样本</div><div><b>${d.字段.length}</b>字段</div><div><b>${d.敏感.length}</b>保护对象</div><div><b>${c.filter(f => f.二次等级 > f.一次等级).length}</b>调高</div></div></div>` }).join("")}
   <div class="tcard new" id="new"><div class="plus">＋</div><div style="margin-top:6px;font-weight:650">新建任务</div><div class="sub">上传数据表与字段目录</div></div></div>`;
  $$(".tcard[data-k]").forEach(a => a.onclick = () => { S.page = "overview"; setTask(a.dataset.k) });
  $("#new").onclick = () => { $("#modal").innerHTML = `<div class="mask"><div class="dlg" style="width:560px"><h2>新建定级任务</h2><label>任务名称</label><input placeholder="例如：某业务系统数据定级"><label>数据文件（CSV，每列一个字段）</label><input type="file"><label>字段目录（字段名、中文名、类别、公开情况、说明）</label><input type="file">
     <label>规则库</label><select><option>GB/T 43697 数据安全技术 数据分类分级规则</option></select><p class="sub" style="margin-top:12px">从数据文件直接完成全流程的后端尚在开发；目前新建任务需在服务器上运行 <code>python V5/scripts/build_samples.py</code>。</p><div class="act"><button class="btn o" id="mc">取消</button><button class="btn" disabled>开始定级</button></div></div></div>`; $("#mc").onclick = () => $("#modal").innerHTML = "" };
}

/* ---------------- 总体概览 ---------------- */
function capMatrix() {
  const rs = RECV3(); return `<table><tr><th>保护对象</th><th>等级</th>${rs.map(r => `<th style="text-align:center">${rt(r.名称, r.级)}<div class="sub">判定线 ${r.判定线}</div></th>`).join("")}</tr>${sens().map(f => `<tr><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td>${rs.map(r => { const x = capOf(r.名称, f.中文名);
    if (!x) return `<td style="text-align:center"><span class="cellv n">有权获取</span></td>`; const o = v => v > x.判定线;
    return `<td style="text-align:center"><span class="cellv ${o(x.定级前) ? "r" : "g"}">${f2(x.定级前)}</span> <span class="sub">→</span> <span class="cellv ${o(x.定级后) ? "r" : "g"}">${f2(x.定级后)}</span>${isRes(r.名称, f.中文名) ? ` ${q("仅凭法定公开的信息即可推出，调整候选字段的等级不起作用。")}` : ""}</td>` }).join("")}</tr>`).join("")}</table>`;
}
function pOverview() {
  const c = cand(), up = c.filter(f => f.二次等级 > f.一次等级), b0 = overCells("定级前"), b1 = overCells("定级后");
  const steps = [["一次定级", `${D.字段.length} 个字段`, "grade1", "layers"], ["单字段推断风险", `${c.filter(f => f.单独精度.some(v => v > .7)).length} 个字段单独超过 0.7`, "single", "risk"], ["聚合推断风险", `${c.filter(f => Math.max(...f.M) >= D.参数.直接定级线).length} 个字段达到直接定级线`, "aggr", "nodes"], ["二次定级", `调高 ${up.length} 个字段`, "regrade", "tune"], ["定级效果", b1 ? `${b1} 处仍越线` : "无越线", "effect", "check"]];
  $("#main").innerHTML = `<div class="kpis">${kpi(icon("layers"), "b", "字段", D.字段.length, `候选 ${c.length} · 保护对象 ${D.敏感.length}${hasBase() ? " · 公开基底 " + (D.字段.length - c.length - D.敏感.length) : ""}`)}
   ${kpi(icon("risk"), "r", "越线的“接收方 × 保护对象” " + q(TIP.V + " " + TIP.line), `<span class="red">${b0}</span> <small>→</small> <span class="${b1 ? "red" : "green"}">${b1}</span>`, "一次定级 → 二次定级")}
   ${kpi(icon("nodes"), "a", "最小越线组合 " + q(TIP.combo), `<span class="red">${D.一次定级下的越线.length}</span> <small>→</small> <span class="green">${D.二次定级后的越线.length}</span>`, `组合规模 ≤ ${D.组合上限}`)}
   ${kpi(icon("tune"), "g", "调高等级的字段", `${up.length} <small>/ ${c.length}</small>`, `其余 ${c.length - up.length} 个保持原等级`)}</div>
  <div class="pipe">${steps.map((s, i) => `${i ? '<div class="ar">›</div>' : ""}<div class="p" data-go="${s[2]}"><span class="no">${icon(s[3])}</span><div><div class="a">${i + 1}. ${s[0]}</div><div class="b">${s[1]}</div></div></div>`).join("")}</div>
  <div class="row"><div class="card f2"><h3>${icon("users")}各接收方对保护对象的推断精度：一次定级 → 二次定级 ${q(TIP.V)}<span class="r"><span class="legend"><span><i style="background:rgba(229,72,77,.3)"></i>超过判定线</span><span><i style="background:rgba(15,159,110,.3)"></i>未超过</span></span></span></h3>${capMatrix()}</div>
   <div class="card"><h3>${icon("layers")}候选字段的等级分布</h3><div id="c1" style="height:260px"></div></div></div>
  <div class="card"><h3>${icon("book")}任务说明</h3><div style="font-size:13.5px;color:var(--ink2)">${D.数据说明}</div></div>`;
  $$("[data-go]").forEach(a => a.onclick = () => go(a.dataset.go));
  const cnt = k => [1, 2, 3, 4].map(l => c.filter(f => f[k] == l).length);
  chart($("#c1"), { grid: { left: 36, right: 12, top: 34, bottom: 28 }, legend: { top: 0, right: 0, itemWidth: 12, itemHeight: 8 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "category", data: ["1 级", "2 级", "3 级", "4 级"], axisTick: { show: false } }, yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: C.grid } } },
    series: [{ name: "一次定级", type: "bar", data: cnt("一次等级"), itemStyle: { color: "#b6c5df", borderRadius: [6, 6, 0, 0] }, barGap: "12%", label: { show: true, position: "top", fontSize: 11, color: C.gray } }, { name: "二次定级", type: "bar", data: cnt("二次等级"), itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "#60a5fa" }, { offset: 1, color: "#2563eb" }]), borderRadius: [6, 6, 0, 0] }, label: { show: true, position: "top", fontSize: 11, fontWeight: 700 } }] });
}

/* ---------------- ① 一次定级 ---------------- */
function pGrade1() {
  const all = D.字段, fl = { 全部: f => 1, 候选字段: f => f.角色 == "候选", 保护对象: f => f.角色 == "敏感", 复核调整: f => f.复核调整 }, fs = all.filter(fl[S.filter]).filter(f => !S.kw || (f.中文名 + f.字段).includes(S.kw));
  if (S.sel == null || !fs.includes(all[S.sel])) S.sel = fs.length ? all.indexOf(fs[0]) : 0;
  const f = all[S.sel], rowNo = fs.indexOf(f) + 1, objs = ["国家安全", "经济运行", "社会秩序", "公共利益", "组织权益", "个人权益"], degs = ["一般危害", "严重危害", "特别严重危害"], cl = D.条文.filter(c => f.检索到的条文.includes(c.编号)), nfix = all.filter(x => x.复核调整).length;
  const role = x => x.角色 == "敏感" ? '<span class="tag r">保护对象</span>' : x.角色 == "公开基底" ? `<span class="tag v">公开基底</span>` : '<span class="tag b">候选字段</span>';
  const open = x => x == "已公开" ? '<span class="tag g">已公开</span>' : x == "有条件开放" ? '<span class="tag a">有条件开放</span>' : '<span class="tag">未公开</span>';
  $("#main").innerHTML = `<div class="pipe">${[["rules", "book", "规则库", `GB/T 43697 · ${D.条文.length} 条条文 · 判定表`], ["llm", "bot", "大语言模型初判", `${D.大语言模型} · 检索条文后判断`], ["review", "users", "人工复核", `${nfix} 个字段调整，保留初判与理由`], ["levels", "layers", "一次等级", [1, 2, 3, 4, 5, 6].map(l => [l, all.filter(x => x.一次等级 == l).length]).filter(x => x[1]).map(x => `${LVN(x[0])} ${x[1]}`).join(" · ")]]
     .map((s, i) => `${i ? '<div class="ar">›</div>' : ""}<div class="p" data-m="${s[0]}"><span class="no">${icon(s[1])}</span><div><div class="a">${s[2]}</div><div class="b">${s[3]}</div></div><span class="go">详情 ›</span></div>`).join("")}</div>
   <div class="split"><div class="left card"><h3>${icon("layers")}字段定级结果<span class="r" style="display:flex;gap:10px;align-items:center"><input class="search" id="kw" placeholder="搜索字段" value="${S.kw}"><span class="chips">${Object.keys(fl).map(k => `<span class="chip ${k == S.filter ? "on" : ""}" data-f="${k}">${k} ${all.filter(fl[k]).length}</span>`).join("")}</span></span></h3>
    <div class="scroll" data-sk="g1" style="max-height:calc(100vh - 300px)"><table><tr><th>#</th><th>字段</th><th>角色</th><th>公开情况</th><th>影响对象</th><th>影响程度</th><th>一次等级</th><th>可获取的接收方</th></tr>
    ${fs.map((x, k) => { const i = all.indexOf(x); return `<tr class="c ${i == S.sel ? "pick" : ""}" data-i="${i}"><td class="sub">${k + 1}</td><td><b>${x.中文名}</b> <span class="sub">${x.字段}</span></td><td>${role(x)}</td><td>${open(x.公开情况)}</td><td>${x.影响对象}</td><td>${x.影响程度}</td><td>${lv(x.一次等级)} ${x.复核调整 ? '<span class="tag b">复核</span>' : ""}</td><td>${recvTags(x.一次等级)}</td></tr>` }).join("")}</table></div></div>
   <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${rowNo} 行</div><h3 style="font-size:18px">${f.中文名}<span class="r">${f.字段}</span></h3><div style="font-size:13px;color:var(--ink2);margin-top:-6px">${f.说明}</div>
    <div class="box" style="margin:12px 0"><div class="kv"><span>判定结果</span><span>${f.影响对象} · ${f.影响程度} → ${lv(f.一次等级)}</span></div><div class="kv"><span>可获取的接收方</span><span>${recvTags(f.一次等级)}</span></div></div>
    <h3>${icon("bot")}模型初判${f.复核调整 ? " 与复核" : ""}</h3><div class="kv"><span>${D.大语言模型}</span><span>${f.初判.影响对象} · ${f.初判.影响程度} → ${lv(f.初判.等级)}</span></div><div class="sub">${f.初判.理由}</div>
    ${f.复核调整 ? `<div class="box a" style="margin-top:8px"><div class="kv"><span><span class="tag a">复核调整</span></span><span>${f.影响对象} · ${f.影响程度} → ${lv(f.一次等级)}</span></div><div class="sub">${f.复核理由}</div></div>` : ""}
    <h3 style="margin-top:14px">${icon("overview")}判定表位置</h3><table class="mx"><tr><th></th>${degs.map(d => `<th>${d.replace("危害", "")}</th>`).join("")}</tr>${objs.map(o => `<tr><th style="text-align:right">${o}</th>${degs.map(d => `<td class="${f.影响对象 == o && f.影响程度 == d ? "hit" : ""}">${lv(D.判定表[o][d])}</td>`).join("")}</tr>`).join("")}<tr><th style="text-align:right">无危害</th><td colspan="3" class="${f.影响程度 == "无危害" ? "hit" : ""}">${lv(1)}</td></tr></table>
    <h3 style="margin-top:14px">${icon("book")}检索到的国标条文</h3>${cl.map(c => `<div class="kv"><span>${c.编号}</span><span>${c.标题} ${q(c.内容)}</span></div>`).join("")}</div></div>`;
  pick("tr.c", r => S.sel = +r.dataset.i); $$("[data-f]").forEach(a => a.onclick = () => { S.filter = a.dataset.f; S.sel = null; render() });
  $$("[data-m]").forEach(a => a.onclick = () => { S.modal = a.dataset.m; modal() }); $("#kw").onchange = e => { S.kw = e.target.value.trim(); S.sel = null; render() };
}

/* ---------------- ② 单字段推断风险 ---------------- */
const curveOpt = series => ({ grid: { left: 58, right: 14, top: 34, bottom: 24 }, legend: { top: 0, right: 0, textStyle: { fontSize: 11 } }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: SH().真实.map((_, i) => i), name: D.横轴, nameLocation: "middle", nameGap: 8, axisLabel: { show: false }, axisTick: { show: false }, axisLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "value", scale: true, splitLine: { lineStyle: { color: C.grid } } },
  series: [{ name: "真实值", type: "line", data: SH().真实, showSymbol: false, lineStyle: { color: C.gray, width: 2 }, itemStyle: { color: C.gray }, z: 2 }].concat(series.map(s => ({ name: s[0], type: D.时间序列 ? "line" : "scatter", data: s[1], showSymbol: !D.时间序列, symbolSize: 4, lineStyle: { color: s[2], width: 1.6 }, itemStyle: { color: s[2], opacity: .85 }, z: 3 }))) });
function relLine(f) { const rs = RECV3().filter(r => f.一次等级 <= r.级 && T().一次等级 > r.级); return rs.length ? Math.min(...rs.map(r => r.判定线)) : null }
function pSingle() {
  const sh = SH(), rows = cand().map(f => ({ f, x: sh.单字段.find(s => s.字段 == f.中文名), line: relLine(f) })).sort((a, b) => b.x.精度 - a.x.精度);
  if (S.sel == null || !rows[S.sel]) S.sel = 0; const cur = rows[S.sel], over = rows.filter(r => r.line != null && r.x.精度 > r.line), curOver = cur.line != null && cur.x.精度 > cur.line;
  $("#main").innerHTML = objBar() + `<div class="kpis">${kpi(icon("risk"), over.length ? "r" : "g", "单独即可推出的字段", over.length, over.length ? over.slice(0, 3).map(r => r.f.中文名).join("、") : "没有字段单独超过判定线")}
     ${kpi(icon("target"), "a", "单字段最高推断精度", f3(rows[0].x.精度), rows[0].f.中文名 + (hasBase() ? "（含公开基底）" : ""))}
     ${kpi(icon("layers"), "b", "参与推断的候选字段", rows.length, `其中 ${rows.filter(r => r.line == null).length} 个只有有权接收方能拿到`)}</div>
   <div class="split"><div class="left card"><h3>${icon("risk")}每个候选字段单独推断“${T().中文名}” ${q(TIP.V + (hasBase() ? " 本任务的推断都包含公开基底。" + TIP.base : ""))}<span class="r">点击一行查看推断曲线</span></h3>
     <div class="scroll" data-sk="s1" style="max-height:calc(100vh - 340px)"><table><tr><th>#</th><th>字段</th><th>一次等级</th><th>可获取的接收方</th><th style="width:30%">单独推断精度</th><th>结论</th></tr>
     ${rows.map((r, k) => `<tr class="c ${k == S.sel ? "pick" : ""}" data-i="${k}"><td class="sub">${k + 1}</td><td><b>${r.f.中文名}</b></td><td>${lv(r.f.一次等级)}</td><td>${recvTags(r.f.一次等级)}</td>
       <td><div class="hbar"><div class="bar"><i style="width:${r.x.精度 * 100}%;background:${r.line != null && r.x.精度 > r.line ? "linear-gradient(90deg,#f87171,#e5484d)" : "linear-gradient(90deg,#60a5fa,#2563eb)"}"></i>${r.line != null ? `<b style="left:${r.line * 100}%"></b>` : ""}</div><b class="num">${f3(r.x.精度)}</b></div></td>
       <td>${r.line == null ? '<span class="tag">无越权接收方</span>' : r.x.精度 > r.line ? '<span class="tag r">单独可推出</span>' : '<span class="tag g">单独推不出</span>'}</td></tr>`).join("")}</table></div>
     <div class="legend" style="margin-top:8px"><span><i style="background:#2563eb"></i>未超过判定线</span><span><i style="background:#e5484d"></i>超过判定线</span><span><i style="background:#0f1a2e;width:2px"></i>可获取该字段、但无权获取保护对象的接收方的判定线</span></div></div>
    <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${S.sel + 1} 行</div><h3 style="font-size:18px">${cur.f.中文名}<span class="r">${lv(cur.f.一次等级)}</span></h3>
     <div class="row"><div class="box ${curOver ? "r" : "g"}"><div class="sub">单独推断“${T().中文名}”</div><div class="big ${curOver ? "red" : "green"}">${f3(cur.x.精度)}</div><div class="sub">${cur.line == null ? "能拿到该字段的接收方都有权获取保护对象" : "判定线 " + cur.line + (curOver ? "，已超过" : "，未超过")}</div></div></div>
     <div class="kv" style="margin-top:8px"><span>可获取的接收方</span><span>${recvTags(cur.f.一次等级)}</span></div>
     <h3 style="margin-top:12px">${icon("eye")}推断值与真实值</h3><div id="cv1" style="height:250px"></div><div class="sub">${D.时间序列 ? "留出数据的前 240 个时段" : "留出数据，按真实值从小到大排列"}${hasBase() ? "；推断时含公开基底" : ""}</div></div></div>`;
  bindObj(); pick("tr.c", r => S.sel = +r.dataset.i);
  chart($("#cv1"), curveOpt([["仅凭“" + cur.f.中文名 + "”的推断值", cur.x.值, C.red]]));
}

/* ---------------- ③ 聚合推断风险 ---------------- */
function glassSlider(id, max, val) { return `<div class="glass-slider"><input type="range" id="${id}" min="0" max="${max}" step="1" value="${val}" style="--p:${max ? val / max * 100 : 0}%"><div class="ticks">${Array.from({ length: max + 1 }, (_, k) => `<span data-kt="${k}" class="${k == val ? "on" : ""}">K = ${k}${k == 0 ? "（单独）" : ""}</span>`).join("")}</div></div>` }
function pAggr() {
  const sh = SH(), det = sh.背景明细 || [], nK = det.length ? det[0].M.length : 1; S.K = Math.min(S.K, nK - 1); const K = S.K, DL = D.参数.直接定级线;
  const rows0 = cand().map(f => ({ f, d: det.find(x => x.字段 == f.中文名) })).filter(r => r.d), amp = r => r.d.M[K] - r.d.M[0];
  const fl = { 全部: r => 1, 背景放大: r => amp(r) > 0.05, 达到直接定级线: r => r.d.M[K] >= DL };
  const rows = rows0.filter(fl[S.afilter] || fl.全部).sort((a, b) => b.d.M[K] - a.d.M[K]);
  if (S.sel == null || !rows[S.sel]) S.sel = 0; const cur = rows[S.sel] || rows0[0], cd = cur.d, gcur = sh.背景增益.find(x => x.字段 == cur.f.中文名);
  const combos = D.一次定级下的越线.filter(x => x.敏感数据 == T().中文名 && x.组合.includes(cur.f.中文名));
  const ov = rows0.slice().sort((a, b) => b.d.M[nK - 1] - a.d.M[nK - 1]).slice(0, 14);
  $("#main").innerHTML = objBar() + `<div class="card"><h3>${icon("nodes")}全部候选字段的推断敏感度总览 ${q(TIP.M)}<span class="r">拖动滑块：接收方已掌握的背景字段数上限 K</span></h3>
     <div style="display:flex;gap:20px;align-items:center"><div style="flex:1">${glassSlider("K", nK - 1, K)}</div><div class="kbox"><div class="sub">达到直接定级线 ${DL}</div><div class="v"><span id="kd"></span> 个字段</div><div class="sub" id="ka"></div></div></div>
     <div id="gb" style="height:${40 + ov.length * 24}px;margin-top:6px"></div><div class="legend"><span><i style="background:#94a8c8"></i>K = 0（单独）</span><span><i style="background:#2563eb"></i>当前 K 的 M</span><span><i style="background:#e5484d"></i>达到直接定级线</span></div></div>
   <div class="split"><div class="left card"><h3>${icon("risk")}考虑背景后的字段推断能力（K = ${K}）<span class="r"><span class="chips">${Object.keys(fl).map(k => `<span class="chip ${k == S.afilter ? "on" : ""}" data-af="${k}">${k} ${rows0.filter(fl[k]).length}</span>`).join("")}</span></span></h3>
     <div class="scroll" data-sk="a1" style="max-height:calc(100vh - 260px)"><table><tr><th>#</th><th>字段</th><th>一次等级</th><th>可获取的接收方</th><th style="width:30%">单独 → 有背景时加入该字段</th><th>M</th><th>结论</th></tr>
     ${rows.map((r, k) => { const s = r.d.合并精度[0], e = r.d.合并精度[K], m = r.d.M[K]; return `<tr class="c ${k == S.sel ? "pick" : ""}" data-i="${k}"><td class="sub">${k + 1}</td><td><b>${r.f.中文名}</b></td><td>${lv(r.f.一次等级)}</td><td>${recvTags(r.f.一次等级)}</td>
       <td><div class="hbar"><div class="bar2"><i class="s" style="width:${s * 100}%"></i>${e > s ? `<i class="e" style="left:${s * 100}%;width:${(e - s) * 100}%"></i>` : ""}<b style="left:70%"></b></div><span class="num" style="width:92px;text-align:right">${f2(s)} → <b class="${e > .7 ? "red" : ""}">${f2(e)}</b></span></div></td>
       <td class="num"><b class="${m >= DL ? "red" : ""}">${f3(m)}</b></td><td>${m >= DL ? '<span class="tag r">直接定级</span>' : amp(r) > 0.05 ? '<span class="tag a">背景放大</span>' : '<span class="tag">作用有限</span>'}</td></tr>` }).join("") || `<tr><td colspan="7" class="empty">没有符合条件的字段</td></tr>`}</table></div>
     <div class="legend" style="margin-top:8px"><span><i style="background:#94a8c8"></i>单独推断</span><span><i style="background:#e5484d"></i>有背景时加入该字段后的增加</span><span><i style="background:#0f1a2e;width:2px"></i>0.7</span></div></div>
    <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${S.sel + 1} 行</div><h3 style="font-size:18px">${cur.f.中文名}<span class="r">M = <b class="${Math.max(...cd.M) >= DL ? "red" : "blue"}" style="font-size:18px">&nbsp;${f3(cd.M[K])}</b></span></h3>
     <div class="sub" style="margin-top:-6px;margin-bottom:6px">在哪些背景下，它对“${T().中文名}”的推断作用被放大</div>
     ${cd.M.map((m, k) => `<div class="gainrow" style="${k == K ? "background:rgba(37,99,235,.06);border-radius:10px;padding-left:6px" : ""}"><span class="kk">K=${k}</span><span class="tx">${cd.背景[k].length ? cd.背景[k].map(x => `<span class="tag">${x}</span>`).join("") : '<span class="sub">无背景（单独）</span>'}</span>
       <div class="bar2"><i class="s" style="width:${cd.背景精度[k] * 100}%"></i><i class="e" style="left:${cd.背景精度[k] * 100}%;width:${Math.max(0, cd.合并精度[k] - cd.背景精度[k]) * 100}%"></i><b style="left:70%"></b></div>
       <span class="mv">${f2(cd.背景精度[k])} → <span class="${cd.合并精度[k] > .7 ? "red" : ""}">${f2(cd.合并精度[k])}</span></span></div>`).join("")}
     <div class="legend" style="margin:6px 0 4px"><span><i style="background:#94a8c8"></i>只有背景</span><span><i style="background:#e5484d"></i>加入该字段后的增加（即 M）</span></div>
     <h3 style="margin-top:12px">${icon("eye")}推断值与真实值</h3>${gcur ? `<div id="gc" style="height:230px"></div>` : `<div class="empty">这个字段的推断曲线没有导出（只为每项保护对象中 M 最大或放大最明显的若干字段导出曲线）。</div>`}
     ${combos.length ? `<h3 style="margin-top:12px">${icon("nodes")}含该字段的越线组合<span class="r">${combos.length} 个</span></h3>${combos.slice(0, 6).map(x => `<div class="kv"><span>${rt(x.接收方, rlev(x.接收方))}</span><span>${x.组合.map(n => `<span class="tag ${n == cur.f.中文名 ? "b" : ""}">${n}</span>`).join("")} <b class="red num">${f3(x.精度)}</b></span></div>`).join("")}` : ""}</div></div>`;
  bindObj(); pick("tr.c", r => S.sel = +r.dataset.i); $$("[data-af]").forEach(a => a.onclick = () => { S.afilter = a.dataset.af; S.sel = null; render() });
  if (gcur) { const k2 = gcur.M.length - 1; chart($("#gc"), curveOpt([["只有背景（" + (gcur.背景[k2].join("、") || "无") + "）", gcur.曲线.背景.length ? gcur.曲线.背景 : SH().真实.map(() => null), C.lite], ["背景 + " + gcur.字段, gcur.曲线.合并, C.red]])) }
  const bar = chart($("#gb"), { grid: { left: 150, right: 50, top: 4, bottom: 20 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", inverse: true, data: ov.map(r => r.f.中文名), axisTick: { show: false }, axisLine: { show: false }, axisLabel: { fontSize: 12, color: "#2a3852" } },
    series: [{ name: "当前 K", type: "bar", data: [], barWidth: 13, z: 1, label: { show: true, position: "right", fontSize: 11, fontWeight: 700, formatter: p => f2(p.value) }, itemStyle: { borderRadius: [0, 6, 6, 0] }, markLine: { symbol: "none", silent: true, lineStyle: { color: C.red, type: "dashed" }, label: { formatter: "直接定级线", fontSize: 11 }, data: [{ xAxis: DL }] }, animationDurationUpdate: 450 },
      { name: "K = 0", type: "bar", barGap: "-100%", data: ov.map(r => r.d.M[0]), barWidth: 5, z: 2, silent: true, itemStyle: { color: "#94a8c8", borderRadius: [0, 3, 3, 0] } }] });
  const upd = k => { const el = $("#K"); el.style.setProperty("--p", (nK > 1 ? k / (nK - 1) * 100 : 0) + "%"); $$("[data-kt]").forEach(s => s.classList.toggle("on", +s.dataset.kt == k));
    $("#kd").textContent = rows0.filter(r => r.d.M[k] >= DL).length; $("#ka").textContent = `背景放大超过 0.05 的字段 ${rows0.filter(r => r.d.M[k] - r.d.M[0] > .05).length} 个`;
    bar.setOption({ series: [{ data: ov.map(r => ({ value: r.d.M[k], itemStyle: { color: r.d.M[k] >= DL ? new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: "#f87171" }, { offset: 1, color: "#e5484d" }]) : new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: "#93c5fd" }, { offset: 1, color: "#2563eb" }]) } })) }] }) };
  upd(K); $("#K").oninput = e => upd(+e.target.value); $("#K").onchange = e => { S.K = +e.target.value; render() }; $$("[data-kt]").forEach(s => s.onclick = () => { S.K = +s.dataset.kt; render() });
}

/* ---------------- ④ 二次定级 ---------------- */
function pRegrade() {
  const c = cand(), up = c.filter(f => f.二次等级 > f.一次等级), G = D.GRPO, t = S.t, tn = T().中文名, nk = k => up.filter(f => upKind(f) == k).length;
  const gap = G.参照最优 != null ? Math.abs((G.效用 - G.参照最优) / (G.参照最优 || 1)) * 100 : null;
  const list = c.slice().sort((a, b) => ((b.二次等级 > b.一次等级) - (a.二次等级 > a.一次等级)) || b.M[t] - a.M[t]).filter((f, k) => k < 30 || f.二次等级 > f.一次等级);
  if (S.sel == null || !list[S.sel]) S.sel = 0; const cur = list[S.sel], k = upKind(cur), y = cur.依据, w = cur.整体核对上调;
  const c0 = D.一次定级下的越线.filter(x => x.敏感数据 == tn).length, c1 = D.二次定级后的越线.filter(x => x.敏感数据 == tn).length, caps = D.接收方能力.filter(x => x.敏感数据 == tn && !isRes(x.接收方, tn));
  const related = up.filter(f => f.M[t] >= 0.05).length;
  const why = !k ? `<div class="empty">等级不变。</div>` : (k == "直接定级" ? `<div class="box r"><b>直接定级</b> ${q(TIP.direct)}<div class="sub">对“${y.对应敏感数据}”的 M = ${f3(cur.M[D.敏感.indexOf(y.对应敏感数据)])}，达到直接定级线 ${D.参数.直接定级线}</div></div>` : k == "联合评估" ? `<div class="box" style="background:rgba(37,99,235,.08)"><b>联合评估上调</b> ${q(TIP.grpo)}<div class="sub">强化学习在整套等级方案中权衡后上调；对“${tn}”的 M = ${f3(cur.M[t])}</div></div>` : "") +
    (w ? `<div class="box a" style="margin-top:8px"><b>整体核对上调</b> ${q(TIP.whole)}<div class="sub">保持原等级时，${rt(w.接收方, rlev(w.接收方))}可获取的全部字段对“${w.敏感数据}”的推断精度为 <b class="red">${f3(w.精度)}</b>${w.上调后 != null ? `，上调后 ${f3(w.上调后)}` : ""}</div></div>` : "") +
    (y && y.重新成立的越线组合.length ? `<h3 style="margin-top:14px">若降回 ${LVN(cur.一次等级)}，重新成立的越线组合<span class="r">${y.重新成立的数量} 个</span></h3>` + y.重新成立的越线组合.map(x => `<div class="kv"><span>${rt(x.接收方, rlev(x.接收方))} → ${x.敏感数据}</span><span>${x.组合.map(n => `<span class="tag ${n == cur.中文名 ? "b" : ""}">${n}</span>`).join("")} <b class="red num">${f2(x.精度)}</b></span></div>`).join("") : "");
  $("#main").innerHTML = objBar(`与“${tn}”相关：越线组合 <b class="red">${c0}</b> → <b class="green">${c1}</b>`) +
   `<div class="kpis">${kpi(icon("nodes"), "a", `涉及“${tn}”的越线组合`, `<span class="red">${c0}</span> <small>→</small> <span class="${c1 ? "amber" : "green"}">${c1}</span>`, "一次定级 → 二次定级")}
    ${kpi(icon("risk"), "r", `各接收方对“${tn}”的最高推断精度`, caps.length ? `<span class="red">${f2(Math.max(...caps.map(x => x.定级前)))}</span> <small>→</small> <span class="${Math.max(...caps.map(x => x.定级后 - x.判定线)) > 0 ? "amber" : "green"}">${f2(Math.max(...caps.map(x => x.定级后)))}</span>` : "—", "合并全部可获取字段，两种模型取较高")}
    ${kpi(icon("tune"), "b", "与它有关的调高字段", related, `对“${tn}”的 M ≥ 0.05 且被调高`)}</div>
   <div class="split"><div class="left card"><h3>${icon("tune")}字段调整明细<span class="r">按对“${tn}”的 M 排序；已调高的在前</span></h3><div class="scroll" data-sk="r1" style="max-height:calc(100vh - 330px)"><table><tr><th>#</th><th>字段</th><th>一次等级</th><th>二次等级</th><th>调整方式</th><th>对“${tn}”的 M</th></tr>
    ${list.map((f, i) => `<tr class="c ${i == S.sel ? "pick" : ""}" data-i="${i}"><td class="sub">${i + 1}</td><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td><td>${f.二次等级 > f.一次等级 ? lv(f.二次等级) : '<span class="sub">不变</span>'}</td><td>${kindTag(upKind(f))}</td><td class="num"><b class="${f.M[t] >= D.参数.直接定级线 ? "red" : ""}">${f3(f.M[t])}</b></td></tr>`).join("")}</table></div></div>
   <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${S.sel + 1} 行</div><h3 style="font-size:18px">${cur.中文名}<span class="r">${lv(cur.一次等级)} → ${lv(cur.二次等级)}</span></h3>${why}</div></div>
   <div class="card" style="background:linear-gradient(135deg,rgba(239,245,255,.85),rgba(247,242,255,.8))"><h3>${icon("bot")}整套等级方案（所有保护对象共同决定） ${q("每个字段只能有一个等级，所以强化学习求的是覆盖全部保护对象的一整套方案。下面的效用、训练过程和构成都属于这套方案，切换保护对象时不变。")}<span class="r">直接定级 ${nk("直接定级")} · 联合评估 ${nk("联合评估")} · 整体核对 ${nk("整体核对")}</span></h3>
    <div class="kpis" style="margin-bottom:12px">${kpi(icon("tune"), "a", "调高等级的字段", `${up.length} <small>/ ${c.length}</small>`, "全部保护对象合计")}${kpi(icon("nodes"), "g", "越线组合切断比例", `${(G.切断比例 * 100).toFixed(1)}%`, `${D.一次定级下的越线.length} → ${D.二次定级后的越线.length} 个`)}
     ${kpi(icon("shield"), "b", "综合效用 " + q(TIP.grpo), f2(G.最终效用 ?? G.效用), `只做一次定级 ${f2(G.只做一次定级.效用)}`)}${kpi(icon("check"), gap != null && gap < 1 ? "g" : "a", "联合评估与精确最优的差距", gap == null ? "—" : gap.toFixed(1) + "%", G.参照最优 != null ? `精确最优 ${f2(G.参照最优)}（${G.参照最优求法}）` : "未求得参照解")}</div>
    <div class="row"><div class="f2"><div class="sub" style="font-weight:600;margin-bottom:4px">训练过程（每步采样 ${D.参数.group} 套完整方案）</div><div id="tc" style="height:220px"></div></div><div><div class="sub" style="font-weight:600;margin-bottom:4px">综合效用的构成</div><div id="uc" style="height:220px"></div></div></div></div>`;
  bindObj(); pick("tr.c", r => S.sel = +r.dataset.i);
  const cu = G.训练曲线; chart($("#tc"), { grid: { left: 56, right: 20, top: 30, bottom: 36 }, legend: { top: 0, right: 0 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: cu.map(x => x.步), name: "训练步", nameLocation: "middle", nameGap: 24 }, yAxis: { type: "value", scale: true, name: "效用", splitLine: { lineStyle: { color: C.grid } } },
    series: [{ name: "组内平均", type: "line", data: cu.map(x => x.组内平均), showSymbol: false, smooth: true, lineStyle: { color: C.blue, width: 2.5 }, itemStyle: { color: C.blue }, areaStyle: { color: "rgba(37,99,235,.08)" } }, { name: "组内最好", type: "line", data: cu.map(x => x.组内最好), showSymbol: false, smooth: true, lineStyle: { color: "#93c5fd", width: 1.5 }, itemStyle: { color: "#93c5fd" } }].concat(G.参照最优 != null ? [{ name: "精确最优", type: "line", data: cu.map(() => G.参照最优), showSymbol: false, lineStyle: { color: C.green, type: "dashed", width: 1.5 }, itemStyle: { color: C.green } }] : []) });
  const a = G.只做一次定级.构成, b = G.效用构成, ks = ["安全收益", "可用性成本", "聚合推断惩罚", "整体推断惩罚"].filter(x => x in b), col = ["#7fa2e8", "#f2b14c", "#e5484d", "#9b5de5"];
  chart($("#uc"), { grid: { left: 90, right: 24, top: 30, bottom: 24 }, legend: { top: 0, right: 0, itemWidth: 12, itemHeight: 8, textStyle: { fontSize: 11 } }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "value", splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", data: ["二次定级", "只做一次定级"], axisTick: { show: false } },
    series: ks.map((x, i) => ({ name: x, type: "bar", stack: "u", data: [b[x], a[x]], itemStyle: { color: col[i] }, barWidth: 24 })) });
}

/* ---------------- ⑤ 定级效果 ---------------- */
function pEffect() {
  const tn = T().中文名, R = D.换模型复测, res = D.仅凭公开基底可推出 || [], b0 = overCells("定级前"), b1 = overCells("定级后"), RC = ["", "var(--r1)", "var(--r2)", "var(--r3)"];
  const card = r => { const x = capOf(r.名称, tn), m = R.find(z => z.接收方 == r.名称 && z.敏感数据 == tn), base = isRes(r.名称, tn), nf = [cand().filter(f => f.一次等级 <= r.级).length, cand().filter(f => f.二次等级 <= r.级).length];
    if (!x) return `<div class="rcard" style="--rc:${RC[r.级]}"><div class="hd">${rt(r.名称, r.级)}<span class="tag">有权获取</span></div><div class="empty">该接收方有权获取“${tn}”，不涉及推断风险。</div><div class="kv"><span>可获取的候选字段</span><span class="num">${nf[0]} → <b>${nf[1]}</b></span></div></div>`;
    const ok = x.定级后 <= x.判定线, col = base ? C.amber : ok ? C.green : C.red;
    return `<div class="rcard" style="--rc:${RC[r.级]}"><div class="hd">${rt(r.名称, r.级)}${base ? '<span class="tag a">公开基底可推出</span>' : ok ? '<span class="tag g">调级后未越线</span>' : '<span class="tag r">调级后仍越线</span>'}</div>
      <div class="sub">对“${tn}”的推断精度（合并全部可获取字段）</div><div class="vs"><span class="o">${f2(x.定级前)}</span><span class="sub" style="margin-bottom:6px">→</span><span class="n" style="color:${col}">${f2(x.定级后)}</span></div>
      <div class="track"><i class="before" style="width:${x.定级前 * 100}%"></i><i class="after" style="width:${x.定级后 * 100}%;background:${col}"></i><b style="left:${x.判定线 * 100}%"></b><span style="left:${x.判定线 * 100}%">判定线 ${x.判定线}</span></div>
      <div class="kv"><span>可获取的候选字段</span><span class="num">${nf[0]} → <b>${nf[1]}</b></span></div>${m ? `<div class="kv"><span>神经网络 / 梯度提升树</span><span class="num">${m.调级前神经网络 != null ? f2(m.调级前神经网络) + " / " + f2(m.调级前梯度提升树) + " → " : ""}<b>${f2(m.神经网络)} / ${f2(m.梯度提升树)}</b></span></div>` : ""}</div>` };
  $("#main").innerHTML = objBar() + `<div class="rcards">${RECV3().map(card).join("")}</div>
   <div class="row"><div class="card f2"><h3>${icon("overview")}全部保护对象一览：一次定级 → 二次定级 ${q(TIP.V)}<span class="r"><span class="legend"><span><i style="background:rgba(229,72,77,.3)"></i>超过判定线</span><span><i style="background:rgba(15,159,110,.3)"></i>未超过</span></span></span></h3>${capMatrix()}</div>
    <div class="card"><h3>${icon("check")}整体结论</h3><div class="kv"><span>越线的“接收方 × 保护对象”</span><span class="num"><b class="red">${b0}</b> → <b class="${b1 ? "red" : "green"}">${b1}</b></span></div>
     <div class="kv"><span>调高等级的字段</span><span class="num">${cand().filter(f => f.二次等级 > f.一次等级).length} / ${cand().length}</span></div>
     ${RECV3().map(r => `<div class="kv"><span>${rt(r.名称, r.级)}可获取的候选字段</span><span class="num">${cand().filter(f => f.一次等级 <= r.级).length} → <b>${cand().filter(f => f.二次等级 <= r.级).length}</b></span></div>`).join("")}
     ${res.length ? `<div class="box a" style="margin-top:10px"><b>调级无法解决的项</b> ${q(TIP.base)}<div class="sub">${[...new Set(res.map(x => x.敏感数据))].join("、")}仅凭法定公开的信息即可推出，需由数据主管方另行评估。</div></div>` : ""}
     <button class="btn" id="exp" style="margin-top:14px;width:100%;justify-content:center">${icon("download")}导出定级台账（CSV）</button></div></div>
   <div class="row"><div class="card"><h3>${icon("flask")}整体核对 ${q(TIP.whole)}</h3>${D.整体核对.length ? `<table><tr><th>接收方</th><th>核对前</th><th>撤出</th><th>放回</th><th>核对后</th></tr>${D.整体核对.map(r => `<tr><td>${rt(r.接收方, rlev(r.接收方))}</td><td class="num"><b class="${r.核对前推断精度 > rline(rlev(r.接收方)) ? "red" : ""}">${f3(r.核对前推断精度)}</b></td><td class="num">${r.撤出字段数}</td><td class="num">${r.放回字段数}</td><td class="num"><b class="${r.核对后推断精度 > rline(rlev(r.接收方)) ? "amber" : "green"}">${f3(r.核对后推断精度)}</b></td></tr>`).join("")}</table>` : `<div class="empty">联合评估后各接收方均未越线，无需追加调整。</div>`}</div>
    <div class="card f2"><h3>${icon("flask")}换模型复测<span class="r">任一模型超过判定线即视为越线</span></h3><div class="scroll" data-sk="e1" style="max-height:300px"><table><tr><th>接收方</th><th>保护对象</th><th>调级前（神经网络 / 梯度提升树）</th><th>调级后（神经网络 / 梯度提升树）</th><th>判定线</th><th>结论</th></tr>
     ${R.map(x => { const o = Math.max(x.神经网络, x.梯度提升树) > x.判定线, r = isRes(x.接收方, x.敏感数据); return `<tr class="${x.敏感数据 == tn ? "pick" : ""}"><td>${rt(x.接收方, rlev(x.接收方))}</td><td><b>${x.敏感数据}</b></td><td class="num">${x.调级前神经网络 != null ? f3(x.调级前神经网络) + " / " + f3(x.调级前梯度提升树) : "—"}</td><td class="num"><b>${f3(x.神经网络)} / ${f3(x.梯度提升树)}</b></td><td class="num">${x.判定线}</td><td>${r ? `<span class="tag a">公开基底可推出</span>` : o ? '<span class="tag r">越线</span>' : '<span class="tag g">未越线</span>'}</td></tr>` }).join("")}</table></div></div></div>`;
  bindObj();
  $("#exp").onclick = () => { const rows = [["字段", "中文名", "类别", "角色", "公开情况", "影响对象", "影响程度", "一次等级", "二次等级", "调整方式", "最大M", "复核调整"]].concat(D.字段.map(f => [f.字段, f.中文名, f.类别, f.角色, f.公开情况, f.影响对象, f.影响程度, f.一次等级, f.二次等级, f.角色 == "候选" ? upKind(f) : "", f.M ? Math.max(...f.M) : "", f.复核调整 ? "是" : ""].map(v => `"${String(v).replace(/"/g, '""')}"`)));
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["﻿" + rows.map(r => r.join(",")).join("\n")], { type: "text/csv" })); a.download = D.id + "_定级台账.csv"; a.click() };
}
boot();
