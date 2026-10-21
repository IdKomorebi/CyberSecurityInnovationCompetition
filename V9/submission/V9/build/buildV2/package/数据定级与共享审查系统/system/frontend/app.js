/* 数据定级与共享审查系统 · V9 界面。只读取 ../samples/ 下已算好的任务文件；完整方式下可调参数重跑。 */
let TASKS = ["nem", "ieee30", "pjm", "community", "insurance"];      // 有服务端时改为服务端给出的任务列表（含上传的任务）
const PATHS = {
  combo: "M6 19a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4Z M18 19a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4Z M12 9.4a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4Z M7.2 15 10.8 9.2 M16.8 15 13.2 9.2 M8.2 16.8h7.6",
  shield: "M12 3 3.5 6.5v6c0 5 8.5 9 8.5 9s8.5-4 8.5-9v-6L12 3Z M8.5 12l2.5 2.5 4.5-5", overview: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  layers: "m12 3 10 5-10 5L2 8l10-5Zm-9 10 9 4 9-4M3 18l9 4 9-4", risk: "M3 19h18M5 15l4-5 5 3 6-9M15 4h5v5",
  nodes: "M8 5h8M6 7v10m12-10v10M8 19h8 M4 3h4v4H4z M16 3h4v4h-4z M4 17h4v4H4z M16 17h4v4h-4z M8 7l8 10", tune: "M4 7h16M4 17h16M8 4v6M16 14v6",
  check: "M8 12l3 3 6-7 M20 12v8H4V4h11", folder: "M3 6h7l2 2h9v12H3z M3 6V4h7l2 2", book: "M12 5C8 2 4 3 2 4v16c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-2-10 1Zm0 0v16",
  download: "M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5", link: "M10 14a4 4 0 0 0 6 0l3-3a4 4 0 0 0-6-6l-1 1 M14 10a4 4 0 0 0-6 0l-3 3a4 4 0 0 0 6 6l1-1",
  target: "M12 2v4M12 18v4M2 12h4M18 12h4 M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z", bot: "M12 3v3 M5 8h14v11H5z M9 13h.01M15 13h.01 M9 16h6", users: "M16 21v-3a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v3M20 8a4 4 0 0 1 0 8m2 5v-3M13 6a4 4 0 1 1-8 0 4 4 0 0 1 8 0",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z", plus: "M12 4v16M4 12h16", flask: "M9 3h6M10 3v6L4 19a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2l-6-10V3" };
const icon = n => `<svg class="icon" viewBox="0 0 24 24"><path d="${PATHS[n]}"/></svg>`;
const PAGES = [
  ["", "tasks", "任务管理", "folder", "管理内置与上传的定级任务"],
  ["", "overview", "总体概览", "overview", "定级流程各步骤的结果与风险变化"],
  ["字段本身", "grade1", "一次定级", "layers", "依据 GB/T 43697，按影响对象与影响程度确定字段等级"],
  ["字段本身", "single", "单独推断", "risk", "单个字段对保护对象的推断精度"],
  ["聚合推断风险", "aggr", "考虑背景知识的字段推断风险", "nodes", "在至多 K 个背景字段下，单个字段带来的最大推断增益 M", "字段推断风险"],
  ["聚合推断风险", "combos", "越线组合", "combo", "凑齐即超过判定线、缺少任一字段即不超过的最小字段组合"],
  ["定级与效果", "regrade", "二次定级", "tune", "以字段推断风险 M 和越线组合为输入，用强化学习求解整套等级"],
  ["定级与效果", "effect", "定级效果", "check", "调级前后各类接收方对保护对象的推断精度"]];
const S = { task: null, page: "overview", t: 0, K: null, sel: null, filter: "全部", afilter: "全部", kw: "", guide: null, gtab: 0, P: null, srv: { 完整方式: false, 可重跑: [], 作业: { 状态: "空闲" } } };
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
let D = null, ALL = {}, charts = [];
const LVN = n => n <= 4 ? n + " 级" : n == 5 ? "重要" : "核心", lv = n => `<span class="lv lv${n}">${LVN(n)}</span>`, f2 = x => (+x).toFixed(2), f3 = x => (+x).toFixed(3);
const q = t => `<span class="q" data-tip="${t}">?</span>`;
const TIPBOX = document.body.appendChild(Object.assign(document.createElement("div"), { id: "tipbox" }));
document.addEventListener("mouseover", e => { const el = e.target.closest && e.target.closest(".q"); if (!el) { TIPBOX.classList.remove("on"); return }
  TIPBOX.textContent = el.dataset.tip; const r = el.getBoundingClientRect(), w = TIPBOX.offsetWidth, h = TIPBOX.offsetHeight;
  let x = r.left + r.width / 2 - w / 2, y = r.bottom + 8; x = Math.max(8, Math.min(innerWidth - w - 8, x)); if (y + h > innerHeight - 8) y = r.top - h - 8;
  TIPBOX.style.left = x + "px"; TIPBOX.style.top = y + "px"; TIPBOX.classList.add("on") });
window.addEventListener("scroll", () => TIPBOX.classList.remove("on"), true);
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
  M: "字段推断风险 M：接收方已有至多 K 个其他字段（背景）时，再获得该字段，推断精度的最大提升；等于单独推断的精度加上背景增益。取值 0 至 1。K 由系统在 2、3 中自动选定。",
  Ksel: "背景预算 K 的选定：K 越大，考虑的背景越多、越保守。系统先看 K 从 1 加到 2 时风险靠前的字段 M 还涨多少；几乎不涨就取 2，否则再试 K = 3，平均再涨不少于 0.01 或有字段再涨不少于 0.05 就取 3。",
  direct: "直接定级：M 不低于直接定级线的字段，定为与被推断数据同级。",
  whole: "整体核对：联合评估之后，对每类接收方可获取的全部字段重新训练（神经网络与梯度提升树取较高）。仍越线时沿“逐个撤出”走完整条路径，取综合效用最高的位置，再逐个尝试放回。",
  grpo: "组相对策略优化：每一步对同一任务采样一组完整的等级方案，以组内相对优势更新策略。综合效用是安全收益、可用性成本、聚合推断惩罚、整体推断惩罚四项扣分之和，越接近 0 越好。",
  base: "公开基底：法定公开、所有接收方均已掌握的字段，在推断中始终可见，不参与调级。" };

/* ---------------- 启动与框架 ---------------- */
async function boot() {
  try { S.srv = await (await fetch("/api/status")).json(); if (S.srv.任务列表) TASKS = S.srv.任务列表.slice() } catch (e) { }
  await Promise.all(TASKS.map(async k => { try { ALL[k] = await (await fetch("../samples/" + k + ".json?" + Date.now())).json() } catch (e) { } }));
  const P = new URLSearchParams(location.search); ["task", "page"].forEach(k => P.get(k) && (S[k] = P.get(k))); ["t", "K", "sel"].forEach(k => P.get(k) != null && (S[k] = +P.get(k)));
  if (P.get("guide")) S.guide = S.page; if (P.get("modal")) S.modal = P.get("modal");
  if (!S.task || !ALL[S.task]) S.task = TASKS.find(k => ALL[k]);                // 默认打开任务列表中的第一个
  setTask(S.task, true);
}
function setTask(k, keep) { S.task = k; D = ALL[k]; S.P = Object.assign({}, D.参数); if (!keep || S.K == null) S.K = kUse(); if (!keep) { S.t = 0; S.sel = null; S.K = kUse() } S.t = Math.min(S.t, D.敏感.length - 1); S.K = Math.min(S.K, D.背景增益.length - 1); render(true) }
const kUse = () => D.K选择 && D.K选择.选定 != null ? D.K选择.选定 : (+D.参数.K || 2);           // 二次定级所用的背景预算 K
function go(p) { S.page = p; S.sel = null; render(true) }
function render(top) {
  const keep = top ? null : { y: window.scrollY, s: Object.fromEntries($$("[data-sk]").map(e => [e.dataset.sk, e.scrollTop])) };    // 记住滚动位置，避免点选后跳回顶部
  charts.forEach(c => c.dispose()); charts = []; const p = PAGES.find(p => p[1] == S.page), c = cand();
  let h = "", g = null, no = 0;
  PAGES.forEach(x => { if (x[0] != g) { g = x[0]; if (g) { const gi = ["字段本身", "聚合推断风险", "定级与效果"].indexOf(g); h += `<div class="grp g${gi}"><i>${"一二三"[gi]}</i>${g}</div>` } } h += `<a class="${x[1] == S.page ? "on" : ""}" data-p="${x[1]}">${icon(x[3])}<span>${x[5] || x[2]}</span>${x[0] ? `<b>0${++no}</b>` : ""}</a>` });
  $("#nav").innerHTML = h; $$("#nav a").forEach(a => a.onclick = () => go(a.dataset.p)); $("#logo").innerHTML = icon("shield");
  $("#cur").innerHTML = `<div class="l"><span>当前任务</span><a>切换</a></div><div class="n">${D.名称}</div><div class="m">${D.类别} · ${c.length} 个候选字段 · ${D.敏感.length} 项保护对象</div>`; $("#cur").onclick = () => go("tasks");
  $("#foot").innerHTML = `规则库　GB/T 43697<br>初判模型　${D.大语言模型}<br>${S.srv.完整方式 ? "完整方式 · 可重跑" : "演示方式 · 只读"}`;
  $("#crumb").innerHTML = S.page == "tasks" ? "" : `<b>${D.名称}</b>${p[0] ? " / " + p[0] : ""}`; $("#title").textContent = p[2]; $("#subtitle").innerHTML = icon(p[3]) + p[4];
  $("#guide").innerHTML = `${icon("book")}本页导览与参数`; $("#guide").onclick = () => { S.guide = S.page; S.gtab = 0; drawer() };
  ({ tasks: pTasks, overview: pOverview, grade1: pGrade1, single: pSingle, aggr: pAggr, combos: pCombos, regrade: pRegrade, effect: pEffect })[S.page]();
  drawer(); modal();
  if (keep) { $$("[data-sk]").forEach(e => { if (keep.s[e.dataset.sk] != null) e.scrollTop = keep.s[e.dataset.sk] }); window.scrollTo(0, keep.y) } else window.scrollTo(0, 0);
}
const objBar = (extra = "") => { const t = T(), no = RECV3().filter(r => r.级 < t.一次等级);
  return `<div class="objbar"><span class="lab">${icon("target")}保护对象</span>${sens().map((f, i) => `<span class="ob ${i == S.t ? "on" : ""}" data-t="${i}">${f.中文名} ${lv(f.一次等级)}</span>`).join("")}
   <span class="note">${extra || (no.length ? `不得被 ${no.map(r => rt(r.名称, r.级)).join("")} 推出` : "所有接收方均有权获取")}</span></div>` };
const bindObj = () => $$(".ob[data-t]").forEach(a => a.onclick = () => { S.t = +a.dataset.t; S.sel = null; render() });
const pick = (sel, fn) => $$(sel).forEach(r => r.onclick = () => { fn(r); render() });

/* ---------------- 导览抽屉：一图看懂 + 页面示意 + 术语 ---------------- */
const gc = (t, cls = "") => `<span class="gch ${cls}">${t}</span>`, ga = (t = "") => `<span class="gar">${t ? `<small>${t}</small>` : ""}<i>→</i></span>`;
const gn = (ic, t) => `<span class="gnode">${icon(ic)}<b>${t}</b></span>`;
const gbar = (segs, line, lab) => `<div class="gbar">${segs.map(s => `<i style="width:${s[0] * 100}%;background:${s[1]}"></i>`).join("")}${line != null ? `<b style="left:${line * 100}%"><em>${lab}</em></b>` : ""}</div>`;
const grow = (name, segs, val, tag) => `<div class="grow"><span class="gn2">${name}</span>${gbar(segs, SLINE, "")}<span class="gv">${val}</span>${tag}</div>`;
const ladder = () => `<div class="ladder">${[1, 2, 3, 4].map(l => `<div>${lv(l)}<span class="sub">谁能拿到</span>${l < 4 ? RECV3().filter(r => r.级 >= l).map(r => rt(r.名称, r.级)).join("") : rt("仅内部", 4)}</div>`).join("")}</div>`;
function tradeoff() {                                  // 示意：等级越高，风险扣分越少、可用性扣分越多，综合效用在中间取最大
  const d = [0, 1, 2, 3], S_ = d.map(x => -1.5 * Math.exp(-x)), C_ = d.map(x => -(Math.exp(.5 * x) - 1)), U = d.map((_, i) => S_[i] + C_[i]);
  const X = i => 60 + i * 125, Y = v => 34 + (-v) / 3.6 * 100, path = a => a.map((v, i) => (i ? "L" : "M") + X(i) + "," + Y(v)).join(""), best = U.indexOf(Math.max(...U));
  const lg = [["风险扣分", "#e5484d", 150], ["可用性扣分", "#f59e0b", 250], ["综合效用", "#2563eb", 370]];
  return `<svg viewBox="0 0 480 160" class="gsvg">${lg.map(l => `<line x1="${l[2]}" y1="12" x2="${l[2] + 18}" y2="12" stroke="${l[1]}" stroke-width="3"/><text x="${l[2] + 24}" y="16">${l[0]}</text>`).join("")}
    <line x1="60" y1="34" x2="435" y2="34" stroke="#cbd5e1" stroke-dasharray="3 3"/><text x="52" y="38" text-anchor="end">0</text><text x="52" y="134" text-anchor="end">扣分多</text>
    <path d="${path(S_)}" stroke="#e5484d" fill="none" stroke-width="2"/><path d="${path(C_)}" stroke="#f59e0b" fill="none" stroke-width="2"/><path d="${path(U)}" stroke="#2563eb" fill="none" stroke-width="3"/>
    <circle cx="${X(best)}" cy="${Y(U[best])}" r="6" fill="#2563eb" stroke="#fff" stroke-width="2"/><text x="${X(best)}" y="${Y(U[best]) + 22}" text-anchor="middle" fill="#2563eb" font-weight="700">效用最高</text>
    ${d.map(i => `<text x="${X(i)}" y="154" text-anchor="middle">${i ? "原级 +" + i : "原级"}</text>`).join("")}</svg>`;
}
const GUIDE = {
  tasks: { q: "选择任务，或上传一张数据表新建任务。",
    fig: () => `<div class="fx nw">${gn("folder", "上传表格")}${ga()}${gn("bot", "大模型起草目录")}${ga()}${gn("users", "确认保护对象")}${ga()}${gn("tune", "后台全流程")}</div>
      <div class="gtag"><span>CSV / Excel</span><span>自动选空闲显卡，无显卡用处理器</span><span>复核：人工或另一个大模型</span></div>`,
    map: [[["任务卡片：点击切换，拖动排序", 3, 56], ["新建任务", 1, 56]]], terms: [["复核方式", "人工，或另配一个大模型", "人工：在一次定级页的“人工复核”中逐条修改并重算；大模型：由另配的大模型逐条复核，不同意见留痕。"]], keys: [] },
  overview: { q: "调级前后，各类接收方对保护对象的推断精度。",
    fig: () => `<div class="fx nw">${gc("接收方能拿到的字段")}${ga("训练模型")}${gc("推断保护对象", "t")}</div>
      ${gbar([[.86, riskBar(.86)]], .7, "判定线 0.7")}<div class="gtag"><span class="r">超过判定线 = 越线</span><span class="g">二次定级后降到线下</span></div>
      <div class="steps5">${["一次定级", "单独推断", "背景下风险", "越线组合", "二次定级", "定级效果"].map((s, i) => `<span><i>${i + 1}</i>${s}</span>`).join("")}</div>`,
    map: [[["关键数字", 1, 28]], [["六个步骤，点击进入", 1, 28]], [["各接收方 × 保护对象：调级前 → 调级后", 1, 40]]], terms: [["推断精度", "0 推不出，1 完全还原", TIP.V], ["判定线", "超过即视为能推出", TIP.line]], keys: [] },
  grade1: { q: "依据 GB/T 43697 给每个字段定级。",
    fig: () => `<div class="fx nw">${gn("book", "国标条文")}${ga()}${gn("bot", "大模型初判")}${ga()}${gn("users", "复核")}${ga()}${gn("layers", "一次等级")}</div>
      <div class="fx nw" style="margin-top:12px">${gc("影响对象：经济运行")}<b>×</b>${gc("影响程度：一般危害")}${ga("查判定表")}${lv(D.判定表["经济运行"]["一般危害"])}</div>
      <div class="glab" style="margin-top:12px">等级决定谁能拿到</div>${ladder()}`,
    map: [[["四个步骤；“人工复核”可修改", 1, 28]], [["全部字段的等级（点一行）", 3, 60], ["该行的定级依据", 2, 60]]], terms: [["影响对象", "六类", "国家安全、经济运行、社会秩序、公共利益、组织权益、个人权益。"], ["影响程度", "四档", "无危害、一般危害、严重危害、特别严重危害。"]], keys: [] },
  single: { q: "只给一个字段，能把保护对象推到多准。",
    fig: () => `<div class="fx nw">${gc("一个字段")}${ga("训练模型")}${gc("推断保护对象", "t")}</div>
      <div class="gcol">${grow("字段甲", [[.81, riskBar(.81)]], "0.81", '<span class="tag r">单独过线</span>')}${grow("字段乙", [[.18, riskBar(.18)]], "0.18", '<span class="tag g">单独不过线</span>')}<div class="gline">竖线：单字段判定线 0.7</div></div>
      <div class="gtag"><span class="a">单独不过线 ≠ 安全，见下一页</span></div>`,
    map: [[["保护对象", 1, 28]], [["关键数字", 1, 28]], [["各字段单独推断（点一行）", 3, 56], ["推断值与真实值", 2, 56]]], terms: [["推断精度", "0 推不出，1 完全还原", TIP.V], ["单字段判定线", "一律 0.7", "单个字段单独推断的精度达到 0.7 即为单独过线，不分接收方。多个字段合并时才按接收方区分判定线（社会公众 0.7，其他接收方 0.8）。"]], keys: [] },
  aggr: { q: "接收方已有至多 K 个背景字段时，再拿到这个字段，推断精度最多提高多少（M）。",
    fig: () => `<div class="gstack"><i style="width:22%;background:#c3cddd"></i><i style="width:18%;background:${riskBar(.18)}"></i><i style="width:41%;background:${GAIN}"></i></div>
      <div class="gbrace"><span style="width:22%">只有背景</span><span style="width:18%">单独作用</span><span style="width:41%">背景增益</span></div>
      <div class="gform">M ＝ <span>单独推断</span> ＋ <span class="p">背景增益</span></div>
      <div class="kmin">${[[0, .18], [1, .43], [2, .59], [3, .59]].map(([k, v]) => `<div><i style="height:${v * 90}px"></i><b>${f2(v)}</b><span>K = ${k}</span></div>`).join("")}<p>K 自动取 2 或 3：<br>M 不再明显增长就停</p></div>
      <div class="gtag"><span class="r">M ≥ ${D.参数.直接定级线}：直接定级</span><span class="b">其余：进入二次定级的安全收益</span></div>`,
    map: [[["保护对象", 1, 28]], [["M 总览，右下角调 K", 1, 34]], [["K 的选定（可展开）", 1, 26]], [["各字段的单独推断与背景增益（点一行）", 3, 56], ["切换 K；最危险的背景与曲线", 2, 56]]], terms: [["字段推断风险 M", "单独推断 + 背景增益", TIP.M], ["背景预算 K", "自动在 2、3 中选定", TIP.Ksel], ["直接定级线", "M 达到即直接调高", TIP.direct]], keys: ["K", "直接定级线"] },
  combos: { q: "哪些字段凑齐就越线、少一个就不越线。",
    fig: () => `${lattice(["南澳可用容量", "南澳风电预测", "南澳光伏预测"], [[["南澳可用容量"], .045], [["南澳风电预测"], .183], [["南澳光伏预测"], .186], [["南澳可用容量", "南澳风电预测"], .478], [["南澳可用容量", "南澳光伏预测"], .223], [["南澳风电预测", "南澳光伏预测"], .511]], .811, .7)}
      <div class="fx nw" style="margin-top:10px">${gc("估计器打分")}${ga()}${gc("挑出可能越线的")}${ga()}${gc("重新训练，更新结果", "b")}</div>
      <div class="gtag"><span>规模 ≤ ${Math.min(D.组合上限, 3)}：全部重新训练</span><span class="b">更大：先估计，按需重训</span></div>`,
    map: [[["保护对象", 1, 28]], [["关键数字", 1, 28]], [["组合最大字段数", 3, 40], ["字段出现次数", 2, 40]], [["最小越线组合（点一行）", 3, 56], ["子集格子图、成员 M、曲线", 2, 56]]], terms: [["最小越线组合", "凑齐越线，少一个不越线", TIP.combo], ["估计器", "预训练一次，逐组合闭式读出", "先用随机遮挡、重建被遮字段的方式预训练一个主干网络；对每个组合，取主干在该组合下的特征，在训练行上做一次岭回归，在留出行上计算推断精度。每个组合不到 1 毫秒，与重新训练的平均误差在 0.005 至 0.013 之间。估计只用于筛选，结论以重新训练为准。"]], keys: [] },
  regrade: { q: "字段推断风险 M 和越线组合共同决定效用，强化学习据此学出整套等级。",
    fig: () => `<div class="rlmap"><div class="ins"><span class="gch m">${icon("nodes")}字段推断风险 M</span><span class="gch c">${icon("combo")}越线组合</span></div><span class="gar"><i>→</i></span>
        <div class="u"><b>效用 U</b><span class="t1">安全收益</span><span class="t2">可用性成本</span><span class="t3">聚合推断惩罚</span></div><span class="gar"><i>→</i></span>
        <div class="loop"><b>强化学习</b><span>采样 ${D.参数.group} 套方案</span><span>组内比较</span><span>更新策略</span><em>↻ ${D.参数.steps} 步</em></div></div>
      <div class="stage3" style="margin-top:12px"><div class="r"><b>① 直接定级</b>M ≥ ${D.参数.直接定级线}</div><div class="b"><b>② 联合评估</b>强化学习求整套等级</div><div class="a"><b>③ 整体核对</b>合并全部字段复查</div></div>
      <div class="glab" style="margin-top:12px">等级越高：风险扣分减少，可用性扣分增加</div>${tradeoff()}`,
    map: [[["保护范围", 1, 28]], [["M + 越线组合 → 强化学习；效用公式", 1, 34]], [["关键数字、训练过程、效用构成", 1, 30]], [["字段调整明细（点一行）", 3, 50], ["调级原因与效用对比", 2, 50]]], terms: [["综合效用", "越接近 0 越好", TIP.grpo], ["整体核对", "合并全部字段复查", TIP.whole]], keys: ["beta", "lam", "eta", "sigma", "rho", "rho_w", "steps", "group", "严格模式"] },
  effect: { q: "调级前后，各类接收方对保护对象的推断精度。",
    fig: () => `<div class="gcol">${grow("一次定级", [[.92, riskBar(.92)]], "0.92", '<span class="tag r">越线</span>')}${grow("二次定级", [[.62, riskBar(.62)]], "0.62", '<span class="tag g">未越线</span>')}<div class="gline">竖线：判定线</div></div>
      <div class="gtag"><span>接收方能拿到的字段变少</span><span>神经网络与梯度提升树取较高者</span></div>`,
    map: [[["保护对象", 1, 28]], [["三类接收方：调级前 → 调级后", 1, 28]], [["全部保护对象一览", 3, 34], ["结论与台账导出", 2, 34]], [["换模型复测", 3, 28], ["整体核对", 2, 28]]], terms: [["推断精度", "0 推不出，1 完全还原", TIP.V], ["公开基底", "人人都有的公开字段", TIP.base], ["整体核对", "合并全部字段复查", TIP.whole]], keys: ["rho_w", "严格模式"] } };
const PDEF = { 公众判定线: ["社会公众判定线", 0.05, 0.5, 0.95, TIP.line], 其他判定线: ["其他接收方判定线", 0.05, 0.5, 0.95, TIP.line], K: ["背景字段数上限 K", 1, 0, 2, TIP.M], 直接定级线: ["直接定级线", 0.05, 0.5, 0.95, TIP.direct],
  beta: ["安全收益系数 β", 0.5, 0, 10, "越大越倾向于上调 M 高的字段。"], lam: ["安全收益衰减 λ", 0.1, 0.1, 3, "每上调一级，该字段剩余风险的衰减速度。"], eta: ["可用性成本系数 η", 0.5, 0, 10, "越大越不愿意上调。"], sigma: ["可用性成本增长 σ", 0.1, 0.1, 2, "连续上调多级时成本的增长速度。"],
  rho: ["聚合推断惩罚 ρ", 0.5, 0, 20, "每个仍成立的越线组合扣 ρ × 超出判定线的幅度 ÷ 0.1。"], rho_w: ["整体推断惩罚 ρw", 0.5, 0, 20, "各接收方合并全部字段后超出判定线的部分，每超出 0.1 扣 ρw 分；推断精度来自重新训练。"],
  steps: ["训练步数", 50, 50, 2000, "策略更新的次数。"], group: ["每组方案数", 16, 16, 512, "每一步对同一任务采样的完整等级方案数量。"], 严格模式: ["严格模式", 0, 0, 1, "开启后不允许保留越线，一直调到各接收方不越线。"] };
const kMax = () => Math.max(3, Math.min((D.组合上限 || 3) - 1, 4));
const canRun = () => S.srv.完整方式 && S.srv.可重跑.includes(S.task), dirty = () => JSON.stringify(S.P) != JSON.stringify(D.参数);
function drawer() {
  if (!S.guide) { $("#drawer").innerHTML = ""; return }
  const G = GUIDE[S.guide], pg = PAGES.find(p => p[1] == S.guide), j = S.srv.作业, busy = j.状态 == "运行中";
  const intro = `<p class="lead">${G.q}</p>
    <h4>示意</h4><div class="fig">${G.fig()}</div>
    <h4>页面布局</h4><div class="wf">${G.map.map(r => `<div class="wr">${r.map(c => `<div class="wc" style="flex:${c[1]};height:${c[2]}px"><span>${c[0]}</span></div>`).join("")}</div>`).join("")}</div>
    ${G.terms.length ? `<h4>术语</h4><table class="gterm">${G.terms.map(x => `<tr><td>${x[0]}</td><td>${x[1]} ${q(x[2])}</td></tr>`).join("")}</table>` : ""}`;
  const params = G.keys.length ? `<div class="box ${busy ? "a" : ""}" style="margin-bottom:12px"><span class="sub">${busy ? `正在重跑“${j.任务}”，完成后自动刷新…` : !canRun() ? "当前为演示方式或该任务没有缓存，参数只读。" : dirty() ? "参数已修改，尚未生效。" : "当前结果即按下列参数计算。重跑只重做二次定级及之后的步骤。"}</span>${j.状态 == "失败" ? ` <span class="red">上次重跑失败</span>` : ""}</div>` +
    G.keys.map(k => { const d = PDEF[k]; return k == "K" ? `<div class="kv"><span>${d[0]} ${q(TIP.Ksel)}</span><span><select class="search" style="width:120px" data-k="K">${["自动", ...Array.from({ length: kMax() + 1 }, (_, i) => i)].map(v => `<option value="${v}" ${String(S.P.K) == String(v) ? "selected" : ""}>${v == "自动" ? "自动（2 或 3）" : "固定 " + v}</option>`).join("")}</select>${String(S.P.K) != String(D.参数.K) ? ' <span class="tag a">已改</span>' : ""}<div class="sub" style="font-size:11.5px;text-align:right">当前结果：K = ${kUse()}${D.K选择 && D.K选择.方式 == "自动" ? "（自动选定）" : ""}</div></span></div>` : k == "严格模式" ? `<div class="kv"><span>${d[0]} ${q(d[4])}</span><span><label><input type="checkbox" data-k="${k}" ${S.P[k] ? "checked" : ""}> ${S.P[k] ? "开启" : "关闭"}</label></span></div>` :
      `<div class="kv"><span>${d[0]} ${q(d[4])}</span><span><input class="search" style="width:96px;text-align:right" type="number" data-k="${k}" value="${S.P[k]}" step="${d[1]}" min="${d[2]}" max="${k == "K" ? kMax() : d[3]}">${k == "K" ? `<div class="sub" style="font-size:11.5px;text-align:right">本任务最大 ${kMax()}：推断验证精确算到 ${kMax() + 1} 个字段的组合</div>` : ""}${S.P[k] != D.参数[k] ? ' <span class="tag a">已改</span>' : ""}</span></div>` }).join("") +
    `<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:16px"><button class="btn o" id="rst" ${dirty() ? "" : "disabled"}>恢复</button><button class="btn" id="run" ${canRun() && !busy ? "" : "disabled"}>${busy ? "运行中…" : "应用并重跑"}</button></div>` : `<div class="empty">本页没有可调的参数。${S.guide == "grade1" ? "一次定级的规则来自国标判定表。" : ""}</div>`;
  $("#drawer").innerHTML = `<div class="mask" id="dm" style="background:rgba(15,26,46,.18)"></div><div class="dw"><div class="dh"><span class="no">${icon(pg[3])}</span><div><h3>${pg[2]}</h3><div class="sub">${pg[4]}</div></div><span class="x" id="dx">×</span></div>
    <div class="tabs">${["页面说明", "参数调整"].map((n, i) => `<a class="${i == S.gtab ? "on" : ""}" data-gt="${i}">${n}</a>`).join("")}</div><div class="db">${S.gtab == 0 ? intro : params}</div></div>`;
  $("#dm").onclick = $("#dx").onclick = () => { S.guide = null; drawer() }; $$("[data-gt]").forEach(a => a.onclick = () => { S.gtab = +a.dataset.gt; drawer() });
  $$("[data-k]").forEach(e => { if (!canRun()) e.disabled = true; e.onchange = () => { S.P[e.dataset.k] = e.type == "checkbox" ? e.checked : e.value == "自动" ? "自动" : +e.value; drawer() } });
  if ($("#rst")) { $("#rst").onclick = () => { S.P = Object.assign({}, D.参数); drawer() };
    $("#run").onclick = async () => { const r = await (await fetch("/api/rerun", { method: "POST", body: JSON.stringify({ 任务: S.task, 参数: S.P }) })).json(); if (r.错误) return alert(r.错误); S.srv.作业 = { 状态: "运行中", 任务: S.task }; drawer(); poll() } }
}
function poll() {
  clearInterval(S.pt); S.pt = setInterval(async () => { try { S.srv = await (await fetch("/api/status")).json() } catch (e) { return }
    if (S.srv.作业.状态 != "运行中") { clearInterval(S.pt); if (S.srv.作业.状态 == "完成") { delete CURV[S.task]; ALL[S.task] = await (await fetch("../samples/" + S.task + ".json?" + Date.now())).json(); setTask(S.task, true) } else drawer() } }, 2000);
}

/* ---------------- 弹窗（一次定级的四个步骤） ---------------- */
/* 复核：逐条对照大模型初判；可在这里修改，保存后按复核后的等级重做二次定级 */
const OBJS = ["国家安全", "经济运行", "社会秩序", "公共利益", "组织权益", "个人权益"], DEGS = ["无危害", "一般危害", "严重危害", "特别严重危害"];
const lvPreview = (f, o, d) => Math.max(f.最低级别 || 1, d == "无危害" || !D.判定表[o] ? 1 : (D.判定表[o][d] || 1));
function reviewBody(all, fix) {
  const E = S.revEdit, busy = S.srv.作业.状态 == "运行中", OP = (S.llmop || {})[S.task], ops = OP && OP.意见 ? Object.fromEntries(OP.意见.map(x => [x.字段, x])) : null;
  if (OP === undefined && canRunAny()) loadOpinion();
  const src = [...new Set(fix.map(f => f.复核来源 || "人工复核"))].join("、") || "无";
  const opt = (i, k, list, v) => `<select data-rv="${i}" data-k="${k}">${list.map(o => `<option ${o == v ? "selected" : ""}>${o}</option>`).join("")}</select>`;
  const llmBusy = busy && S.srv.作业.类型 == "大模型复核" && S.srv.作业.任务 == S.task;
  const rows = all.map((f, i) => { const v = E ? E[i] : { 对象: f.影响对象, 程度: f.影响程度, 理由: f.复核理由 || "", 来源: f.复核来源 }, ch = v.对象 != f.初判.影响对象 || v.程度 != f.初判.影响程度, nl = E ? lvPreview(f, v.对象, v.程度) : f.一次等级, o = ops && ops[f.字段];
    const sug = !ops ? "" : `<td class="sub" style="font-size:12px;max-width:230px">${o ? `<b style="color:#7c3aed">建议 ${o.影响对象} · ${o.影响程度} → ${lv(lvPreview(f, o.影响对象, o.影响程度))}</b><br>${o.理由}${E ? ` <a class="adopt" data-ad="${i}">采纳</a>` : ""}` : "同意"}</td>`;
    return `<tr class="${ch ? "pick" : ""}"><td class="nw"><b>${f.中文名}</b></td><td>${f.角色 == "敏感" ? '<span class="tag r">保护对象</span>' : '<span class="tag b">候选</span>'}</td><td class="nw">${f.初判.影响对象} · ${f.初判.影响程度} → ${lv(f.初判.等级)}</td>${sug}
      <td class="nw">${E ? opt(i, "对象", OBJS, v.对象) + " " + opt(i, "程度", DEGS, v.程度) : ch ? `${v.对象} · ${v.程度}` : '<span class="sub">同意初判</span>'}</td><td class="nw">${lv(nl)}</td>
      <td>${E ? `<input data-rv="${i}" data-k="理由" value="${(v.理由 || "").replace(/"/g, "&quot;")}" placeholder="${ch ? "必填" : ""}" ${ch ? "" : "disabled"}>` : `<span class="sub" style="font-size:12.5px">${ch ? v.理由 : f.初判.理由}</span>`}</td>
      <td class="sub" style="font-size:12px;max-width:130px">${ch ? v.来源 || "人工复核" : ""}</td></tr>` }).join("");
  const bar = `<div class="rvbar"><span>初判：${D.大语言模型}；已采用的复核来源：${src}</span>
    ${OP && OP.意见 ? `<span class="tag v">${OP.模型} 于 ${OP.时间} 复核 ${OP.字段数} 个字段，${OP.意见.length} 条不同意见</span>` : ""}
    ${canRunAny() ? `<button class="btn o" id="rvl" ${busy ? "disabled" : ""}>${llmBusy ? "大模型复核中… " + (S.srv.作业.日志 || "") : `使用 ${S.srv.复核模型 || "另一个大模型"} ${OP && OP.意见 ? "重新复核" : "复核"}`}</button>` : ""}</div>`;
  return `${bar}<div class="scroll" style="max-height:56vh"><table class="wtab rvtab"><tr><th>字段</th><th>角色</th><th>大模型初判</th>${ops ? "<th>另一个大模型的意见</th>" : ""}<th>复核结果</th><th>等级</th><th>理由</th><th>来源</th></tr>${rows}</table></div>
    <div class="act">${E ? `<span class="sub" style="margin-right:auto">改动 ${all.filter((f, i) => E[i].对象 != f.初判.影响对象 || E[i].程度 != f.初判.影响程度).length} 个字段；保存后按新的一次等级重做二次定级、整体核对与复测</span>${ops && OP.意见.length ? '<button class="btn o" id="rva">全部采纳大模型意见</button>' : ""}<button class="btn o" id="rvc">取消</button><button class="btn" id="rvs" ${busy ? "disabled" : ""}>${busy ? "已有作业在运行" : "保存并重算"}</button>`
      : canRun() ? `<button class="btn" id="rve">修改复核</button>` : `<span class="sub">当前为演示方式，只能查看</span>`}</div>`;
}
const canRunAny = () => S.srv.完整方式;
async function loadOpinion() { S.llmop = S.llmop || {}; S.llmop[S.task] = null; try { S.llmop[S.task] = (await api("/api/llmreview?任务=" + S.task)).意见 } catch (e) { } if (S.modal == "review") modal() }
function bindReview(all) {
  if ($("#rve")) $("#rve").onclick = () => { S.revEdit = all.map(f => ({ 对象: f.影响对象, 程度: f.影响程度, 理由: f.复核理由 || "", 来源: f.复核来源 || "" })); modal() };
  if ($("#rvc")) $("#rvc").onclick = () => { S.revEdit = null; modal() };
  const keep = fn => { const sk = $("#modal .scroll").scrollTop; fn(); modal(); $("#modal .scroll").scrollTop = sk };
  $$("[data-rv]").forEach(e => e.onchange = () => { const v = S.revEdit[+e.dataset.rv]; v[e.dataset.k] = e.value; if (e.dataset.k != "理由") keep(() => v.来源 = "人工复核") });
  const adopt = i => { const o = S.llmop[S.task].意见.find(x => x.字段 == all[i].字段); Object.assign(S.revEdit[i], { 对象: o.影响对象, 程度: o.影响程度, 理由: o.理由, 来源: o.来源 }) };
  $$("[data-ad]").forEach(a => a.onclick = () => keep(() => adopt(+a.dataset.ad)));
  if ($("#rva")) $("#rva").onclick = () => keep(() => all.forEach((f, i) => { if (S.llmop[S.task].意见.some(x => x.字段 == f.字段)) adopt(i) }));
  if ($("#rvl")) $("#rvl").onclick = async () => { try { await api("/api/llmreview", { 任务: S.task }); S.srv.作业 = { 状态: "运行中", 任务: S.task, 类型: "大模型复核" }; modal(); pollOpinion() } catch (e) { alert(e.message) } };
  if ($("#rvs")) $("#rvs").onclick = async () => {
    const fx = all.map((f, i) => ({ f, v: S.revEdit[i] })).filter(x => x.v.对象 != x.f.初判.影响对象 || x.v.程度 != x.f.初判.影响程度)
      .map(x => ({ 字段: x.f.字段, 影响对象: x.v.对象, 影响程度: x.v.程度, 理由: x.v.理由, 来源: x.v.来源 || "人工复核" }));
    if (fx.some(x => !String(x.理由).trim())) return alert("改动过的字段请写明复核理由");
    try { await api("/api/fix", { 任务: S.task, 调整: fx }); S.srv.作业 = { 状态: "运行中", 任务: S.task }; S.revEdit = null; S.modal = null; modal(); render(); poll() } catch (e) { alert(e.message) } };
}
function pollOpinion() {                                // 大模型复核只产生意见，不改结果；完成后刷新弹窗
  clearInterval(S.opt); S.opt = setInterval(async () => { try { S.srv = await api("/api/status") } catch (e) { return }
    if (S.srv.作业.状态 == "运行中") { if (S.modal == "review") { const sk = $("#modal .scroll") && $("#modal .scroll").scrollTop; modal(); if (sk) $("#modal .scroll").scrollTop = sk } return }
    clearInterval(S.opt); if (S.srv.作业.状态 == "失败") alert(S.srv.作业.日志); delete S.llmop[S.task]; if (S.modal == "review") modal() }, 2000);
}
function modal() {
  if (!S.modal) { if (!S.up) $("#modal").innerHTML = ""; return }
  const all = D.字段, objs = ["国家安全", "经济运行", "社会秩序", "公共利益", "组织权益", "个人权益"], degs = ["一般危害", "严重危害", "特别严重危害"], cnt = (k, arr) => arr.map(v => [v, all.filter(f => f.初判[k] == v).length]).filter(x => x[1]);
  const matrix = `<table class="mx mxm"><tr><th></th>${degs.map(d => `<th>${d}</th>`).join("")}</tr>${objs.map(o => `<tr><th style="text-align:right">${o}</th>${degs.map(d => `<td>${lv(D.判定表[o][d])}</td>`).join("")}</tr>`).join("")}<tr><th style="text-align:right">无危害</th><td colspan="3">${lv(1)}</td></tr></table>`;
  const ex = all[S.sel ?? 0] || all[0], fix = all.filter(f => f.复核调整);
  const body = {
    rules: [icon("book"), "规则库：GB/T 43697《数据安全技术 数据分类分级规则》", `<div class="row" style="margin-top:12px"><div><h4>判定表（影响对象 × 影响程度）</h4>${matrix}<p class="sub">国标第 6 章表 1 给出核心、重要、一般三档；一般数据按附录 H.1 细分为 1 至 4 级。</p></div>
      <div><h4>等级与共享范围</h4><table class="tbm">${D.等级表.map(l => `<tr><td>${lv(l.级)}</td><td>${l.共享范围}</td></tr>`).join("")}</table></div></div>
      <h4>入库的条文（${D.条文.length} 条）</h4><table class="tbm art"><colgroup><col style="width:118px"><col style="width:120px"><col></colgroup><tr><th>编号</th><th>标题</th><th>内容</th></tr>${D.条文.map(c => `<tr><td class="nw"><b>${c.编号}</b></td><td>${c.标题}</td><td class="sub" style="font-size:12.5px">${c.内容}</td></tr>`).join("")}</table>`],
    llm: [icon("bot"), `大语言模型初判：${D.大语言模型}`, `<div class="lg3"><div class="gl b"><div class="k">判定字段</div><div class="big">${all.length}</div><div class="s">每个字段调用一次，结果缓存</div></div>
      <div class="gl p"><div class="k">检索方式</div><div class="v">字符二元组重合度，取最相关的 4 条条文</div><div class="s">判定表（6.5 表 1）必定入选</div></div><div class="gl g"><div class="k">输出</div><div class="v">影响对象、影响程度、个人信息类型、依据条文、理由</div><div class="s">温度 0，结构化输出</div></div></div>
      <h4>提示词要点</h4><div class="pmt"><span><b>只判断两件事</b>泄露后最主要的影响对象（六类之一）和影响程度（四档之一）</span><span><b>已公开的数据</b>影响程度取“无危害”</span><span><b>个人信息</b>另判敏感或一般</span><span><b>输出</b>依据条文编号与不超过 60 字的理由</span></div>
      <div class="row"><div class="gl"><h4>初判的影响对象</h4>${cnt("影响对象", objs).map(x => `<div class="dbar"><span>${x[0]}</span><i style="width:${x[1] / all.length * 100}%"></i><b>${x[1]}</b></div>`).join("")}</div><div class="gl"><h4>初判的影响程度</h4>${cnt("影响程度", ["无危害", ...degs]).map(x => `<div class="dbar"><span>${x[0]}</span><i style="width:${x[1] / all.length * 100}%"></i><b>${x[1]}</b></div>`).join("")}</div></div>
      <h4>示例：${ex.中文名}</h4><div class="exm"><div class="flow"><span class="st"><small>检索到的条文</small>${ex.检索到的条文.join("、")}</span><b>→</b><span class="st"><small>影响对象 · 程度</small>${ex.初判.影响对象} · ${ex.初判.影响程度}</span><b>→</b><span class="st"><small>查判定表</small>${lv(ex.初判.等级)}</span></div><div class="why">${ex.初判.理由}</div></div>`],
    review: [icon("users"), `复核：调整 ${fix.length} 个字段`, reviewBody(all, fix)],
    levels: [icon("layers"), "一次等级分布", `<div id="mlv" style="height:260px;margin-top:8px"></div><table>${[1, 2, 3, 4, 5, 6].map(l => [l, all.filter(f => f.一次等级 == l)]).filter(x => x[1].length).map(x => `<tr><td>${lv(x[0])}</td><td class="num"><b>${x[1].length}</b></td><td>${recvTags(x[0])}</td><td class="sub" style="font-size:12.5px">${x[1].slice(0, 6).map(f => f.中文名).join("、")}${x[1].length > 6 ? " 等" : ""}</td></tr>`).join("")}</table>`] }[S.modal];
  $("#modal").innerHTML = `<div class="mask" id="mm"><div class="dlg" onclick="event.stopPropagation()" style="${S.modal == "review" ? "width:min(1280px,96vw)" : S.modal == "rules" ? "width:min(1060px,94vw)" : ""}"><h2><span class="pipe"><span class="no">${body[0]}</span></span>${body[1]}<span class="x" id="mx">×</span></h2>${body[2]}</div></div>`;
  $("#mm").onclick = $("#mx").onclick = () => { S.modal = null; S.revEdit = null; modal() };
  if (S.modal == "review") bindReview(all);
  if (S.modal == "levels") { const ls = [1, 2, 3, 4, 5, 6].filter(l => all.some(f => f.一次等级 == l)), col = ["", "#16a34a", "#2563eb", "#d97706", "#ea580c", "#dc2626", "#7f1d1d"];
    chart($("#mlv"), { tooltip: {}, grid: { left: 40, right: 20, top: 20, bottom: 30 }, xAxis: { type: "category", data: ls.map(LVN) }, yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: C.grid } } }, series: [{ type: "bar", barWidth: 38, data: ls.map(l => ({ value: all.filter(f => f.一次等级 == l).length, itemStyle: { color: col[l], borderRadius: [6, 6, 0, 0] } })), label: { show: true, position: "top" } }] }) }
}

/* ---------------- 任务管理 ---------------- */
function pTasks() {
  const pending = (S.srv.上传任务 || []).filter(u => u.状态 != "完成" || !ALL[u.任务]);
  const del = k => canRunAny() ? `<span class="tdel" data-del="${k}" title="删除任务">×</span>` : "";
  $("#main").innerHTML = (canRunAny() ? `<div class="sub" style="margin:-4px 0 10px">拖动卡片可以调整顺序；鼠标移到卡片上，右上角可以删除（文件移到回收站，可恢复）。</div>` : "") + `<div class="tcards">${TASKS.filter(k => ALL[k]).map(k => { const d = ALL[k], c = cand(d); return `<div class="tcard ${k == S.task ? "on" : ""}" data-k="${k}">${del(k)}<div style="display:flex;justify-content:space-between;padding-right:22px"><span class="tag b">${d.类别}</span>${k == S.task ? '<span class="tag g">当前任务</span>' : k[0] == "u" ? '<span class="tag v">上传</span>' : ""}</div>
    <h3>${d.名称}</h3><div class="sub">${d.数据说明.slice(0, 70)}…</div><div class="st"><div><b>${d.样本数}</b>样本</div><div><b>${d.字段.length}</b>字段</div><div><b>${d.敏感.length}</b>保护对象</div><div><b>${c.filter(f => f.二次等级 > f.一次等级).length}</b>调高</div></div></div>` }).join("")}
   ${pending.map(u => `<div class="tcard" data-up="${u.任务}">${u.状态 == "运行中" ? "" : del(u.任务)}<div style="display:flex;justify-content:space-between;padding-right:22px"><span class="tag v">新建中</span><span class="tag ${u.状态 == "失败" ? "r" : "a"}">${{ 待起草: "待起草目录", 待确认: "待确认目录", 待复核: "待复核一次定级", 运行中: "定级中", 失败: "失败", 完成: "完成" }[u.状态] || u.状态}</span></div>
    <h3>${u.名称}</h3><div class="sub">${u.行数} 行 · ${u.列数} 列；点击继续</div></div>`).join("")}
   <div class="tcard new" id="new"><div class="plus">＋</div><div style="margin-top:6px;font-weight:650">新建任务</div><div class="sub">上传一张数据表（CSV 或 Excel）</div></div></div>`;
  $$(".tcard[data-k]").forEach(a => a.onclick = () => { S.page = "overview"; setTask(a.dataset.k) });
  $$(".tcard[data-up]").forEach(a => a.onclick = () => openNew(a.dataset.up)); $("#new").onclick = () => openNew();
  if (!canRunAny()) return;
  let src = null;
  $$(".tcard[data-k]").forEach(c => { c.draggable = true;                        // 拖动排序：放到哪张卡片上，就排在它的位置
    c.ondragstart = e => { src = c.dataset.k; c.classList.add("drag"); e.dataTransfer.effectAllowed = "move" }; c.ondragend = () => c.classList.remove("drag");
    c.ondragover = e => { e.preventDefault(); if (c.dataset.k != src) c.classList.add("over") }; c.ondragleave = () => c.classList.remove("over");
    c.ondrop = async e => { e.preventDefault(); c.classList.remove("over"); const dst = c.dataset.k; if (!src || src == dst) return;
      const a = TASKS.filter(k => k != src), after = TASKS.indexOf(src) < TASKS.indexOf(dst); a.splice(a.indexOf(dst) + (after ? 1 : 0), 0, src); TASKS = a; render();
      try { await api("/api/order", { 顺序: TASKS }) } catch (err) { alert(err.message) } } });
  $$("[data-del]").forEach(b => b.onclick = async e => { e.stopPropagation(); const k = b.dataset.del, nm = ALL[k] ? ALL[k].名称 : ((S.srv.上传任务 || []).find(u => u.任务 == k) || {}).名称 || k;
    if (!confirm(`删除任务“${nm}”？\n相关文件会移到 runtime/回收站/，需要时可以手动恢复。`)) return;
    try { await api("/api/delete", { 任务: k }); TASKS = TASKS.filter(x => x != k); delete ALL[k]; S.srv = await api("/api/status"); if (S.task == k) { S.page = "tasks"; setTask(TASKS.find(x => ALL[x])) } else render() } catch (err) { alert(err.message) } });
}

/* ---------------- 新建任务向导：上传表格 → 确认字段目录 → 全流程进度 ---------------- */
const UPSTEP = ["上传表格", "确认字段目录", "定级进度"], ROLEC = { 候选字段: "b", 保护对象: "r", 不参与: "" };
async function api(path, body, raw) {
  const r = await fetch(path, body === undefined ? {} : { method: "POST", body: raw ? body : JSON.stringify(body) }); const j = await r.json(); if (j.错误) throw new Error(j.错误); return j;
}
async function openNew(id) {
  clearInterval(S.upt); S.up = { id: id || null, step: 1, err: "" }; S.modal = null;
  if (id) { const u = await api("/api/upload?任务=" + id); Object.assign(S.up, { info: u.信息, prof: u.画像 });
    if (u.信息.状态 == "待起草") return draftNow();
    if (u.信息.状态 == "待确认") { useDraft(u); S.up.step = 2 } else S.up.step = 3 }
  wizard(); if (S.up.step == 3) watchRun();
}
function useDraft(u) {
  const prof = Object.fromEntries(u.画像.map(p => [p.字段, p])), src = u.目录 || u.草稿.字段;
  S.up.rows = src.map(r => Object.assign({ 角色: r.建议角色 }, r, { 画像: prof[r.字段] })); S.up.ts = u.草稿.时间序列; S.up.draft = u.草稿;
}
async function draftNow() {
  S.up.step = 2; S.up.loading = true; wizard();
  try { await api("/api/draft", { 任务: S.up.id, 说明: S.up.note || "" }) } catch (e) { if (!/已有作业/.test(e.message)) { S.up.err = e.message; S.up.loading = false; return wizard() } }
  clearInterval(S.upt); S.upt = setInterval(async () => { const s = await api("/api/status"); S.srv = s; if (s.作业.状态 == "运行中") return;
    clearInterval(S.upt); const u = await api("/api/upload?任务=" + S.up.id); S.up.loading = false;
    if (!u.草稿) { S.up.err = s.作业.日志 || "起草失败"; return wizard() } useDraft(u); wizard() }, 1500);
}
function watchRun() {
  clearInterval(S.upt); const tick = async () => { const u = await api("/api/upload?任务=" + S.up.id); S.up.prog = u.进度; S.up.info = u.信息; S.up.fr = u.一次定级;
    if ($("#wz")) wizard();
    if (u.进度 && u.进度.状态 != "运行中" && u.信息.状态 != "运行中") clearInterval(S.upt) };
  tick(); S.upt = setInterval(tick, 2000);
}
function wizard() {
  const U = S.up; if (!U) { $("#modal").innerHTML = ""; return }
  const head = `<h2>${icon("plus")}新建定级任务<span class="x" id="wx">×</span></h2><div class="wsteps">${UPSTEP.map((s, i) => `<span class="${i + 1 == U.step ? "on" : i + 1 < U.step ? "done" : ""}"><i>${i + 1 < U.step ? "✓" : i + 1}</i>${s}</span>`).join("<b></b>")}</div>${U.err ? `<div class="box r" style="margin:10px 0">${U.err}</div>` : ""}`;
  let body = "";
  if (U.step == 1) body = `<label>任务名称</label><input id="nt" placeholder="例如：某业务系统数据定级" value="${U.title || ""}">
    <label>数据表（CSV 或 Excel，第一行为列名，每行一条记录）</label><input type="file" id="nf" accept=".csv,.xlsx,.xlsm">
    <label>这份数据是什么（可选，帮助大模型理解列名）</label><textarea id="nn" rows="2" placeholder="例如：某省电网逐小时运行与市场数据">${U.note || ""}</textarea>
    <label>规则库</label><select><option>GB/T 43697 数据安全技术 数据分类分级规则</option></select>
    <div class="box" style="margin-top:14px;font-size:12.5px">${icon("bot")} 上传后，大模型根据列名和示例值起草字段目录（中文名、说明、类别、公开情况，并建议哪些是保护对象）；你确认后开始定级。全流程在后台运行，自动选择显卡或处理器。</div>
    <div class="act"><button class="btn o" id="wc">取消</button><button class="btn" id="wgo" ${canUpload() ? "" : "disabled"}>${U.busy ? "正在上传…" : "上传并读取"}</button></div>${canUpload() ? "" : '<div class="sub" style="text-align:right;margin-top:6px">当前为演示方式，不能新建任务</div>'}`;
  else if (U.step == 2 && U.loading) body = `<div class="empty" style="padding:50px 0">${icon("bot")} 大模型正在根据列名和示例值起草字段目录…</div>`;
  else if (U.step == 2) { const n = k => U.rows.filter(r => r.角色 == k).length;
    body = `<div class="wsum"><span>${icon("folder")}${U.info.原文件名}</span><span>${U.info.行数} 行 · ${U.info.列数} 列</span><span>起草模型 ${U.draft.模型}</span><label class="ck"><input type="checkbox" id="wts" ${U.ts ? "checked" : ""}> 各行按时间顺序排列</label><label class="ck">复核方式 <select id="wrv" style="width:auto;padding:3px 6px"><option ${U.rv != "大模型" ? "selected" : ""} value="人工">人工（之后在一次定级页修改）</option><option ${U.rv == "大模型" ? "selected" : ""} value="大模型">另一个大模型复核</option></select></label><label class="ck">计算设备 <select id="wdev" style="width:auto;padding:3px 6px"><option ${U.dev != "处理器" ? "selected" : ""}>自动选择</option><option ${U.dev == "处理器" ? "selected" : ""}>处理器</option></select></label>
      <span class="cnt" id="wcnt">候选字段 <b>${n("候选字段")}</b> · 保护对象 <b class="red">${n("保护对象")}</b> · 不参与 <b>${n("不参与")}</b></span></div>
      ${U.draft.提示 ? `<div class="box a" style="margin:4px 0 8px">${U.draft.提示}</div>` : ""}<div class="sub" style="margin:2px 0 8px">大模型的草稿只是建议。请重点核对<b>公开情况</b>和<b>角色</b>：保护对象是不应被无权者获取、需要防止被其他字段推断出来的数据。</div>
      <div class="scroll" style="max-height:52vh"><table class="wtab"><tr><th>列名</th><th>类型 · 示例</th><th>中文名</th><th>类别</th><th>公开情况</th><th>角色</th><th>说明</th></tr>
      ${U.rows.map((r, i) => `<tr><td><code>${r.字段}</code></td><td><span class="tag">${r.类型}</span> <span class="sub">${(r.画像.示例 || []).slice(0, 2).join("，")}</span></td>
        <td><input data-r="${i}" data-f="中文名" value="${r.中文名}"></td><td>${sel(i, "类别", ["行业数据", "个人信息", "公共数据", "组织数据"], r.类别)}</td><td>${sel(i, "公开情况", ["已公开", "有条件开放", "未公开"], r.公开情况)}</td>
        <td>${["时间", "文本"].includes(r.类型) ? '<span class="tag">不参与</span>' : sel(i, "角色", ["候选字段", "保护对象", "不参与"], r.角色, "role " + ROLEC[r.角色])}${r.角色 != r.建议角色 ? ' <span class="tag a" title="与大模型建议不同">已改</span>' : ""} ${r.理由 ? q("大模型建议：" + r.建议角色 + "。" + r.理由) : ""}</td>
        <td><input data-r="${i}" data-f="说明" value="${(r.说明 || "").replace(/"/g, "&quot;")}"></td></tr>`).join("")}</table></div>
      <div class="act"><button class="btn o" id="wc">稍后再说</button><button class="btn" id="wrun">${U.busy ? "正在提交…" : "确认目录，开始定级"}</button></div>`; }
  else { const P = U.prog, ic = { 等待: "○", 进行中: "◐", 完成: "✓", 失败: "✕" };
    body = !P ? `<div class="empty" style="padding:40px 0">正在启动…</div>` : `<div class="wsum"><span>${icon("folder")}${U.info.名称}</span><span>计算设备：${P.设备 || "选择中"}</span><span>已用 ${P.用时秒 || 0} 秒</span><span class="tag ${P.状态 == "完成" ? "g" : P.状态 == "失败" ? "r" : "a"}">${P.状态}</span></div>
      <div class="wprog">${P.步骤.map(s => `<div class="${{ 完成: "done", 进行中: "on", 失败: "bad" }[s.状态] || ""}"><i>${ic[s.状态]}</i><b>${s.名称}</b><span>${s.说明 || ""}</span></div>`).join("")}</div>
      <div class="wlog">${P.日志.slice(-10).map(l => `<div>${l.replace(/</g, "&lt;")}</div>`).join("")}</div>
      <div class="act"><button class="btn o" id="wc">关闭（后台继续）</button>${P.状态 == "完成" ? '<button class="btn" id="wopen">查看定级结果</button>' : ""}</div>`; }
  const sk = $("#wz .scroll") ? $("#wz .scroll").scrollTop : 0;
  $("#modal").innerHTML = `<div class="mask"><div class="dlg" id="wz" style="width:min(1180px,95vw)">${head}${body}</div></div>`;
  if ($("#wz .scroll")) $("#wz .scroll").scrollTop = sk;
  $("#wx").onclick = () => { clearInterval(S.upt); S.up = null; wizard(); if (S.page == "tasks") render() }; if ($("#wc")) $("#wc").onclick = $("#wx").onclick;
  if ($("#wgo")) $("#wgo").onclick = async () => { const f = $("#nf").files[0]; U.title = $("#nt").value.trim(); U.note = $("#nn").value.trim(); if (!f) { U.err = "请选择数据表文件"; return wizard() }
    U.busy = true; U.err = ""; wizard();
    try { const j = await api(`/api/upload?name=${encodeURIComponent(f.name)}&title=${encodeURIComponent(U.title || f.name.replace(/\.\w+$/, ""))}`, await f.arrayBuffer(), true); U.id = j.任务; U.info = { 原文件名: f.name, 行数: j.行数, 列数: j.列数 }; U.prof = j.画像; U.busy = false; draftNow() }
    catch (e) { U.busy = false; U.err = e.message; wizard() } };
  $$("#wz [data-r]").forEach(e => e.onchange = () => { const r = U.rows[+e.dataset.r]; r[e.dataset.f] = e.value; if (e.dataset.f == "角色") wizard(); else cnt() });
  if ($("#wts")) $("#wts").onchange = e => U.ts = e.target.checked; if ($("#wdev")) $("#wdev").onchange = e => U.dev = e.target.value; if ($("#wrv")) $("#wrv").onchange = e => U.rv = e.target.value;
  if ($("#wrun")) $("#wrun").onclick = async () => { U.busy = true; U.err = ""; wizard();
    try { await api("/api/start", { 任务: U.id, 目录: U.rows.map(r => ({ 字段: r.字段, 中文名: r.中文名, 类别: r.类别, 公开情况: r.公开情况, 说明: r.说明, 角色: r.角色 })), 时间序列: U.ts, 设备: U.dev || "自动", 复核方式: U.rv || "人工", 说明: U.note || "" }); U.busy = false; U.step = 3; U.prog = null; wizard(); watchRun() }
    catch (e) { U.busy = false; U.err = e.message; wizard() } };
  if ($("#wopen")) $("#wopen").onclick = async () => { const k = U.id; ALL[k] = await (await fetch("../samples/" + k + ".json?" + Date.now())).json(); if (!TASKS.includes(k)) TASKS.push(k);
    S.srv = await api("/api/status"); clearInterval(S.upt); S.up = null; wizard(); S.page = "overview"; setTask(k) };
  function cnt() { const n = k => U.rows.filter(r => r.角色 == k).length; if ($("#wcnt")) $("#wcnt").innerHTML = `候选字段 <b>${n("候选字段")}</b> · 保护对象 <b class="red">${n("保护对象")}</b> · 不参与 <b>${n("不参与")}</b>` }
}
const sel = (i, f, opts, v, cls = "") => `<select data-r="${i}" data-f="${f}" class="${cls}">${opts.map(o => `<option ${o == v ? "selected" : ""}>${o}</option>`).join("")}</select>`;
const canUpload = () => S.srv.完整方式;

/* ---------------- 总体概览 ---------------- */
function capMatrix() {
  const rs = RECV3(); return `<table><tr><th>保护对象</th><th>等级</th>${rs.map(r => `<th style="text-align:center">${rt(r.名称, r.级)}<div class="sub">判定线 ${r.判定线}</div></th>`).join("")}</tr>${sens().map(f => `<tr><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td>${rs.map(r => { const x = capOf(r.名称, f.中文名);
    if (!x) return `<td style="text-align:center"><span class="cellv n">有权获取</span></td>`; const o = v => v > x.判定线;
    return `<td style="text-align:center"><span class="cpair"><span class="cellv ${o(x.定级前) ? "r" : "g"}">${f2(x.定级前)}</span><span class="sub">→</span><span class="cellv ${o(x.定级后) ? "r" : "g"}">${f2(x.定级后)}</span>${isRes(r.名称, f.中文名) ? `<span class="qa">${q("仅凭法定公开的信息即可推出，调整候选字段的等级不起作用。")}</span>` : ""}</span></td>` }).join("")}</tr>`).join("")}</table>`;
}
function soloOver(f) {                                 // 与单字段页同一口径：判定线 0.7，有越权接收方，且公开基底本身未过线
  return sens().some((s, t) => { const b = hasBase() ? D.展示[s.中文名].背景明细[0].背景精度[0] : 0;
    return b < 0.7 && f.单独精度[t] >= 0.7 && RECV3().some(r => f.一次等级 <= r.级 && s.一次等级 > r.级) });
}
function pOverview() {
  const c = cand(), up = c.filter(f => f.二次等级 > f.一次等级), b0 = overCells("定级前"), b1 = overCells("定级后");
  const steps = [["一次定级", `${D.字段.length} 个字段`, "grade1", "layers"], ["单独推断", `${c.filter(soloOver).length} 个字段单独可过线`, "single", "risk"], ["背景知识下的风险", `${c.filter(f => Math.max(...f.M) >= D.参数.直接定级线).length} 个字段 M 达到直接定级线`, "aggr", "nodes"], ["越线组合", `${D.一次定级下的越线.length} 个最小越线组合`, "combos", "combo"], ["二次定级", `调高 ${up.length} 个字段`, "regrade", "tune"], ["定级效果", b1 ? `${b1} 处仍越线` : "无越线", "effect", "check"]];
  $("#main").innerHTML = `<div class="kpis">${kpi(icon("layers"), "b", "字段", D.字段.length, `候选 ${c.length} · 保护对象 ${D.敏感.length}${hasBase() ? " · 公开基底 " + (D.字段.length - c.length - D.敏感.length) : ""}`)}
   ${kpi(icon("risk"), "r", "越线的“接收方 × 保护对象” " + q(TIP.V + " " + TIP.line), `<span class="red">${b0}</span> <small>→</small> <span class="${b1 ? "red" : "green"}">${b1}</span>`, "一次定级 → 二次定级")}
   ${kpi(icon("nodes"), "a", "最小越线组合 " + q(TIP.combo), `<span class="red">${D.一次定级下的越线.length}</span> <small>→</small> <span class="green">${D.二次定级后的越线.length}</span>`, `组合规模 ≤ ${Math.max(0, ...D.一次定级下的越线.map(x => x.组合.length)) || D.组合上限}`)}
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

/* ---------------- 颜色：风险随数值逐渐加深（蓝 → 黄 → 橙 → 红） ---------------- */
const STOPS = [[0, [96, 165, 250]], [0.3, [59, 130, 246]], [0.45, [245, 184, 61]], [0.62, [249, 115, 22]], [0.8, [229, 72, 77]], [1, [185, 28, 28]]];
function riskColor(v) { v = Math.max(0, Math.min(1, v)); for (let k = 1; k < STOPS.length; k++) if (v <= STOPS[k][0]) { const [a, ca] = STOPS[k - 1], [b, cb] = STOPS[k], r = (v - a) / (b - a || 1); return `rgb(${ca.map((x, i) => Math.round(x + (cb[i] - x) * r)).join(",")})` } return "rgb(185,28,28)" }
const riskBar = v => `linear-gradient(90deg,#93c5fd,${riskColor(v)})`;
const GAIN = "repeating-linear-gradient(135deg,#8b5cf6 0 7px,#b197fc 7px 11px)", GAINC = "#7c3aed";
const LEG = { top: 0, right: 0, selectedMode: true, itemWidth: 22, itemHeight: 11, itemGap: 14, padding: [6, 12], backgroundColor: "rgba(241,245,252,.95)", borderColor: "rgba(120,140,175,.3)", borderWidth: 1, borderRadius: 10, textStyle: { fontSize: 12, fontWeight: 600, color: "#2a3852" }, inactiveColor: "#b8c2d4" };

/* ---------------- ② 单字段推断风险 ---------------- */
const curveOpt = (series, tc = C.gray) => ({ grid: { left: 58, right: 14, top: 14, bottom: 24 }, legend: Object.assign({}, LEG, { show: false }), tooltip: { trigger: "axis" }, xAxis: { type: "category", data: SH().真实.map((_, i) => i), name: D.横轴, nameLocation: "middle", nameGap: 8, axisLabel: { show: false }, axisTick: { show: false }, axisLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "value", scale: true, splitLine: { lineStyle: { color: C.grid } } },
  series: [{ name: "真实值", type: "line", data: SH().真实, showSymbol: false, lineStyle: { color: tc, width: 2 }, itemStyle: { color: tc }, emphasis: { focus: "series", lineStyle: { width: 3 } }, z: 2 }]
    .concat(series.map(s => ({ name: s[0], type: D.时间序列 ? "line" : "scatter", data: s[1], showSymbol: !D.时间序列, symbolSize: 4, lineStyle: { color: s[2], width: 1.6 }, itemStyle: { color: s[2], opacity: .85 }, emphasis: { focus: "series", lineStyle: { width: 3 } }, z: 3 }))) });
/* 图例做成胶囊按钮：选中时带曲线颜色的描边和光晕，点击显示或隐藏，悬停突出对应曲线 */
function chartL(el, opt) {
  const c = chart(el, opt), ser = c.getOption().series.filter(s => s.name), host = document.createElement("div"); host.className = "lgcs"; el.parentNode.insertBefore(host, el);
  host.innerHTML = ser.map(s => `<span class="lgc on" data-s="${s.name}" style="--c:${(s.lineStyle && s.lineStyle.color) || (s.itemStyle && s.itemStyle.color) || "#64748b"}"><i></i>${s.name}</span>`).join("");
  host.querySelectorAll(".lgc").forEach(b => { b.onclick = () => { c.dispatchAction({ type: "legendToggleSelect", name: b.dataset.s }); b.classList.toggle("on") };
    b.onmouseenter = () => c.dispatchAction({ type: "highlight", seriesName: b.dataset.s }); b.onmouseleave = () => c.dispatchAction({ type: "downplay", seriesName: b.dataset.s }) });
  return c;
}
const legendHint = `<span class="sub" style="display:inline-flex;gap:4px;align-items:center">${icon("eye")}点击图例可显示或隐藏曲线，悬停可突出一条</span>`;
const SLINE = 0.7;   // 单字段判定线：不分接收方，一律 0.7
function relLine(f) { return RECV3().some(r => f.一次等级 <= r.级 && T().一次等级 > r.级) ? SLINE : null }
const baseNames = () => D.字段.filter(f => f.角色 == "公开基底").map(f => f.中文名);
const BASE0 = () => hasBase() ? (((SH().背景明细 || [])[0] || {}).背景精度 || [0])[0] : 0;      // 仅凭公开基底的推断精度
const glow = v => riskColor(v).replace("rgb(", "rgba(").replace(")", ",.3)");
/* 一个字段的作用（单独作用 + 背景增益）合成一段，带毛玻璃描边和微光 */
const fseg = (own, gain, v, plain) =>                   // 颜色只按该字段自身那一段的长度，不把背景和背景增益算进去
  own + gain < 0.003 ? "" : `<span class="fs${plain ? " pl" : ""}" style="width:${(own + gain) * 100}%;--gl:${glow(v)}"><i style="width:${own / (own + gain) * 100}%;background:${riskBar(own)}"></i>${gain > 0.003 ? `<i style="flex:1;background:${GAIN}"></i>` : ""}</span>`;
function pSingle() {
  const sh = SH(), b0 = BASE0(), bOver = hasBase() && b0 >= SLINE, rows = cand().map(f => ({ f, x: sh.单字段.find(s => s.字段 == f.中文名), line: relLine(f) })).sort((a, b) => b.x.精度 - a.x.精度);
  rows.forEach(r => r.inc = Math.max(0, r.x.精度 - b0));
  const pass = r => r.line != null && !bOver && r.x.精度 >= r.line, verdict = r => r.line == null ? '<span class="tag">无越权接收方</span>' : bOver ? '<span class="tag a">公开基底已过线</span>' : pass(r) ? '<span class="tag r">单独过线</span>' : '<span class="tag g">单独不过线</span>';
  if (S.sel == null || !rows[S.sel]) S.sel = 0; const cur = rows[S.sel], pass7 = rows.filter(pass), topInc = rows.slice().sort((a, b) => b.inc - a.inc)[0];
  const barOf = (r, plain) => `<div class="fbar">${b0 > .003 ? `<i class="bg" style="width:${b0 * 100}%"></i>` : ""}${fseg(r.inc, 0, r.x.精度, plain)}${r.line != null ? `<b style="left:${r.line * 100}%"></b>` : ""}</div>`;
  const note = !hasBase() ? "" : `<div class="box ${bOver ? "a" : ""}" style="margin-bottom:14px">${icon(bOver ? "risk" : "layers")} 本任务的推断都包含公开基底（${baseNames().join("、")}）。仅凭公开基底推断“${T().中文名}”的精度为 <b>${f3(b0)}</b>${bOver ? `，<b>已超过判定线 ${SLINE}</b>：任何接收方都能推出这一项，调整候选字段的等级不起作用` : ""}。下表灰色部分来自公开基底，彩色部分才是字段自己的作用，与“聚合推断风险”页 K = 0 时的 M 一致。</div>`;
  $("#main").innerHTML = objBar() + `<div class="kpis">${kpi(icon("risk"), pass7.length ? "r" : "g", "单独可过线的字段", pass7.length, `单字段判定线 ${SLINE}，不分接收方` + (bOver ? "；公开基底已过线，不计入" : pass7.length ? "；" + pass7.slice(0, 3).map(r => r.f.中文名).join("、") : "；没有字段单独达到"))}
     ${hasBase() ? kpi(icon("target"), "a", "比公开基底提高最多", `<span style="color:${riskColor(topInc.inc)}">＋${f3(topInc.inc)}</span>`, topInc.f.中文名 + `：${f3(b0)} → ${f3(topInc.x.精度)}`) : kpi(icon("target"), "a", "单字段最高推断精度", `<span style="color:${riskColor(rows[0].x.精度)}">${f3(rows[0].x.精度)}</span>`, rows[0].f.中文名)}
     ${hasBase() ? kpi(icon("layers"), bOver ? "r" : "b", "仅凭公开基底", `<span style="color:${riskColor(b0)}">${f3(b0)}</span>`, baseNames().join("、")) : kpi(icon("layers"), "b", "推断精度 0.5 以上的字段", rows.filter(r => r.x.精度 >= .5).length, `共 ${rows.length} 个候选字段`)}</div>
   ${note}<div class="split"><div class="left card"><h3>${icon("risk")}每个候选字段单独推断“${T().中文名}” ${q(TIP.V + (hasBase() ? " 本任务的推断都包含公开基底。" + TIP.base : ""))}<span class="r">点击一行查看推断曲线</span></h3>
     <div class="scroll" data-sk="s1" style="max-height:calc(100vh - 340px)"><table><tr><th>#</th><th>字段</th><th>一次等级</th><th>可获取的接收方</th><th style="width:34%">单独推断精度${hasBase() ? "（含公开基底）" : ""}</th><th>与判定线比</th></tr>
     ${rows.map((r, k) => `<tr class="c ${k == S.sel ? "pick" : ""}" data-i="${k}"><td class="sub">${k + 1}</td><td class="nw"><b>${r.f.中文名}</b></td><td>${lv(r.f.一次等级)}</td><td>${recvTags(r.f.一次等级)}</td>
       <td><div class="hbar">${barOf(r, true)}<span class="num" style="min-width:${hasBase() ? 104 : 44}px;text-align:right"><b style="color:${riskColor(r.x.精度)}">${f3(r.x.精度)}</b>${hasBase() ? ` <small class="sub">＋${f3(r.inc)}</small>` : ""}</span></div></td>
       <td>${verdict(r)}</td></tr>`).join("")}</table></div>
     <div class="legend" style="margin-top:8px">${hasBase() ? `<span><i style="background:#c3cddd"></i>公开基底</span><span><i style="background:linear-gradient(90deg,#60a5fa,#f5b83d,#e5484d)"></i>字段自己的作用，颜色随推断精度加深</span>` : `<span><i style="background:linear-gradient(90deg,#60a5fa,#f5b83d,#f97316,#e5484d)"></i>颜色随推断精度逐渐加深</span>`}<span><i style="background:#0f1a2e;width:2px"></i>单字段判定线 ${SLINE}（不分接收方）</span></div></div>
    <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${S.sel + 1} 行</div><h3 style="font-size:18px">${cur.f.中文名}<span class="r">${lv(cur.f.一次等级)}</span></h3>
     <div class="box" style="background:linear-gradient(140deg,rgba(255,255,255,.9),rgba(241,245,252,.85))"><div class="sub">单独推断“${T().中文名}”${hasBase() ? "（含公开基底）" : ""}</div><div class="big" style="color:${riskColor(cur.x.精度)}">${f3(cur.x.精度)}</div>
      <div style="margin:8px 0 6px">${barOf(cur)}</div>
      <div class="sub">${hasBase() ? `公开基底 ${f3(b0)} ＋ 该字段 ${f3(cur.inc)}；` : ""}${cur.line == null ? "能拿到该字段的接收方都有权获取保护对象" : bOver ? "公开基底已过线" : `单字段判定线 ${cur.line}，${pass(cur) ? "单独过线" : "单独不过线"}`}</div></div>
     <div class="kv" style="margin-top:8px"><span>可获取的接收方</span><span>${recvTags(cur.f.一次等级)}</span></div>
     <h3 style="margin-top:12px">${icon("eye")}推断值与真实值</h3><div id="cv1" style="height:260px"></div><div class="sub" style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><span>${D.时间序列 ? "留出数据的前 240 个时段" : "留出数据，按真实值从小到大排列"}${hasBase() ? "；推断时含公开基底" : ""}</span>${legendHint}</div></div></div>`;
  bindObj(); pick("tr.c", r => S.sel = +r.dataset.i);
  chartL($("#cv1"), curveOpt([["仅凭“" + cur.f.中文名 + "”" + (hasBase() ? "（含公开基底）" : "") + "的推断值", cur.x.值, C.red]]));
}

/* ---------------- ③ 聚合推断风险 ---------------- */
function kSlider(id, max, val) {                    // 横向液态玻璃选择器：玻璃块可拖动，松开后吸附到最近的 K
  return `<div class="kmini"><span class="kl">背景字段数上限 K ${q(TIP.M)}</span><div class="hsel" id="${id}" data-max="${max}" style="--n:${max + 1}"><div class="hpill" style="transform:translateX(${val * 100}%)"></div>${Array.from({ length: max + 1 }, (_, k) => `<a data-kt="${k}" class="${k == val ? "on" : ""} ${k == kUse() ? "use" : ""}" ${k == kUse() ? 'title="二次定级所用的 K"' : ""}>K = ${k}</a>`).join("")}</div></div>` }
function bindHsel(el, onMove, onDone) {               // 拖动跟手、悬停预览、松开吸附
  const n = +el.dataset.max + 1, pill = el.querySelector(".hpill"); let drag = null;
  const kAt = x => { const r = el.getBoundingClientRect(); return Math.max(0, Math.min(n - 1, Math.floor((x - r.left - 4) / ((r.width - 8) / n)))) };
  const place = (k, smooth = true) => { pill.style.transition = smooth ? "" : "none"; pill.style.transform = `translateX(${k * 100}%)`; el.querySelectorAll("a").forEach(a => a.classList.toggle("on", +a.dataset.kt == k)) };
  el.onpointerdown = e => { const r = el.getBoundingClientRect(), w = (r.width - 8) / n; drag = { k: kAt(e.clientX), x0: e.clientX, p0: kAt(e.clientX) * w, w, moved: false }; el.setPointerCapture(e.pointerId); el.classList.add("drag") };
  el.onpointermove = e => { if (!drag) return; const dx = e.clientX - drag.x0; if (Math.abs(dx) > 3) drag.moved = true; if (!drag.moved) return;
    const px = Math.max(0, Math.min((n - 1) * drag.w, drag.p0 + dx)); pill.style.transition = "none"; pill.style.transform = `translateX(${px / drag.w * 100}%)`; const k = Math.round(px / drag.w); if (k != drag.k) { drag.k = k; el.querySelectorAll("a").forEach(a => a.classList.toggle("on", +a.dataset.kt == k)); onMove(k) } };
  el.onpointerup = e => { if (!drag) return; el.classList.remove("drag"); const k = drag.moved ? drag.k : kAt(e.clientX); drag = null; place(k); onMove(k); onDone(k) };
}
function kCard() {                                    // 背景预算 K 的选定：默认折叠，点开看风险靠前字段的平均 M 随 K 的变化
  const ks = D.K选择 || {}, k = kUse(), auto = ks.方式 == "自动", b = ks.增量最大, open = auto && S.kOpen;
  const head = `<div class="kh" ${auto ? 'id="kt"' : ""}><span class="kn">${icon("tune")}背景预算 K</span><span class="kuse">${auto ? "自动选定" : "手动指定"} K = ${k}</span>
    <span class="ks">${auto ? (ks.平均M.length > 3 ? `K 从 2 到 3 仍有字段增加 ${f3(b.K3 - b.K2)}，取 3` : ks.测试方式 == "精确" ? "K 从 2 到 3 增量很小，取 2" : "K 从 1 到 2 已饱和，取 2") : "在“本页导览与参数”中可改回自动"}</span>
    ${auto ? `<span class="kx">${open ? "收起" : "展开选定过程"}<i class="${open ? "up" : ""}">⌄</i></span>` : ""}</div>`;
  if (!open) return `<div class="card kcard fold">${head}</div>`;
  return `<div class="card kcard">${head}
    <div class="kc"><div id="kch"></div><div class="kt"><p>${ks.依据} ${q(TIP.Ksel + (ks.测试方式 && ks.测试方式 != "精确" ? `本任务字段较多，K = 3 在 K = 2 的最危险背景上逐个加入一个字段试算，新训练 ${ks.新训练组合数} 个组合。` : ""))}</p>
      ${b ? `<div class="kb"><span class="sub">K 从 2 到 3 增加最多</span><b>${b.字段}</b><span class="sub">→ ${b.保护对象}</span><span class="num">${f3(b.K2)} → <b style="color:${b.K3 - b.K2 >= ks.阈值.单个 ? GAINC : "inherit"}">${f3(b.K3)}</b></span>${b.背景.length ? `<span class="ws">${b.背景.map(n => `<span class="bgt">${n}</span>`).join("<b>＋</b>")}</span>` : ""}</div>` : ""}</div></div></div>` }
function kChart() {
  const ks = D.K选择 || {}, m = ks.平均M; if (!m || !$("#kch")) return; const k = kUse();
  chart($("#kch"), { grid: { left: 44, right: 14, top: 22, bottom: 26 }, tooltip: { trigger: "axis", valueFormatter: v => f3(v) },
    xAxis: { type: "category", data: m.map((_, i) => "K = " + i), axisTick: { show: false }, axisLabel: { fontSize: 12, fontWeight: 650, color: "#2a3852" } },
    yAxis: { type: "value", min: v => Math.max(0, Math.floor((v.min - 0.05) * 20) / 20), splitLine: { lineStyle: { color: C.grid } }, axisLabel: { fontSize: 11 } },
    series: [{ name: "风险靠前字段的平均 M", type: "bar", barWidth: 30, data: m.map((v, i) => ({ value: v, itemStyle: { color: i == k ? "#8b5cf6" : i > k ? "#d9cffb" : "#c7d4ea", borderRadius: [6, 6, 0, 0] } })),
      label: { show: true, position: "top", fontSize: 11.5, fontWeight: 700, formatter: p => p.dataIndex ? "＋" + f3(m[p.dataIndex] - m[p.dataIndex - 1]) : f3(p.value) } }] }) }
function decomp(cd, k) { const bg = cd.背景精度[k], m = cd.M[k], m0 = cd.M[0], own = Math.min(m0, m), gain = Math.max(0, m - m0);
  return { bg, m, m0, own, gain, all: cd.合并精度[k], names: cd.背景[k] } }
const CURV = {};                                       // 越线组合的推断曲线，按任务懒加载
async function loadCurv(k) { CURV[k] = null; try { CURV[k] = await (await fetch("../samples/" + k + "_组合曲线.json?" + Date.now())).json() } catch (e) { CURV[k] = {} } if ((S.page == "aggr" || S.page == "combos") && S.task == k) render() }
const CTRUE = "#1e293b", CREST = "#0fa5a0";            // 真实值、组合去掉该字段
function pAggr() {
  const sh = SH(), det = sh.背景明细 || [], nK = det.length ? det[0].M.length : 1; S.K = Math.min(S.K, nK - 1); const K = S.K, DL = D.参数.直接定级线;
  const rows0 = cand().map(f => ({ f, d: det.find(x => x.字段 == f.中文名) })).filter(r => r.d), amp = (r, k = K) => r.d.M[k] - r.d.M[0];
  const fl = { 全部: r => 1, 有背景增益: r => amp(r) > 0.05, 达到直接定级线: r => r.d.M[K] >= DL };
  const rows = rows0.filter(fl[S.afilter] || fl.全部).sort((a, b) => b.d.M[K] - a.d.M[K]);
  if (S.sel == null || !rows[S.sel]) S.sel = 0; const cur = rows[S.sel] || rows0[0], cd = cur.d, gcur = sh.背景增益.find(x => x.字段 == cur.f.中文名), me = cur.f.中文名;
  if (S.rk == null || S.rk >= nK) S.rk = K;
  const ov = rows0.slice().sort((a, b) => b.d.M[nK - 1] - a.d.M[nK - 1]).slice(0, 12);
  $("#main").innerHTML = objBar() + `<div class="card"><h3>${icon("nodes")}全部候选字段的推断风险总览 ${q(TIP.M)}<span class="r">按 K = ${nK - 1} 时的 M 排序，前 ${ov.length} 个</span></h3>
     <div id="gb" style="height:${36 + ov.length * 34}px"></div>
     <div style="display:flex;align-items:flex-end;gap:16px;margin-top:4px"><div class="legend" style="flex:1"><span><i style="background:linear-gradient(90deg,#60a5fa,#f5b83d,#e5484d)"></i>单独作用（K = 0），颜色随数值加深</span><span><i style="background:${GAIN}"></i>背景增益</span><span><i style="background:#0f1a2e;width:2px"></i>直接定级线 ${DL}</span></div>
      <div class="kbox" style="min-width:160px;padding:9px 14px"><div class="sub">达到直接定级线</div><div class="v" style="font-size:20px"><span id="kd"></span> 个字段</div></div>${kSlider("K", nK - 1, K)}</div></div>
${kCard()}
   <div class="split"><div class="left card"><h3>${icon("risk")}考虑背景知识的字段推断风险（K = ${K}）<span class="r"><span class="chips">${Object.keys(fl).map(k => `<span class="chip ${k == S.afilter ? "on" : ""}" data-af="${k}">${k} ${rows0.filter(fl[k]).length}</span>`).join("")}</span></span></h3>
     <div class="scroll" data-sk="a1" style="max-height:calc(100vh - 260px)"><table class="agt"><tr><th>#</th><th>字段</th><th>一次等级</th><th>可获取的接收方</th><th style="width:21%">单独推断 ＋ 背景增益 ＝ M</th><th>M</th><th class="nw">结论</th></tr>
     ${rows.map((r, k) => { const x = decomp(r.d, K); return `<tr class="c ${k == S.sel ? "pick" : ""}" data-i="${k}"><td class="sub">${k + 1}</td><td class="nw"><b>${r.f.中文名}</b></td><td>${lv(r.f.一次等级)}</td><td>${recvTags(r.f.一次等级)}</td>
       <td><div class="hbar"><div class="bar2"><i class="s" style="width:${x.own * 100}%;background:${riskBar(x.own)}"></i>${x.gain > 0.005 ? `<i class="e" style="left:${x.own * 100}%;width:${x.gain * 100}%;background:${GAIN}"></i>` : ""}<b style="left:${DL * 100}%"></b></div>
       <span class="num" style="width:118px;text-align:right;font-size:12.5px">${f2(x.m0)}${x.gain > 0.005 ? ` <span style="color:${GAINC};font-weight:700">＋${f2(x.gain)}</span>` : x.m < x.m0 - .005 ? ` <span class="sub">−${f2(x.m0 - x.m)}</span>` : ""}</span></div></td>
       <td class="num"><b style="color:${riskColor(x.m)}">${f3(x.m)}</b></td><td>${x.m >= DL ? '<span class="tag r">直接定级</span>' : x.gain > 0.05 ? '<span class="tag a">背景放大</span>' : '<span class="tag">增益有限</span>'}</td></tr>` }).join("") || `<tr><td colspan="7" class="empty">没有符合条件的字段</td></tr>`}</table></div>
     <div class="legend" style="margin-top:8px"><span><i style="background:linear-gradient(90deg,#60a5fa,#f5b83d,#e5484d)"></i>单独作用（K = 0）</span><span><i style="background:${GAIN}"></i>背景增益（M − 单独作用）</span><span><i style="background:#0f1a2e;width:2px"></i>直接定级线</span></div></div>
    <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${S.sel + 1} 行</div><h3 style="font-size:18px">${me}<span class="r">${lv(cur.f.一次等级)}</span></h3>
     <div class="sub" style="margin-top:-6px;margin-bottom:10px">接收方已经掌握背景字段时，再拿到它，对“${T().中文名}”的推断能提高多少。上下拖动左侧的玻璃块切换 K。</div>
     <div style="display:flex;gap:16px;align-items:stretch"><div class="vsel" id="vsel"><div class="pill" id="pill" style="transform:translateY(${S.rk * 56}px)"></div>${cd.M.map((_, k) => `<a data-rk="${k}" class="${k == S.rk ? "on" : ""}">K = ${k}<small>${k ? "背景 ≤ " + k : "单独"}</small></a>`).join("")}</div><div style="flex:1;min-width:0" id="dec"></div></div>
     <div class="subpanel"><h3>${icon("users")}与哪些字段一起开放最危险 ${q("见证背景：在至多 K 个背景字段的全部组合中，使该字段带来的推断增益最大的那一组。它说明这个字段不宜与哪些字段一起开放给同一类接收方。凑齐后是否越线，见“越线组合”页。")}</h3>
      ${cd.M.map((m, k) => k ? `<div class="wit ${k == S.rk ? "on" : ""}" data-wk="${k}"><span class="kk">K = ${k}</span><span class="ws">${cd.背景[k].length ? cd.背景[k].map(n => `<span class="bgt">${n}</span>`).join('<b>＋</b>') : '<span class="sub">无</span>'}</span><span class="wv">背景 ${f3(cd.背景精度[k])} → 加上该字段 <b style="color:${riskColor(cd.合并精度[k])}">${f3(cd.合并精度[k])}</b></span></div>` : "").join("")}
      <div class="go2" data-go="combos">${icon("combo")}查看“${T().中文名}”的越线组合 ›</div>
      ${gcur ? `<h3 style="margin-top:14px">${icon("eye")}最危险背景下的推断值与真实值<span class="r" id="gck"></span></h3><div id="gc" style="height:230px"></div><div class="sub" style="text-align:right">${legendHint}</div>` : ""}</div></div></div>`;
  bindObj(); pick("tr.c", r => { S.sel = +r.dataset.i; S.rk = S.K; S.ci = 0 }); $$("[data-af]").forEach(a => a.onclick = () => { S.afilter = a.dataset.af; S.sel = null; render() });
  $$("[data-go]").forEach(a => a.onclick = () => go(a.dataset.go));
  const H = 56, vs = $("#vsel"), pill = $("#pill");
  let gk = null;
  const drawGain = k => {                               // 最危险背景下的推断曲线随 K 切换，重新播放加载动画
    if (!gcur || !$("#gc")) return; const cs = Array.isArray(gcur.曲线) ? gcur.曲线 : null, kk = cs ? Math.min(k, cs.length - 1) : gcur.M.length - 1; if (gk === kk) return; gk = kk;
    const cv = cs ? cs[kk] : gcur.曲线, bgn = gcur.背景[kk] || [];
    $("#gck").textContent = "K = " + kk; const old = charts.indexOf($("#gc")._c); if ($("#gc")._c) { $("#gc")._c.dispose(); if (old >= 0) charts.splice(old, 1); const lg = $("#gc").previousElementSibling; if (lg && lg.classList.contains("lgcs")) lg.remove() }
    $("#gc")._c = chartL($("#gc"), curveOpt([[bgn.length ? "只有背景（" + bgn.join("、") + "）" : "无背景", cv.背景.length ? cv.背景 : null, CREST], ["背景 + " + gcur.字段, cv.合并, C.red]].filter(s => s[1]), CTRUE)) };
  const showDec = (k, movePill = true) => { const x = decomp(cd, k); S.rk = k; if (movePill) pill.style.transform = `translateY(${k * H}px)`; $$("[data-rk]").forEach(a => a.classList.toggle("on", +a.dataset.rk == k));
    $$("[data-wk]").forEach(a => a.classList.toggle("on", +a.dataset.wk == k)); drawGain(k);
    $("#dec").innerHTML = `<div class="bgline"><span class="bl">${icon("layers")}背景字段</span>${x.names.length ? x.names.map(n => `<span class="bgt">${n}</span>`).join("") : '<span class="bgt none">无（该字段单独）</span>'}${hasBase() ? '<span class="bgt base">＋公开基底</span>' : ""}</div>
      <div class="stack">${x.bg > .003 ? `<i class="bg" style="width:${x.bg * 100}%">${x.bg >= .14 ? `<em>背景 ${f2(x.bg)}</em>` : ""}</i>` : ""}${fseg(x.own, x.gain, x.m)}</div><div class="ruler"><span>0</span><span>0.25</span><span>0.5</span><span>0.75</span><span>1</span></div>
      <div class="dgrid3"><div><span class="sw" style="background:#c3cddd"></span>只有背景<b>${f3(x.bg)}</b></div><div><span class="sw" style="background:${riskBar(x.own)}"></span>该字段单独作用<b>${f3(x.m0)}</b></div><div><span class="sw" style="background:${GAIN}"></span>背景增益<b style="color:${x.gain > .005 ? GAINC : "inherit"}">${x.m < x.m0 - .005 ? "−" + f3(x.m0 - x.m) : "＋" + f3(x.gain)}</b></div></div>
      <div class="box ${x.m >= DL ? "r" : ""}" style="margin-top:10px;display:flex;justify-content:space-between;align-items:center"><span>背景 ＋ 该字段 <b>${f3(x.all)}</b></span><span>M（K = ${k}）<b style="font-size:22px;color:${riskColor(x.m)}">&nbsp;${f3(x.m)}</b></span></div>` };
  showDec(S.rk);
  let drag = null; const maxY = (cd.M.length - 1) * H, kAt = y => Math.max(0, Math.min(cd.M.length - 1, Math.round(y / H)));      // 拖动玻璃块：跟手移动，松开后吸附到最近的 K
  vs.onpointerdown = e => { const r = vs.getBoundingClientRect(); drag = { y0: e.clientY, p0: S.rk * H, y: S.rk * H, moved: false, top: r.top }; vs.setPointerCapture(e.pointerId); pill.style.transition = "none"; vs.classList.add("drag") };
  vs.onpointermove = e => { if (!drag) return; const dy = e.clientY - drag.y0; if (Math.abs(dy) > 3) drag.moved = true; if (!drag.moved) return;
    drag.y = Math.max(0, Math.min(maxY, drag.p0 + dy)); pill.style.transform = `translateY(${drag.y}px)`; const k = kAt(drag.y); if (k != S.rk) showDec(k, false) };
  vs.onpointerup = e => { if (!drag) return; pill.style.transition = ""; vs.classList.remove("drag"); const k = drag.moved ? kAt(drag.y) : kAt(e.clientY - drag.top - 6 - H / 2); drag = null; showDec(k) };
  $$("[data-wk]").forEach(a => a.onclick = () => showDec(+a.dataset.wk));
  const decal = { symbol: "rect", dashArrayX: [1, 0], dashArrayY: [4, 3], rotation: -Math.PI / 4, color: "rgba(255,255,255,.45)" };
  const bar = chart($("#gb"), { grid: { left: 150, right: 60, top: 4, bottom: 22 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, valueFormatter: v => f3(v) }, xAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", inverse: true, data: ov.map(r => r.f.中文名), axisTick: { show: false }, axisLine: { show: false }, axisLabel: { fontSize: 12.5, color: "#2a3852", fontWeight: 600 } },
    series: [{ name: "单独作用（K = 0）", type: "bar", stack: "m", barWidth: 16, data: [], itemStyle: { borderRadius: [4, 0, 0, 4] }, animationDurationUpdate: 450, markLine: { symbol: "none", silent: true, lineStyle: { color: "#0f1a2e", type: "solid", width: 1.5 }, label: { formatter: "直接定级线", fontSize: 11 }, data: [{ xAxis: DL }] } },
      { name: "背景增益", type: "bar", stack: "m", barWidth: 16, data: [], itemStyle: { color: "#8b5cf6", decal, borderRadius: [0, 6, 6, 0] }, label: { show: true, position: "right", fontSize: 11.5, fontWeight: 700, formatter: p => "M " + f2(p.data.m) }, animationDurationUpdate: 450 }] });
  const upd = k => { $("#kd").textContent = rows0.filter(r => r.d.M[k] >= DL).length;
    bar.setOption({ series: [{ data: ov.map(r => { const x = decomp(r.d, k); return { value: x.own, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: "#93c5fd" }, { offset: 1, color: riskColor(x.own) }]) } } }) },
      { data: ov.map(r => { const x = decomp(r.d, k); return { value: x.gain, m: x.m } }) }] }) };
  kChart(); if ($("#kt")) $("#kt").onclick = () => { S.kOpen = !S.kOpen; render() }; upd(K);
  bindHsel($("#K"), upd, k => { if (k != S.K) setTimeout(() => { S.K = k; S.rk = k; render() }, 260) });
}

/* ---------------- ④ 越线组合 ---------------- */
const CMB = {};                                        // 估计得到的更大组合，键：任务|保护对象|规模
const tcode = () => T().字段, cnameOf = c => (D.字段.find(f => f.字段 == c) || {}).中文名 || c, fOf = nm => D.字段.find(f => f.中文名 == nm);
const CIRC = "①②③④⑤⑥";
function verifiedCombos() {                            // 已逐个重新训练的最小越线组合；同一组合对多类接收方越线时合并为一行
  const tn = T().中文名, m = {}, after = new Set(D.二次定级后的越线.filter(x => x.敏感数据 == tn).map(x => x.接收方 + "|" + x.组合.join("、")));
  D.一次定级下的越线.filter(x => x.敏感数据 == tn).forEach(x => { const k = x.组合.join("、"), o = m[k] = m[k] || { 组合: x.组合, 规模: x.组合.length, 精度: 0, 接收方: [], 来源: "重训", 仍成立: [] };
    o.精度 = Math.max(o.精度, x.精度); if (!o.接收方.includes(x.接收方)) o.接收方.push(x.接收方); if (after.has(x.接收方 + "|" + k)) o.仍成立.push(x.接收方) });
  return Object.values(m);
}
function estimatedCombos(res, exactMax) {
  const m = {};
  (res.组合 || []).filter(x => x.规模 > exactMax).forEach(x => { const names = x.组合.map(cnameOf), k = names.join("、");
    const o = m[k] = m[k] || { 组合: names, 规模: x.规模, 精度: 0, 估计: 0, 接收方: [], 来源: x.来源, 仍成立: [], 子集: x.子集.map(u => [u.字段.map(cnameOf), u.精度]), 重训精度: x.重训精度, 核对越线: x.核对越线 };
    o.估计 = Math.max(o.估计, x.精度); o.精度 = x.重训精度 != null ? x.重训精度 : o.估计; o.接收方.push(x.接收方); if (x.二次定级后仍成立) o.仍成立.push(x.接收方) });
  return Object.values(m);
}
async function loadCombos(key, k, retrain = 0) {
  const [task, tgt] = key.split("|"); if (retrain) { CMB[key] = { 计算中: true, 重训: retrain }; render() } else CMB[key] = null;
  const get = async () => (await api(`/api/combos?${new URLSearchParams({ 任务: task, 保护对象: tgt, 规模: k })}`)).结果;
  try {
    let r = retrain ? null : await get();
    if (!r && canRun()) {
      if (S.srv.作业.状态 == "运行中") { CMB[key] = { 错误: "已有作业在运行，请稍后再选" }; return render() }
      await api("/api/combos", { 任务: task, 保护对象: tgt, 规模: k, 重训: retrain }); CMB[key] = { 计算中: true, 重训: retrain }; if (S.page == "combos") render();
      while ((S.srv = await api("/api/status")).作业.状态 == "运行中") { await new Promise(z => setTimeout(z, 1500)); CMB[key] = { 计算中: true, 重训: retrain, 日志: S.srv.作业.日志 }; if (S.page == "combos") render() }
      r = await get(); if (!r) { CMB[key] = { 错误: S.srv.作业.日志 || "计算失败" }; return render() }
    }
    CMB[key] = r || { 错误: canRun() ? "计算失败" : "当前为演示方式，不能当场计算更大的组合" };
  } catch (e) { CMB[key] = { 错误: e.message } }
  if (S.page == "combos" && S.task == task) render();
}
function lattice(names, sub, full, line) {             // 子集格子图：最下层单个字段，往上逐层多一个字段，最上层为整个组合
  const s = names.length, val = {}; sub.forEach(([fs, v]) => val[fs.slice().sort().join("|")] = v); val[names.slice().sort().join("|")] = full;
  const lvls = []; for (let k = 1; k <= s; k++) { const out = []; const rec = (st, cur) => { if (cur.length == k) { out.push(cur); return } for (let i = st; i < s; i++) rec(i + 1, cur.concat(i)) }; rec(0, []); lvls.push(out) }
  const W = 620, H = 20 + s * 92, pos = {};
  lvls.forEach((row, li) => row.forEach((c, j) => pos[c.join(",")] = [W * (j + 1) / (row.length + 1), H - 50 - li * 92]));
  let edges = "", nodes = "";
  lvls.slice(0, -1).forEach((row, li) => row.forEach(c => lvls[li + 1].filter(d => c.every(x => d.includes(x))).forEach(d => { const [x1, y1] = pos[c.join(",")], [x2, y2] = pos[d.join(",")]; edges += `<line x1="${x1}" y1="${y1 - 18}" x2="${x2}" y2="${y2 + 18}"/>` })));
  lvls.forEach(row => row.forEach(c => { const v = val[c.map(i => names[i]).sort().join("|")], [x, y] = pos[c.join(",")], over = v != null && v > line, w = 22 + c.length * 20;
    nodes += `<g class="${over ? "ov" : "ok"}"><rect x="${x - w / 2 - 14}" y="${y - 20}" width="${w + 28}" height="40" rx="10"/><text x="${x}" y="${y - 3}">${c.map(i => CIRC[i]).join("")}</text><text class="v" x="${x}" y="${y + 13}">${v == null ? "—" : f3(v)}</text></g>` }));
  return `<svg class="lat" viewBox="0 0 ${W} ${H}" style="width:100%"><g class="e">${edges}</g>${nodes}</svg>
    <div class="latk">${names.map((n, i) => `<span><b>${CIRC[i]}</b>${n}</span>`).join("")}<span class="sub">绿框不过线，红框越线（判定线 ${line}）</span></div>`;
}
function pCombos() {
  const tn = T().中文名, n = cand().length, exactMax = Math.min(D.组合上限, n), maxSel = Math.min(6, n);
  // 组合最大字段数默认取 K + 1，与背景预算一致
  if (!S.ck || S.ckTask != S.task) { S.ck = Math.min(kUse() + 1, maxSel); S.ckTask = S.task } S.ck = Math.min(S.ck, maxSel); const k = S.ck, key = `${S.task}|${tcode()}|${k}`, needEst = k > exactMax;
  let rows = verifiedCombos().filter(x => x.规模 <= k), est = null, estNew = [];
  if (needEst) { est = CMB[key]; if (est === undefined) { loadCombos(key, k); est = null } else if (est && est.组合) { const have = new Set(rows.map(x => x.组合.join("、"))); estNew = estimatedCombos(est, exactMax).filter(x => !have.has(x.组合.join("、"))); rows = rows.concat(estNew) } }
  const fl = { 全部: x => 1, 调级后仍成立: x => x.仍成立.length, 已拆开: x => !x.仍成立.length };
  if (!fl[S.cfl]) S.cfl = "全部";
  rows.sort((a, b) => a.规模 - b.规模 || b.精度 - a.精度); const shown = rows.filter(fl[S.cfl]);
  if (S.cs == null || !shown[S.cs]) S.cs = 0; const cur = shown[S.cs];
  const bySize = {}; rows.forEach(x => bySize[x.规模] = (bySize[x.规模] || 0) + 1);
  const freq = {}; rows.forEach(x => x.组合.forEach(nm => freq[nm] = (freq[nm] || 0) + 1)); const top = Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 10);
  const still = rows.filter(x => x.仍成立.length).length, ti = D.敏感.indexOf(tn);
  const lineOf = x => Math.min(...x.接收方.map(r => rline(rlev(r))));
  const pend = est && est.待核对 ? est.待核对 : [], estHelp = "规模不超过 " + exactMax + " 的组合在推断验证中逐个重新训练。更大的规模先由估计器当场打分：预训练的主干网络对每个组合做一次闭式岭回归读出，给出圈定字段全部组合的估计，单调闭包后找出估计的最小越线组合；估计值在判定线下 0.05 以内、子集都不过线的组合也列为“值得重新训练”。点“重新训练”后，这些组合用 3 个随机种子重新训练，结果写入推断缓存，本页自动更新，重跑二次定级时也会计入。" + (est && est.估计与重训平均绝对误差 != null ? `估计与已重训组合的平均误差 ${est.估计与重训平均绝对误差}。` : "");
  const status = !needEst ? `<span class="tag g">规模 ≤ ${exactMax}：全部为重新训练的结果</span>` : !est ? `<span class="tag a">正在读取…</span>` : est.计算中 ? `<span class="tag a">${est.重训 ? `正在重新训练 ${est.重训} 个组合…` : "估计器计算中…"} ${(est.日志 || "").split("\n").pop()}</span>` : est.错误 ? `<span class="tag r">${est.错误}</span>`
    : `<span class="tag b">估计器打分 ${est.估计组合数} 个组合 · ${est.用时秒} 秒</span><span class="tag ${estNew.length ? "r" : "g"}">${estNew.length ? `另有 ${estNew.length} 个越线组合` : "没有其他越线组合"}</span>${pend.length ? `<span class="tag a">值得重新训练 ${pend.length} 个</span>` : `<span class="tag g">候选都已重新训练</span>`}`;
  const retrainBtn = needEst && est && !est.计算中 && !est.错误 && pend.length ? `<button class="btn sm" id="rtn" ${canRun() ? "" : "disabled"}>${icon("bot")}重新训练 ${pend.length} 个组合</button>` : "";
  const sizeSel = Array.from({ length: maxSel - 1 }, (_, i) => i + 2).map(s => `<a data-ck="${s}" class="${s == k ? "on" : ""}">${s}<small>${s <= exactMax ? "逐个重训" : s == kUse() + 1 ? "试算 + 估计器" : "估计器"}</small>${s == kUse() + 1 ? '<em class="kdef">K + 1</em>' : ""}</a>`).join("");
  $("#main").innerHTML = objBar() + `<div class="kpis">${kpi(icon("combo"), rows.length ? "r" : "g", "最小越线组合 " + q(TIP.combo), rows.length, Object.entries(bySize).map(([s, c]) => `${s} 字段 ${c}`).join(" · ") || "没有越线组合")}
     ${kpi(icon("layers"), "a", "涉及的字段", Object.keys(freq).length + ` <small>/ ${n}</small>`, top.length ? `出现最多：${top[0][0]}（${top[0][1]} 次）` : "—")}
     ${kpi(icon("shield"), still ? "r" : "g", "二次定级后仍成立", still, rows.length ? `其余 ${rows.length - still} 个已被调级拆开` : "—")}
     ${kpi(icon("tune"), "b", "组合最大字段数", k, k <= exactMax ? "全部为重新训练的结果" : `规模 > ${exactMax} 的由估计器计算`)}</div>
   <div class="card ctl"><div class="ctl-l"><h3>${icon("combo")}组合最大字段数 ${q(`接收方最多把几个字段凑在一起推断。默认取背景预算 K 加 1，即一个字段加上至多 K 个背景字段。`)}</h3>
      <div class="seg" id="seg">${sizeSel}</div><div class="cstat">${status} ${needEst ? q(estHelp) : ""}${retrainBtn}</div>
      </div>
     <div class="ctl-r"><div class="sub" style="font-weight:600;margin-bottom:2px">字段在越线组合中出现的次数</div>${top.length ? `<div id="cf" style="height:${Math.max(120, 26 * top.length + 20)}px"></div>` : '<div class="empty" style="padding:30px 0">当前规模下没有越线组合</div>'}</div></div>
   <div class="split"><div class="left card"><h3>${icon("combo")}“${tn}”的最小越线组合<span class="r"><span class="chips">${Object.keys(fl).map(c => `<span class="chip ${c == S.cfl ? "on" : ""}" data-cf="${c}">${c} ${rows.filter(fl[c]).length}</span>`).join("")}</span></span></h3>
     <div class="scroll" data-sk="c1" style="max-height:calc(100vh - 280px)"><table><tr><th>#</th><th>组合中的字段</th><th>规模</th><th>能凑齐的接收方</th><th style="width:24%">推断精度</th><th>来源</th><th>二次定级后</th></tr>
     ${shown.map((x, i) => { const line = lineOf(x); return `<tr class="c ${i == S.cs ? "pick" : ""}" data-i="${i}"><td class="sub">${i + 1}</td><td>${x.组合.map(nm => `<span class="tag">${nm}</span>`).join("")}</td><td class="num">${x.规模}</td><td class="nw">${x.接收方.map(r => rt(r, rlev(r))).join("")}</td>
       <td><div class="hbar"><div class="bar"><i style="width:${x.精度 * 100}%;background:${riskBar(x.精度)}"></i><b style="left:${line * 100}%"></b></div><b class="num" style="color:${riskColor(x.精度)}">${f3(x.精度)}</b></div></td>
       <td class="nw">${x.来源 == "重训" ? '<span class="tag g">重新训练</span>' : x.来源 == "估计、已核对" ? `<span class="tag b">估计 · 已核对</span>${x.核对越线 === false ? '<span class="tag">核对未越线</span>' : ""}` : '<span class="tag a">估计</span>'}</td>
       <td class="nw">${x.仍成立.length ? '<span class="tag r">仍成立</span>' : '<span class="tag g">已拆开</span>'}</td></tr>` }).join("") || `<tr><td colspan="7" class="empty">${needEst && est && est.计算中 ? "估计器计算中…" : "没有符合条件的越线组合"}</td></tr>`}</table></div>
     <div class="legend" style="margin-top:8px"><span><i style="background:linear-gradient(90deg,#60a5fa,#f5b83d,#e5484d)"></i>推断精度</span><span><i style="background:#0f1a2e;width:2px"></i>判定线（取能凑齐的接收方中最低的一条）</span></div></div>
    <div class="right card linked">${cur ? comboDetail(cur, ti, lineOf(cur)) : '<div class="empty">选择左侧的一个组合</div>'}</div></div>`;
  bindObj(); pick("tr.c", r => S.cs = +r.dataset.i);
  $$("[data-ck]").forEach(a => a.onclick = () => { S.ck = +a.dataset.ck; S.cs = null; render() }); if ($("#rtn")) $("#rtn").onclick = () => loadCombos(key, k, pend.length); $$("[data-cf]").forEach(a => a.onclick = () => { S.cfl = a.dataset.cf; S.cs = null; render() });
  if (top.length) chart($("#cf"), { grid: { left: 150, right: 30, top: 4, bottom: 4 }, tooltip: {}, xAxis: { type: "value", show: false }, yAxis: { type: "category", inverse: true, data: top.map(x => x[0]), axisTick: { show: false }, axisLine: { show: false }, axisLabel: { fontSize: 12, color: "#2a3852" } },
    series: [{ type: "bar", data: top.map(x => x[1]), barWidth: 12, itemStyle: { color: "#8b5cf6", borderRadius: [0, 6, 6, 0] }, label: { show: true, position: "right", fontSize: 11 } }] });
  if (cur) { if (CURV[S.task] === undefined) loadCurv(S.task); const cv = ((CURV[S.task] || {})[tn] || {})[cur.组合.join("、")]; if (cv && $("#cc")) chartL($("#cc"), curveOpt([["组合的推断值", cv, C.red]], CTRUE)) }
}
function comboDetail(x, ti, line) {
  const sub = x.子集 || (D.组合子集 || {})[T().中文名 + "|" + x.组合.join("、")] || [], cv = ((CURV[S.task] || {})[T().中文名] || {})[x.组合.join("、")];
  const mem = x.组合.map(nm => { const f = fOf(nm) || {}; return { nm, a: (f.单独精度 || [])[ti], m: (f.M || [])[ti], l1: f.一次等级, l2: f.二次等级 } });
  return `<div class="lk">${icon("link")}对应左侧选中的组合</div><h3 style="font-size:17px">${x.规模} 个字段凑齐，推断精度 <span style="color:${riskColor(x.精度)}">${f3(x.精度)}</span><span class="r">${x.接收方.map(r => rt(r, rlev(r))).join("")}</span></h3>
    ${x.来源 != "重训" ? `<div class="box" style="background:var(--blue-soft);margin-bottom:10px;font-size:12.5px">估计器估计 ${f3(x.估计)}，尚未重新训练；可在上方点“重新训练”核对。子集的数值中，已重新训练的为真实值，其余为估计值。</div>` : ""}
    <div class="sub" style="font-weight:600">单独、两两……逐层凑齐时的推断精度</div>${x.规模 <= 4 ? lattice(x.组合, sub, x.精度, line) : `<div class="empty">组合超过 4 个字段，子集较多，不画格子图。</div>`}
    <h3 style="margin-top:12px">${icon("risk")}组合中的字段</h3><table class="mini"><tr><th>字段</th><th>单独推断</th><th>字段推断风险 M</th><th>一次 → 二次</th></tr>${mem.map(r => `<tr><td class="nw"><b>${r.nm}</b></td><td class="num">${r.a == null ? "—" : f3(r.a)}</td><td class="num"><b style="color:${riskColor(r.m || 0)}">${r.m == null ? "—" : f3(r.m)}</b></td><td class="nw">${r.l1 ? lv(r.l1) : ""}${r.l2 > r.l1 ? " → " + lv(r.l2) : ' <span class="sub">不变</span>'}</td></tr>`).join("")}</table>
    <div class="sub" style="margin-top:6px">${x.仍成立.length ? `二次定级后，${x.仍成立.join("、")}仍能凑齐这个组合。` : "二次定级调高了其中至少一个字段，接收方已凑不齐这个组合。"}</div>
    ${cv ? `<h3 style="margin-top:12px">${icon("eye")}组合的推断值与真实值</h3><div id="cc" style="height:220px"></div>` : ""}`;
}

/* ---------------- ⑤ 二次定级：保护全部（默认）或单独保护某一项 ---------------- */
function scopeData() {
  if (S.scope == "all" || !D.单独保护 || !D.单独保护[S.scope]) return { all: true, G: D.GRPO, fld: f => f, c0: D.一次定级下的越线, c1: D.二次定级后的越线, caps: D.接收方能力, rounds: D.整体核对 };
  const s = D.单独保护[S.scope]; return { all: false, name: s.保护对象, G: s.GRPO, fld: f => Object.assign({}, f, s.字段[f.字段] || {}), c0: s.一次定级下的越线, c1: s.二次定级后的越线, caps: s.接收方能力, rounds: s.整体核对 };
}
async function runScope(code) {
  if (!canRun()) return alert("当前为演示方式或该任务没有缓存，不能计算。");
  if (S.srv.作业.状态 == "运行中") return alert("已有作业在运行，请稍候。");
  const r = await (await fetch("/api/rerun", { method: "POST", body: JSON.stringify({ 任务: S.task, 参数: Object.assign({}, D.参数, { 只保护: code }) }) })).json(); if (r.错误) return alert(r.错误);
  S.srv.作业 = { 状态: "运行中", 任务: S.task }; S.scope = code; render(); poll();
}
const UPARTS = ["安全收益", "可用性成本", "聚合推断惩罚"];
function uWhy(cur, y) {                                // 保持原级与现等级时整套方案的综合效用之差
  const L = y && y.各级效用, z0 = L && L.find(z => z.等级 == cur.一次等级), z1 = L && L.find(z => z.等级 == cur.二次等级); if (!z0 || !z1) return "";
  const d = z1.效用 - z0.效用;
  return `<div class="sub" style="margin-top:4px">若保持 ${LVN(cur.一次等级)}，整套方案的综合效用为 <b>${f2(z0.效用)}</b>；调到 ${LVN(cur.二次等级)}后为 <b>${f2(z1.效用)}</b>，<b class="${d >= 0 ? "green" : "red"}">${d >= 0 ? "提高" : "降低"} ${f2(Math.abs(d))}</b></div>
    <div class="dchips">${UPARTS.map(k => { const x = z1.构成[k] - z0.构成[k]; return `<span class="${x >= 0 ? "up" : "dn"}">${k} ${x >= 0 ? "＋" : "−"}${f2(Math.abs(x))}</span>` }).join("")}</div>`;
}
function lvUtil(cur, y) {
  const L = y && y.各级效用; if (!L) return ""; const now = L.find(z => z.等级 == cur.二次等级) || L[L.length - 1];
  return `<h3 style="margin-top:14px">${icon("tune")}只改这个字段的等级时，整套方案的综合效用 ${q("其他字段保持现方案的等级不动，只把这个字段换成各个等级，计算整套方案的综合效用（安全收益 + 可用性成本 − 聚合推断惩罚）。各项为扣分，越接近 0 越好。")}</h3>
    <table class="lvu"><tr><th>等级</th><th>综合效用</th><th>与现等级比</th><th>含该字段的越线组合</th></tr>${L.map(z => `<tr class="${z.等级 == now.等级 ? "pick" : ""} ${z.允许 ? "" : "off"}"><td>${lv(z.等级)}${z.等级 == cur.一次等级 ? ' <span class="sub">原级</span>' : ""}${z.等级 == now.等级 ? ' <span class="tag b" style="margin:0 0 0 4px">现等级</span>' : ""}</td>
      <td class="num"><b>${f2(z.效用)}</b></td><td class="num">${z.等级 == now.等级 ? '<span class="sub">—</span>' : `<span class="${z.效用 < now.效用 ? "red" : "green"}">${z.效用 >= now.效用 ? "＋" : "−"}${f2(Math.abs(z.效用 - now.效用))}</span>`}</td>
      <td class="num">${z.含该字段的越线组合}${z.允许 ? "" : ' <span class="sub">（低于直接定级要求，不可选）</span>'}</td></tr>`).join("")}</table>`;
}
function inputsBar(sd) {                               // 强化学习的思路：字段推断风险 M 与越线组合共同进入效用，求整套等级
  const DL = D.参数.直接定级线, cs = cand().map(sd.fld), dir = cs.filter(f => upKind(f) == "直接定级").length, mx = Math.max(0, ...D.一次定级下的越线.map(x => x.组合.length));
  return `<div class="inbar big"><div class="in m" data-go="aggr"><div class="h">${icon("nodes")}字段推断风险 M<em>K = ${kUse()}</em></div><div class="t">M ≥ ${DL} 直接定级（${dir} 个），其余进入<b>安全收益</b></div></div>
    <div class="op">＋</div><div class="in c" data-go="combos"><div class="h">${icon("combo")}越线组合<em>${sd.c0.length} 个 · 至多 ${mx} 字段</em></div><div class="t">调级后仍能凑齐的，进入<b>聚合推断惩罚</b></div></div>
    <div class="op">→</div><div class="in r"><div class="h">${icon("bot")}强化学习求整套等级</div><div class="t">每步采样 ${D.参数.group} 套方案，按组内相对好坏更新策略，共 ${D.参数.steps} 步；越线组合 <b class="red">${sd.c0.length}</b> → <b class="${sd.c1.length ? "red" : "green"}">${sd.c1.length}</b></div></div></div>`;
}
function pRegrade() {
  if (!S.scope) S.scope = "all"; const sd = scopeData(), G = sd.G, cs = cand().map(sd.fld), up = cs.filter(f => f.二次等级 > f.一次等级), nk = k => up.filter(f => upKind(f) == k).length, busy = S.srv.作业.状态 == "运行中";
  const gap = G.参照最优 != null ? Math.abs((G.效用 - G.参照最优) / (G.参照最优 || 1)) * 100 : null, ti = sd.all ? null : D.敏感.indexOf(sd.name);
  const mOf = f => sd.all ? Math.max(...f.M) : f.M[0], mWho = f => sd.all ? D.敏感[f.M.indexOf(Math.max(...f.M))] : sd.name;
  const list = cs.slice().sort((a, b) => ((b.二次等级 > b.一次等级) - (a.二次等级 > a.一次等级)) || mOf(b) - mOf(a)).filter((f, k) => k < 30 || f.二次等级 > f.一次等级);
  if (S.sel == null || !list[S.sel]) S.sel = 0; const cur = list[S.sel], k = upKind(cur), y = cur.依据, w = cur.整体核对上调;
  const dIdx = y && y.对应敏感数据 ? D.敏感.indexOf(y.对应敏感数据) : -1, dM = y && y.直接定级 ? (sd.all ? cur.M[dIdx] : cur.M[0]) : null;
  const why = !k ? `<div class="empty">等级不变。</div>` : (k == "直接定级" ? `<div class="box r"><b>直接定级</b> ${q(TIP.direct)}<div class="sub">对“${y.对应敏感数据}”的 M = ${f3(dM)}，达到直接定级线 ${D.参数.直接定级线}</div></div>` : k == "联合评估" ? `<div class="box" style="background:rgba(37,99,235,.08)"><b>联合评估上调</b> ${q(TIP.grpo)}${uWhy(cur, y)}<div class="sub" style="margin-top:4px">该字段最大 M = ${f3(mOf(cur))}（对“${mWho(cur)}”）</div></div>` : "") +
    (w ? `<div class="box a" style="margin-top:8px"><b>整体核对上调</b> ${q(TIP.whole)}<div class="sub">保持原等级时，${rt(w.接收方, rlev(w.接收方))}可获取的全部字段对“${w.敏感数据}”的推断精度为 <b class="red">${f3(w.精度)}</b>${w.上调后 != null ? `，上调后 ${f3(w.上调后)}` : ""}</div></div>` : "") +
    lvUtil(cur, y) + (y && y.重新成立的越线组合 && y.重新成立的越线组合.length ? `<h3 style="margin-top:14px">若降回 ${LVN(cur.一次等级)}，重新成立的越线组合<span class="r">${y.重新成立的数量} 个</span></h3>` + y.重新成立的越线组合.map(x => `<div class="kv"><span>${rt(x.接收方, rlev(x.接收方))} → ${x.敏感数据}</span><span>${x.组合.map(n => `<span class="tag ${n == cur.中文名 ? "b" : ""}">${n}</span>`).join("")} <b class="red num">${f2(x.精度)}</b></span></div>`).join("") : "");
  const chip = f => { const done = D.单独保护 && D.单独保护[f.字段], on = S.scope == f.字段;
    return done ? `<span class="ob ${on ? "on" : ""}" data-sc="${f.字段}">只保护 ${f.中文名} ${lv(f.一次等级)}<span class="tag g" style="margin:0">已计算</span></span>` : `<span class="ob off" data-calc="${f.字段}" title="${canRun() ? "点击后在后台计算" : "演示方式下不能计算"}">只保护 ${f.中文名} ${lv(f.一次等级)}<span class="tag" style="margin:0">${busy && S.scope == f.字段 ? "计算中…" : "未计算 · 点击计算"}</span></span>` };
  $("#main").innerHTML = `<div class="objbar"><span class="lab">${icon("shield")}保护范围</span><span class="ob ${sd.all ? "on" : ""}" data-sc="all">保护全部保护对象<span class="tag g" style="margin:0">默认 · 已计算</span></span><span class="sep"></span>${sens().map(chip).join("")}
     <span class="note">${sd.all ? "所有保护对象一起权衡，每个字段只定一个等级" : `只保护“${sd.name}”，其余保护对象视为不需要保护`}</span></div>
   ${sd.all ? "" : `<div class="box a" style="margin-bottom:14px">${icon("target")} 当前为<b>单独保护“${sd.name}”</b>的结果：只考虑这一项不被推出，其余保护对象不参与权衡，所以调高的字段通常更少。与“保护全部”的结果分别保存，互不覆盖。</div>`}
   <div class="card" style="background:linear-gradient(135deg,rgba(239,245,255,.88),rgba(247,242,255,.82))"><h3>${icon("bot")}${sd.all ? "整套等级方案（所有保护对象共同决定）" : `单独保护“${sd.name}”的等级方案`} ${q("每个字段只能有一个等级。强化学习在所选保护范围内求一整套等级方案；下面的效用、训练过程和构成都属于这套方案。")}<span class="r">直接定级 ${nk("直接定级")} · 联合评估 ${nk("联合评估")} · 整体核对 ${nk("整体核对")}</span></h3>
    ${inputsBar(sd)}<div class="rlbox"><div class="fml3"><span class="lhs">U(<i>a</i>) ＝</span>
        <span class="f t1"><b>− Σ<sub>i</sub> β M<sub>i</sub> e<sup>−λ(a<sub>i</sub>−L<sub>i</sub>)</sup></b></span><span class="f t2"><b>− Σ<sub>i</sub> η (e<sup>σ(a<sub>i</sub>−L<sub>i</sub>)</sup> − 1)</b></span><span class="f t3"><b>− Σ<sub>越线组合</sub> ρ · max(v − 判定线, 0.02) / 0.1</b></span>
        <span class="nt">a<sub>i</sub> 二次等级，L<sub>i</sub> 一次等级<br>U 越接近 0 越好</span>
        <span></span><span class="k k1">安全收益：M 大的字段留在低等级时扣分</span><span class="k k2">可用性成本：每升一级，可共享的接收方减少</span><span class="k k3">聚合推断惩罚：仍能凑齐的越线组合</span><span></span></div></div>
    <div class="kpis" style="margin-bottom:12px">${kpi(icon("tune"), "a", "调高等级的字段", `${up.length} <small>/ ${cs.length}</small>`, sd.all ? "全部保护对象合计" : "只为这一项")}${kpi(icon("nodes"), "g", "越线组合", `<span class="red">${sd.c0.length}</span> <small>→</small> <span class="${sd.c1.length ? "amber" : "green"}">${sd.c1.length}</span>`, `切断 ${(G.切断比例 * 100).toFixed(1)}%`)}
     ${kpi(icon("shield"), "b", "综合效用 " + q(TIP.grpo), f2(G.最终效用 ?? G.效用), `只做一次定级 ${f2(G.只做一次定级.效用)}`)}${kpi(icon("check"), gap != null && gap < 1 ? "g" : "a", "联合评估与精确最优的差距", gap == null ? "—" : gap.toFixed(1) + "%", G.参照最优 != null ? `精确最优 ${f2(G.参照最优)}（${G.参照最优求法}）` : "未求得参照解")}</div>
    <div class="row"><div class="f2"><div class="sub" style="font-weight:600;margin-bottom:4px">训练过程（每步采样 ${D.参数.group} 套完整方案）</div><div id="tc" style="height:210px"></div></div><div><div class="sub" style="font-weight:600;margin-bottom:4px">综合效用的构成</div><div id="uc" style="height:210px"></div></div></div></div>
   <div class="split"><div class="left card"><h3>${icon("tune")}字段调整明细<span class="r">已调高的在前；${sd.all ? "M 取对各保护对象的最大值" : `M 为对“${sd.name}”的值`}</span></h3><div class="scroll" data-sk="r1" style="max-height:calc(100vh - 300px)"><table><tr><th>#</th><th>字段</th><th>一次等级</th><th>二次等级</th><th>调整方式</th><th>M</th>${sd.all ? "<th>对应保护对象</th>" : ""}</tr>
    ${list.map((f, i) => `<tr class="c ${i == S.sel ? "pick" : ""}" data-i="${i}"><td class="sub">${i + 1}</td><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td><td>${f.二次等级 > f.一次等级 ? lv(f.二次等级) : '<span class="sub">不变</span>'}</td><td>${kindTag(upKind(f))}</td><td class="num"><b style="color:${riskColor(mOf(f))}">${f3(mOf(f))}</b></td>${sd.all ? `<td class="sub">${mWho(f)}</td>` : ""}</tr>`).join("")}</table></div></div>
   <div class="right card linked"><div class="lk">${icon("link")}对应左侧第 ${S.sel + 1} 行</div><h3 style="font-size:18px">${cur.中文名}<span class="r">${lv(cur.一次等级)} → ${lv(cur.二次等级)}</span></h3>${why}</div></div>`;
  $$("[data-sc]").forEach(a => a.onclick = () => { S.scope = a.dataset.sc; S.sel = null; render() }); $$(".inbar [data-go]").forEach(a => a.onclick = () => go(a.dataset.go)); $$("[data-calc]").forEach(a => a.onclick = () => runScope(a.dataset.calc)); pick("tr.c", r => S.sel = +r.dataset.i);
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
   <div class="row"><div class="card f2"><h3>${icon("flask")}换模型复测<span class="r">任一模型超过判定线即视为越线</span></h3><div class="scroll" data-sk="e1" style="max-height:300px"><table><tr><th>接收方</th><th>保护对象</th><th>调级前（神经网络 / 梯度提升树）</th><th>调级后（神经网络 / 梯度提升树）</th><th>判定线</th><th>结论</th></tr>
     ${R.map(x => { const o = Math.max(x.神经网络, x.梯度提升树) > x.判定线, r = isRes(x.接收方, x.敏感数据); return `<tr class="${x.敏感数据 == tn ? "pick" : ""}"><td>${rt(x.接收方, rlev(x.接收方))}</td><td><b>${x.敏感数据}</b></td><td class="num">${x.调级前神经网络 != null ? f3(x.调级前神经网络) + " / " + f3(x.调级前梯度提升树) : "—"}</td><td class="num"><b>${f3(x.神经网络)} / ${f3(x.梯度提升树)}</b></td><td class="num">${x.判定线}</td><td>${r ? `<span class="tag a">公开基底可推出</span>` : o ? '<span class="tag r">越线</span>' : '<span class="tag g">未越线</span>'}</td></tr>` }).join("")}</table></div></div>
    <div class="card"><h3>${icon("flask")}整体核对 ${q(TIP.whole)}</h3>${D.整体核对.length ? `<table><tr><th>接收方</th><th>核对前</th><th>撤出</th><th>放回</th><th>核对后</th></tr>${D.整体核对.map(r => `<tr><td>${rt(r.接收方, rlev(r.接收方))}</td><td class="num"><b class="${r.核对前推断精度 > rline(rlev(r.接收方)) ? "red" : ""}">${f3(r.核对前推断精度)}</b></td><td class="num">${r.撤出字段数}</td><td class="num">${r.放回字段数}</td><td class="num"><b class="${r.核对后推断精度 > rline(rlev(r.接收方)) ? "amber" : "green"}">${f3(r.核对后推断精度)}</b></td></tr>`).join("")}</table>` : `<div class="empty">联合评估后各接收方均未越线，无需追加调整。</div>`}</div></div>`;
  bindObj();
  $("#exp").onclick = () => { const rows = [["字段", "中文名", "类别", "角色", "公开情况", "影响对象", "影响程度", "一次等级", "二次等级", "调整方式", "最大M", "复核调整"]].concat(D.字段.map(f => [f.字段, f.中文名, f.类别, f.角色, f.公开情况, f.影响对象, f.影响程度, f.一次等级, f.二次等级, f.角色 == "候选" ? upKind(f) : "", f.M ? Math.max(...f.M) : "", f.复核调整 ? "是" : ""].map(v => `"${String(v).replace(/"/g, '""')}"`)));
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["﻿" + rows.map(r => r.join(",")).join("\n")], { type: "text/csv" })); a.download = D.id + "_定级台账.csv"; a.click() };
}
boot();
