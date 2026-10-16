/* 数据定级与共享审查系统：界面（第三版）。只读取 ../samples/ 下已算好的任务文件。 */
const TASKS = ["ieee30", "pjm", "community", "insurance"];
const PAGES = [
  ["", "tasks", "任务管理", "选择或新建定级任务"],
  ["", "overview", "总体概览", "当前任务的定级结果与风险变化"],
  ["规则与参数", "rules", "等级与接收方", "各等级的数据可以提供给谁"],
  ["规则与参数", "params", "判定参数", "判定线、字段敏感度的计算口径"],
  ["规则与参数", "policy", "强化学习策略", "联合评估的效用函数与训练设置"],
  ["定级", "grade1", "一次定级", "依据国家标准，由大语言模型逐字段判定初始等级"],
  ["定级", "risk", "推断风险", "按一次等级放行时，接收方能否推出无权获取的数据"],
  ["定级", "sens", "字段敏感度", "把组合的推断能力落实到每个字段"],
  ["定级", "regrade", "二次定级", "把聚合推断计入等级"],
  ["效果", "effect", "定级效果", "调级前后的推断风险对比与核对"]];
const S = { task: "ieee30", page: "overview", t: 0, K: 2, sel: null, step: 0, filter: "全部", kw: "", shut: {}, P: null, srv: { 完整方式: false, 可重跑: [], 作业: { 状态: "空闲" } } };
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
let D = null, ALL = {}, charts = [];
const LVN = n => n <= 4 ? n + " 级" : n == 5 ? "重要" : "核心", lv = n => `<span class="lv lv${n}">${LVN(n)}</span>`, f2 = x => (+x).toFixed(2), f3 = x => (+x).toFixed(3);
const q = t => `<span class="q" data-tip="${t}">?</span>`;
const C = { blue: "#2563eb", red: "#e5484d", green: "#12a36d", amber: "#e08a1e", ink: "#1a2233", grid: "#eef1f6" };
function chart(el, opt) { const c = echarts.init(el); c.setOption(Object.assign({ textStyle: { fontFamily: "Noto Sans CJK SC, Microsoft YaHei, sans-serif" } }, opt)); charts.push(c); return c }
window.addEventListener("resize", () => charts.forEach(c => c.resize()));
const cand = (d = D) => d.字段.filter(f => f.角色 == "候选"), sens = (d = D) => d.字段.filter(f => f.角色 == "敏感"), T = () => sens()[S.t];
const upKind = f => f.二次等级 <= f.一次等级 ? "" : f.依据 && f.依据.直接定级 ? "直接定级" : f.整体核对上调 ? "整体核对" : "联合评估";
const kindTag = k => k ? `<span class="tag ${k == "直接定级" ? "r" : k == "整体核对" ? "a" : "b"}">${k}</span>` : "";
const RECV3 = () => D.接收方.filter(r => r.级 <= 3);
const TIP = {
  M: "字段推断敏感度 M：在接收方已有至多 K 个其他字段的基础上，再获得该字段，对敏感数据的推断精度的最大提升。取值 0 至 1。",
  V: "推断精度：用接收方可获取的字段训练预测模型，在未参与训练的数据上的拟合优度 R²。0 为无法推断，1 为完全还原。",
  line: "判定线：推断精度超过该值即视为敏感数据可被推出。社会公众 0.7，其他接收方 0.8。",
  combo: "最小越线组合：某类接收方可同时获取、且推断精度超过判定线的字段组合；去掉其中任一字段即不再越线。",
  direct: "直接定级：M 不低于 0.7 的字段，定为与被推断数据同级。",
  whole: "整体核对：调级后，对每类接收方可获取的全部字段重新训练，取神经网络与梯度提升树中较高的精度；仍越线则继续调整。",
  grpo: "组相对策略优化：每一步对同一任务采样一组完整的等级方案，以组内相对优势更新策略。综合效用 = 安全收益 + 可用性成本 − 聚合推断惩罚，各项为扣分，越接近 0 越好。",
  W: "整体推断惩罚：各类接收方合并全部可获取字段后，对无权数据的推断精度超出判定线的部分。由快速估计模型计算，估计值可能偏低，最终结果以重新训练为准。",
  S: "安全收益：字段留在较低等级时仍存在的推断风险，M 越大、等级越低，扣分越多。", Cc: "可用性成本：等级越高，数据越难共享使用，扣分越多。", P: "聚合推断惩罚：每个仍成立的越线组合扣固定分值；输出方案须为零。",
  base: "公开基底：法定公开、所有接收方均已掌握的字段，在推断中始终可见，不参与调级。" };

async function boot() {
  await Promise.all(TASKS.map(async k => { try { ALL[k] = await (await fetch("../samples/" + k + ".json?" + Date.now())).json() } catch (e) { } }));
  const P = new URLSearchParams(location.search); ["task", "page"].forEach(k => P.get(k) && (S[k] = P.get(k))); ["t", "step", "K", "sel"].forEach(k => P.get(k) != null && (S[k] = +P.get(k)));
  try { S.srv = await (await fetch("/api/status")).json() } catch (e) { }
  setTask(S.task, true);
}
function setTask(k, keep) { S.task = k; D = ALL[k]; S.P = Object.assign({}, D.参数); if (!keep) { S.t = 0; S.step = 0; S.sel = null } S.t = Math.min(S.t, D.敏感.length - 1); S.K = Math.min(S.K, D.背景增益.length - 1); render() }
function go(p) { S.page = p; S.sel = null; render() }
function render() {
  clearInterval(S.timer); charts.forEach(c => c.dispose()); charts = []; const p = PAGES.find(p => p[1] == S.page), c = cand();
  let h = "", g = null, no = 0;
  PAGES.forEach(x => { if (x[0] != g) { g = x[0]; no = 0; if (g) h += `<div class="grp" data-g="${g}"><span>${g}</span><em>${S.shut[g] ? "▸" : "▾"}</em></div>` }
    if (!x[0] || !S.shut[x[0]] || x[1] == S.page) h += `<a class="${x[1] == S.page ? "on" : ""} ${x[0] ? "sub" : ""}" data-p="${x[1]}">${x[0] ? `<b>${++no}</b>` : "<i></i>"}${x[2]}</a>` });
  $("#nav").innerHTML = h; $$("#nav a").forEach(a => a.onclick = () => go(a.dataset.p)); $$("#nav .grp").forEach(a => a.onclick = () => { S.shut[a.dataset.g] = !S.shut[a.dataset.g]; render() });
  $("#cur").innerHTML = `<div class="l"><span>当前任务</span><a>切换</a></div><div class="n">${D.名称}</div><div class="m">${D.类别} · ${c.length} 个候选字段 · ${D.敏感.length} 项敏感数据</div>`; $("#cur").onclick = () => go("tasks");
  $("#foot").innerHTML = `规则库：GB/T 43697<br>初判模型：${D.大语言模型}`;
  $("#crumb").innerHTML = S.page == "tasks" ? "" : `<b>${D.名称}</b>${p[0] ? " / " + p[0] : ""}`; $("#title").textContent = p[2]; $("#subtitle").textContent = p[3]; $("#hright").innerHTML = "";
  ({ tasks: pTasks, overview: pOverview, rules: pRules, params: pParams, policy: pPolicy, grade1: pGrade1, risk: pRisk, sens: pSens, regrade: pRegrade, effect: pEffect })[S.page]();
}
const kpi = (ic, cls, k, v, d) => `<div class="kpi"><div class="ic ${cls}">${ic}</div><div><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div></div>`;
const objChips = () => `<div class="chips" style="margin-bottom:12px"><span class="sub" style="align-self:center;margin-right:4px">敏感数据</span>${sens().map((f, i) => `<span class="chip ${i == S.t ? "on" : ""}" data-t="${i}">${f.中文名} ${LVN(f.一次等级)}</span>`).join("")}</div>`;
const bindObj = () => $$(".chip[data-t]").forEach(a => a.onclick = () => { S.t = +a.dataset.t; S.step = 0; S.sel = null; render() });
const capOf = (r, tn) => D.接收方能力.find(x => x.接收方 == r && x.敏感数据 == tn);
const isRes = (r, tn) => (D.仅凭公开基底可推出 || []).some(x => x.接收方 == r && x.敏感数据 == tn);
const overCells = k => D.接收方能力.filter(x => x[k] > x.判定线 && !isRes(x.接收方, x.敏感数据)).length;

/* ================= 规则与参数 ================= */
const canRun = () => S.srv.完整方式 && S.srv.可重跑.includes(S.task), dirty = () => JSON.stringify(S.P) != JSON.stringify(D.参数);
function runBar() {
  const j = S.srv.作业, busy = j.状态 == "运行中";
  return `<div class="card" style="display:flex;align-items:center;gap:14px"><div style="flex:1"><b>参数应用于：${D.名称}</b><div class="sub">${busy ? `正在重跑“${j.任务}”，完成后自动刷新…` : !canRun() ? "当前为演示方式或该任务没有缓存的推断精度，参数只读。完整方式下可修改并重跑二次定级。" : dirty() ? "参数已修改，尚未生效。" : "当前结果即按下列参数计算。重跑只重做二次定级及之后的步骤，不重新训练字段组合的推断模型。"}${j.状态 == "失败" ? ` <span class="red">上次重跑失败：${(j.日志 || "").slice(-120)}</span>` : ""}</div></div>
   <button class="btn o" id="rst" ${dirty() ? "" : "disabled"}>恢复</button><button class="btn" id="run" ${canRun() && !busy ? "" : "disabled"}>${busy ? "运行中…" : "应用并重跑"}</button></div>`;
}
function bindRun() {
  $$("[data-k]").forEach(e => { const k = e.dataset.k; if (!canRun()) e.disabled = true; e.onchange = () => { S.P[k] = e.type == "checkbox" ? e.checked : +e.value; render() } });
  $("#rst").onclick = () => { S.P = Object.assign({}, D.参数); render() };
  $("#run").onclick = async () => { const r = await (await fetch("/api/rerun", { method: "POST", body: JSON.stringify({ 任务: S.task, 参数: S.P }) })).json(); if (r.错误) return alert(r.错误); S.srv.作业 = { 状态: "运行中", 任务: S.task }; render(); poll() };
}
async function poll() {
  clearInterval(S.pt); S.pt = setInterval(async () => { try { S.srv = await (await fetch("/api/status")).json() } catch (e) { return }
    if (S.srv.作业.状态 != "运行中") { clearInterval(S.pt); if (S.srv.作业.状态 == "完成") { ALL[S.task] = await (await fetch("../samples/" + S.task + ".json?" + Date.now())).json(); setTask(S.task, true) } else render() } }, 2000);
}
const num = (k, label, tip, step, min, max) => `<div class="kv"><span>${label} ${q(tip)}</span><span><input class="search" style="width:90px;text-align:right" type="number" data-k="${k}" value="${S.P[k]}" step="${step}" min="${min}" max="${max}">${S.P[k] != D.参数[k] ? ' <span class="tag a">已改</span>' : ""}</span></div>`;
function pRules() {
  const c = cand(), rs = D.接收方;
  $("#main").innerHTML = `<div class="card"><h3>等级与接收方 ${q("取自 GB/T 43697 附录 H：一般数据分 4 级，另有重要数据、核心数据。各等级的共享范围决定了哪类接收方可以获取。")}</h3>
   <table><tr><th>等级</th><th>国标给出的共享范围</th><th>可获取的接收方</th><th>本任务的字段数（一次 → 二次）</th></tr>${D.等级表.map(l => `<tr><td>${lv(l.级)}</td><td>${l.共享范围}</td><td>${l.接收方 == "无" ? '<span class="sub">不对外</span>' : rs.filter(r => r.级 >= l.级).map(r => `<span class="tag">${r.名称}</span>`).join("")}</td><td class="num">${l.级 <= 4 ? `${c.filter(f => f.一次等级 == l.级).length} → <b>${c.filter(f => f.二次等级 == l.级).length}</b>` : "—"}　<span class="sub">敏感数据 ${sens().filter(f => f.一次等级 == l.级).length}</span></td></tr>`).join("")}</table></div>
  <div class="row"><div class="card"><h3>各类接收方</h3><table><tr><th>接收方</th><th>可获取的等级</th><th>不得被其推出的数据</th><th>判定线 ${q(TIP.line)}</th><th>可获取的候选字段（一次 → 二次）</th></tr>
   ${rs.map(r => `<tr><td><b>${r.名称}</b></td><td>${[1, 2, 3, 4].filter(l => l <= r.级).map(lv).join(" ")}</td><td>${LVN(r.级 + 1)}及以上</td><td class="num">${r.判定线}</td><td class="num">${c.filter(f => f.一次等级 <= r.级).length} → <b>${c.filter(f => f.二次等级 <= r.级).length}</b></td></tr>`).join("")}</table></div>
  <div class="card"><h3>判定表：影响对象 × 影响程度 ${q(TIP.first || "按“影响对象 × 影响程度”查表确定等级。")}</h3><table class="mx"><tr><th></th>${["一般危害", "严重危害", "特别严重危害"].map(d => `<th>${d}</th>`).join("")}</tr>
   ${["国家安全", "经济运行", "社会秩序", "公共利益", "组织权益", "个人权益"].map(o => `<tr><th style="text-align:right">${o}</th>${["一般危害", "严重危害", "特别严重危害"].map(d => `<td>${lv(D.判定表[o][d])}</td>`).join("")}</tr>`).join("")}<tr><th style="text-align:right">无危害</th><td colspan="3">${lv(1)}</td></tr></table>
   <div class="sub" style="margin-top:8px">最低参考级别：敏感个人信息不低于 4 级，一般个人信息不低于 2 级；有条件开放的公共数据不低于 2 级，禁止开放的不低于 4 级。</div></div></div>`;
}
function pParams() {
  $("#main").innerHTML = runBar() + `<div class="row"><div class="card"><h3>判定线</h3>${num("公众判定线", "社会公众", "社会公众可获取的字段对无权数据的推断精度超过该值，即视为可被推出。", 0.05, 0.5, 0.95)}${num("其他判定线", "关联方、特定授权对象", "签有协议或经授权的接收方，判定线可以略宽。", 0.05, 0.5, 0.95)}
    <div class="sub" style="margin-top:8px">推断精度为未参与训练的数据上的拟合优度 R²，取神经网络与梯度提升树中较高者。</div></div>
   <div class="card"><h3>字段推断敏感度</h3>${num("K", "背景字段数上限 K", TIP.M + " 本任务核对了 " + D.组合上限 + " 个字段以内的组合。", 1, 0, 2)}${num("直接定级线", "直接定级线", TIP.direct, 0.05, 0.5, 0.95)}
    <div class="sub" style="margin-top:8px">当前：${cand().filter(f => Math.max(...f.M) >= D.参数.直接定级线).length} 个字段达到直接定级线。</div></div></div>`; bindRun();
}
function pPolicy() {
  const G = D.GRPO;
  $("#main").innerHTML = runBar() + `<div class="row"><div class="card"><h3>综合效用 ${q(TIP.grpo)}</h3>
    ${num("beta", "安全收益系数 β", TIP.S + " 越大越倾向于上调 M 高的字段。", 0.5, 0, 10)}${num("lam", "安全收益衰减 λ", "每上调一级，该字段剩余风险的衰减速度。", 0.1, 0.1, 3)}
    ${num("eta", "可用性成本系数 η", TIP.Cc + " 越大越不愿意上调。", 0.5, 0, 10)}${num("sigma", "可用性成本增长 σ", "连续上调多级时成本的增长速度。", 0.1, 0.1, 2)}
    ${num("rho_w", "整体推断惩罚 ρw", TIP.W + " 取 0 则不计这一项。", 0.5, 0, 20)}
    ${num("rho", "聚合推断惩罚 ρ", "每个仍成立的越线组合的罚分 = ρ × 超出判定线的幅度 ÷ 0.1。刚过线的组合罚得轻，远超判定线的罚得重。", 0.5, 0, 20)}
    <div class="kv"><span>严格模式 ${q("开启后：任何越线组合都不允许保留，并在调级后做整体核对，仍越线则继续上调。结果更安全，调高的字段明显更多。")}</span><span><label style="display:flex;gap:6px;align-items:center"><input type="checkbox" data-k="严格模式" ${S.P.严格模式 ? "checked" : ""}> ${S.P.严格模式 ? "开启" : "关闭"}</label></span></div></div>
   <div class="card"><h3>训练设置</h3>${num("steps", "训练步数", "策略更新的次数。", 50, 50, 2000)}${num("group", "每组方案数", "每一步对同一任务采样的完整等级方案数量，组内比较。", 16, 16, 512)}
    <h3 style="margin-top:16px">当前结果</h3><div class="kv"><span>综合效用</span><span class="num"><b>${f2(G.效用)}</b></span></div><div class="kv"><span>同一效用下的精确最优</span><span class="num">${G.参照最优 != null ? f2(G.参照最优) + "（" + G.参照最优求法 + "）" : "—"}</span></div>
    <div class="kv"><span>越线组合切断比例</span><span class="num"><b>${(G.切断比例 * 100).toFixed(1)}%</b>（${D.一次定级下的越线.length} → ${D.二次定级后的越线.length}）</span></div><div class="kv"><span>调高的字段</span><span class="num">${cand().filter(f => f.二次等级 > f.一次等级).length} / ${cand().length}</span></div>
    ${G.整体推断项 && G.整体推断项.核对轮次 ? `<div class="kv"><span>整体推断：估计与重新训练的最大偏差 ${q("对求得的方案，把快速估计的整体推断精度与重新训练的结果比较。偏差大说明这一项被低估，剩余风险以“定级效果”页为准。")}</span><span class="num">${G.整体推断项.核对轮次[0].估计与重新训练的最大偏差}</span></div>` : ""}</div></div>`; bindRun();
}

/* ================= 任务管理 ================= */
function pTasks() {
  $("#main").innerHTML = `<div class="tcards">${TASKS.filter(k => ALL[k]).map(k => { const d = ALL[k], c = cand(d); return `<div class="tcard ${k == S.task ? "on" : ""}" data-k="${k}"><div style="display:flex;justify-content:space-between"><span class="tag b">${d.类别}</span>${k == S.task ? '<span class="tag g">当前任务</span>' : ""}</div>
    <h3 style="margin-top:8px">${d.名称}</h3><div class="sub">${d.数据说明.slice(0, 62)}…</div><div class="st"><div><b>${d.样本数}</b>样本</div><div><b>${d.字段.length}</b>字段</div><div><b>${d.敏感.length}</b>敏感数据</div><div><b>${c.filter(f => f.二次等级 > f.一次等级).length}</b>调高</div></div></div>` }).join("")}
   <div class="tcard new" id="new"><div class="plus">＋</div><div style="margin-top:6px;font-weight:600">新建任务</div><div class="sub">上传数据表与字段目录</div></div></div>`;
  $$(".tcard[data-k]").forEach(a => a.onclick = () => { S.page = "overview"; setTask(a.dataset.k) });
  $("#new").onclick = () => { $("#modal").innerHTML = `<div class="mask"><div class="dlg"><h3>新建定级任务</h3><label>任务名称</label><input placeholder="例如：某业务系统数据定级"><label>数据文件（CSV，每列一个字段）</label><input type="file"><label>字段目录（字段名、中文名、类别、公开情况、说明）</label><input type="file">
     <label>规则库</label><select><option>GB/T 43697 数据安全技术 数据分类分级规则</option></select><label>判定线</label><select><option>社会公众 0.7，其他接收方 0.8</option></select>
     <p class="sub" style="margin-top:12px">当前为演示方式，只能查看内置任务。新建任务需在完整方式下运行（需要显卡）：<code>python system/scripts/build_samples.py</code></p><div class="act"><button class="btn o" id="mc">取消</button><button class="btn" disabled>开始定级</button></div></div></div>`; $("#mc").onclick = () => $("#modal").innerHTML = "" };
}

/* ================= 总体概览 ================= */
function capMatrix(mode) {
  const rs = RECV3(); return `<table><tr><th>敏感数据</th><th>等级</th>${rs.map(r => `<th style="text-align:center">${r.名称}<br><span class="sub">判定线 ${r.判定线}</span></th>`).join("")}</tr>${sens().map((f, i) => `<tr class="c ${mode == "pick" && i == S.t ? "sel" : ""}" data-t="${i}"><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td>${rs.map(r => { const x = capOf(r.名称, f.中文名);
    if (!x) return `<td style="text-align:center"><span class="cellv n">有权获取</span></td>`; const res = isRes(r.名称, f.中文名), a = x.定级前, b = x.定级后, o = v => v > x.判定线;
    return `<td style="text-align:center">${mode == "both" ? `<span class="cellv ${o(a) ? "r" : "g"}">${f2(a)}</span> <span class="sub">→</span> <span class="cellv ${o(b) ? "r" : "g"}">${f2(b)}</span>` : `<span class="cellv ${o(a) ? "r" : "g"}">${f2(a)}</span>`}${res ? ` ${q("仅凭法定公开的信息即可推出，调整候选字段的等级不起作用。")}` : ""}</td>` }).join("")}</tr>`).join("")}</table>`;
}
function pOverview() {
  const c = cand(), up = c.filter(f => f.二次等级 > f.一次等级), b0 = overCells("定级前"), b1 = overCells("定级后");
  const steps = [["一次定级", `${D.字段.length} 个字段`, "grade1"], ["推断风险", `${b0} 处越线`, "risk"], ["字段敏感度", `${c.filter(f => Math.max(...f.M) >= .7).length} 个达到 0.7`, "sens"], ["二次定级", `调高 ${up.length} 个`, "regrade"], ["定级效果", b1 ? `${b1} 处越线` : "无越线", "effect"]];
  $("#main").innerHTML = `<div class="kpis">
   ${kpi("字", "b", "字段", D.字段.length, `候选 ${c.length} · 敏感 ${D.敏感.length}${D.字段.length - c.length - D.敏感.length ? " · 公开基底 " + (D.字段.length - c.length - D.敏感.length) : ""}`)}
   ${kpi("险", "r", "越线的“接收方 × 敏感数据” " + q(TIP.V + " " + TIP.line), `<span class="red">${b0}</span> <small>→</small> <span class="${b1 ? "red" : "green"}">${b1}</span>`, "一次定级 → 二次定级")}
   ${kpi("组", "a", "最小越线组合 " + q(TIP.combo), `<span class="red">${D.一次定级下的越线.length}</span> <small>→</small> <span class="${D.二次定级后的越线.length ? "amber" : "green"}">${D.二次定级后的越线.length}</span>`, `切断 ${(D.GRPO.切断比例 * 100).toFixed(1)}%`)}
   ${kpi("调", "b", "调高等级的字段", `${up.length} <small>/ ${c.length}</small>`, `其余 ${c.length - up.length} 个保持原等级`)}</div>
  <div class="pipe">${steps.map((s, i) => `<div class="p" style="cursor:pointer" data-go="${s[2]}"><span class="no">${i + 1}</span><div><div class="a">${s[0]}</div><div class="b">${s[1]}</div></div></div>${i < steps.length - 1 ? '<div class="ar">›</div>' : ""}`).join("")}</div>
  <div class="row"><div class="card f2"><h3>各接收方对敏感数据的推断精度：一次定级 → 二次定级 ${q(TIP.V)}<span class="r"><span class="legend"><span><i style="background:var(--red2)"></i>超过判定线</span><span><i style="background:var(--green2)"></i>未超过</span></span></span></h3>${capMatrix("both")}</div>
   <div class="card"><h3>候选字段的等级分布</h3><div id="c1" style="height:250px"></div></div></div>
  <div class="card"><h3>任务说明</h3><div class="sub" style="font-size:13px">${D.数据说明}</div></div>`;
  $$("[data-go]").forEach(a => a.onclick = () => go(a.dataset.go));
  const cnt = k => [1, 2, 3, 4].map(l => c.filter(f => f[k] == l).length);
  chart($("#c1"), { grid: { left: 36, right: 12, top: 34, bottom: 28 }, legend: { top: 0, right: 0, itemWidth: 12, itemHeight: 8 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "category", data: ["1 级", "2 级", "3 级", "4 级"], axisTick: { show: false } }, yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: C.grid } } },
    series: [{ name: "一次定级", type: "bar", data: cnt("一次等级"), itemStyle: { color: "#b9c7de", borderRadius: [4, 4, 0, 0] }, barGap: "10%", label: { show: true, position: "top", fontSize: 11, color: "#8a96aa" } }, { name: "二次定级", type: "bar", data: cnt("二次等级"), itemStyle: { color: C.blue, borderRadius: [4, 4, 0, 0] }, label: { show: true, position: "top", fontSize: 11 } }] });
}

/* ================= ① 一次定级 ================= */
function pGrade1() {
  const all = D.字段, fl = { 全部: f => 1, 候选字段: f => f.角色 == "候选", 敏感数据: f => f.角色 == "敏感", 复核调整: f => f.复核调整 }, fs = all.filter(fl[S.filter]).filter(f => !S.kw || (f.中文名 + f.字段).includes(S.kw));
  const objs = ["国家安全", "经济运行", "社会秩序", "公共利益", "组织权益", "个人权益"], degs = ["一般危害", "严重危害", "特别严重危害"], nfix = all.filter(f => f.复核调整).length;
  const detail = f => { const cl = D.条文.filter(c => f.检索到的条文.includes(c.编号));
    return `<tr class="detail"><td colspan="7"><div class="dgrid"><div><h4>判定依据</h4><div class="sub" style="font-size:13px;color:var(--ink)">${f.说明}</div>
      <div class="kv" style="margin-top:6px"><span>模型初判</span><span>${f.初判.影响对象} · ${f.初判.影响程度} → ${lv(f.初判.等级)}</span></div><div class="sub">${f.初判.理由}</div>
      ${f.复核调整 ? `<div class="kv" style="margin-top:6px"><span><span class="tag b">复核调整</span></span><span>${f.影响对象} · ${f.影响程度} → ${lv(f.一次等级)}</span></div><div class="sub">${f.复核理由}</div>` : ""}</div>
     <div><h4>判定表位置（影响对象 × 影响程度）</h4><table class="mx"><tr><th></th>${degs.map(d => `<th>${d.replace("危害", "")}</th>`).join("")}</tr>${objs.map(o => `<tr><th style="text-align:right">${o}</th>${degs.map(d => `<td class="${f.影响对象 == o && f.影响程度 == d ? "hit" : ""}">${lv(D.判定表[o][d])}</td>`).join("")}</tr>`).join("")}<tr><th style="text-align:right">无危害</th><td colspan="3" class="${f.影响程度 == "无危害" ? "hit" : ""}">${lv(1)}</td></tr></table></div>
     <div><h4>检索到的国标条文</h4>${cl.map(c => `<div class="kv"><span>${c.编号}</span><span>${c.标题} ${q(c.内容)}</span></div>`).join("")}</div></div></td></tr>` };
  $("#main").innerHTML = `<div class="pipe"><div class="p"><span class="no">1</span><div><div class="a">规则库</div><div class="b">GB/T 43697 · ${D.条文.length} 条条文 · 判定表</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">2</span><div><div class="a">大语言模型初判</div><div class="b">${D.大语言模型} · 检索条文后判断影响对象与程度</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">3</span><div><div class="a">复核</div><div class="b">${nfix} 个字段调整，保留初判与理由</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">4</span><div><div class="a">一次等级</div><div class="b">${[1, 2, 3, 4, 5, 6].map(l => [l, all.filter(f => f.一次等级 == l).length]).filter(x => x[1]).map(x => `${LVN(x[0])} ${x[1]}`).join(" · ")}</div></div></div></div>
   <div class="card"><h3>字段定级结果<span class="r" style="display:flex;gap:10px;align-items:center"><input class="search" id="kw" placeholder="搜索字段" value="${S.kw}"><span class="chips">${Object.keys(fl).map(k => `<span class="chip ${k == S.filter ? "on" : ""}" data-f="${k}">${k} ${all.filter(fl[k]).length}</span>`).join("")}</span></span></h3>
   <div class="scroll" style="max-height:760px"><table><tr><th>字段</th><th>角色</th><th>公开情况</th><th>影响对象</th><th>影响程度</th><th>一次等级</th><th>共享范围</th></tr>
   ${fs.map(f => { const i = all.indexOf(f); return `<tr class="c ${S.sel == i ? "sel" : ""}" data-i="${i}"><td><b>${f.中文名}</b> <span class="sub">${f.字段}</span></td><td>${f.角色 == "敏感" ? '<span class="tag r">敏感数据</span>' : f.角色 == "公开基底" ? `<span class="tag">公开基底</span>` : "候选"}</td><td>${f.公开情况}</td><td>${f.影响对象}</td><td>${f.影响程度}</td><td>${lv(f.一次等级)} ${f.复核调整 ? '<span class="tag b">复核调整</span>' : ""}</td><td class="sub">${D.等级表[f.一次等级 - 1].接收方 == "无" ? "不对外" : D.等级表[f.一次等级 - 1].接收方 + "及以上可获取"}</td></tr>${S.sel == i ? detail(f) : ""}` }).join("")}</table></div>
   <div class="sub" style="margin-top:8px">点击字段查看判定依据。</div></div>`;
  $$("tr.c").forEach(r => r.onclick = () => { S.sel = S.sel == +r.dataset.i ? null : +r.dataset.i; render() }); $$("[data-f]").forEach(a => a.onclick = () => { S.filter = a.dataset.f; S.sel = null; render() });
  $("#kw").onchange = e => { S.kw = e.target.value.trim(); S.sel = null; render() };
}

/* ================= ② 推断风险 ================= */
function pRisk() {
  const tn = T().中文名, st = D.阶梯[S.t], cv = D.曲线[S.t], n = st.步骤.length, combos = D.一次定级下的越线.filter(x => x.敏感数据 == tn), b0 = overCells("定级前"), res = D.仅凭公开基底可推出 || [];
  S.step = Math.min(S.step, n - 1);
  $("#main").innerHTML = `<div class="kpis">${kpi("险", b0 ? "r" : "g", "越线的“接收方 × 敏感数据” " + q(TIP.V + " " + TIP.line), b0, "按一次等级放行、合并全部可获取字段")}${kpi("组", "a", "最小越线组合 " + q(TIP.combo), D.一次定级下的越线.length, `组合规模 ≤ ${D.组合上限} 个字段`)}
    ${kpi("基", res.length ? "a" : "g", "仅凭公开基底可推出 " + q(TIP.base), new Set(res.map(x => x.敏感数据)).size + " 项", res.length ? [...new Set(res.map(x => x.敏感数据))].join("、") : "无")}</div>
   <div class="row"><div class="card" style="flex:1.15"><h3>一次定级后，各接收方对敏感数据的推断精度<span class="r">点击一行查看推断过程</span></h3>${capMatrix("pick")}
     <div class="legend" style="margin-top:10px"><span><i style="background:var(--red2)"></i>超过判定线，可被推出</span><span><i style="background:var(--green2)"></i>未超过</span><span><i style="background:#f0f3f8"></i>有权获取，不涉及</span></div></div>
    <div class="card" style="flex:1"><h3>推断过程：${tn}<span class="r"><button class="btn o" id="play">▶ 逐步演示</button></span></h3><div id="pc" style="height:190px"></div>
     <div class="chips" id="steps" style="margin-top:4px">${st.步骤.map((s, i) => `<span class="chip" data-s="${i}">${i ? "＋" : ""}${s.加入}</span>`).join("")}</div></div></div>
   <div class="card"><h3>推断值与真实值<span class="r" id="cap"></span></h3><div id="cv" style="height:220px"></div></div>
   <div class="card"><h3>最小越线组合：${tn} ${q(TIP.combo)}<span class="r">${combos.length} 个</span></h3><div class="scroll" style="max-height:330px"><table><tr><th>接收方</th><th>可同时获取的字段组合</th><th>规模</th><th>推断精度</th><th>判定线</th></tr>
   ${combos.map(x => `<tr><td>${x.接收方}</td><td>${x.组合.map(n => `<span class="tag">${n}</span>`).join("")}</td><td>${x.组合.length}</td><td class="num"><b class="red">${f3(x.精度)}</b></td><td class="num">${D.接收方.find(r => r.名称 == x.接收方).判定线}</td></tr>`).join("") || `<tr><td colspan="5" class="empty">${isRes("社会公众", tn) ? "该数据仅凭公开基底即可推出，不依赖候选字段的组合" : "没有三个字段以内的越线组合"}</td></tr>`}</table></div></div>`;
  $$("tr.c[data-t]").forEach(a => a.onclick = () => { S.t = +a.dataset.t; S.step = 0; render() });
  const pc = chart($("#pc"), { grid: { left: 40, right: 80, top: 26, bottom: 24 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: st.步骤.map((s, i) => i + 1), name: "字段数", axisTick: { show: false } }, yAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: C.grid } } },
    series: [{ type: "line", data: [], symbolSize: 10, lineStyle: { width: 3, color: C.blue }, itemStyle: { color: C.blue }, label: { show: true, formatter: p => f2(p.value), fontSize: 12, fontWeight: 600 }, areaStyle: { color: "rgba(37,99,235,.07)" }, markLine: { symbol: "none", silent: true, lineStyle: { color: C.red, type: "dashed" }, label: { formatter: "判定线 0.7", color: C.red }, data: [{ yAxis: 0.7 }] } }] });
  const isLine = D.时间序列, cvc = chart($("#cv"), { grid: { left: 60, right: 16, top: 28, bottom: 26 }, legend: { top: 0, right: 0 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: cv.真实.map((_, i) => i), name: D.横轴, nameLocation: "middle", nameGap: 8, axisLabel: { show: false }, axisTick: { show: false } }, yAxis: { type: "value", scale: true, splitLine: { lineStyle: { color: C.grid } } },
    series: [{ name: "真实值", type: "line", data: cv.真实, showSymbol: false, lineStyle: { color: "#8c98ad", width: 2 }, itemStyle: { color: "#8c98ad" }, z: 2 }, { name: "接收方的推断值", type: isLine ? "line" : "scatter", data: [], showSymbol: !isLine, symbolSize: 4, lineStyle: { color: C.red, width: 1.6 }, itemStyle: { color: C.red, opacity: .8 }, z: 3 }] });
  const show = k => { S.step = k; const s = st.步骤[k]; $$("#steps .chip").forEach((r, i) => r.classList.toggle("on", i <= k));
    $("#cap").innerHTML = `已获取：${s.组合.join(" ＋ ")}　推断精度 <b class="${s.精度 > .7 ? "red" : "green"}">${f2(s.精度)}</b>`; pc.setOption({ series: [{ data: st.步骤.map((x, i) => i <= k ? x.精度 : null) }] }); cvc.setOption({ series: [{}, { data: cv.还原[k].值 }] }) };
  show(S.step); $$("#steps .chip").forEach(r => r.onclick = () => { clearInterval(S.timer); show(+r.dataset.s) });
  $("#play").onclick = () => { clearInterval(S.timer); let k = 0; show(0); S.timer = setInterval(() => { k++; if (k >= n) return clearInterval(S.timer); show(k) }, 1500) };
}

/* ================= ③ 字段敏感度 ================= */
function pSens() {
  const c = cand(), Ks = D.背景增益, Kmax = Ks.length - 1, t = S.t, order = c.map((f, i) => i).sort((a, b) => Ks[Kmax].M[b][t] - Ks[Kmax].M[a][t]).slice(0, 14), cur = S.sel ?? order[0];
  const top = c.map((f, i) => i).sort((a, b) => Math.max(...c[b].M) - Math.max(...c[a].M)).slice(0, 16), hm = [];
  top.forEach((i, r) => D.敏感.forEach((_, k) => hm.push([k, top.length - 1 - r, c[i].M[k]])));
  $("#main").innerHTML = `<div class="pipe"><div class="p"><span class="no">V</span><div><div class="a">组合的推断精度</div><div class="b">已核对 ${D.已核对的组合数} 个字段组合${D.快速估计 ? `，快速估计 ${D.快速估计.估计的组合数} 个` : ""}</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">M</span><div><div class="a">字段推断敏感度 ${q(TIP.M)}</div><div class="b">已有至多 K 个其他字段时，再获得该字段的最大提升</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">≥</span><div><div class="a">直接定级线 0.7 ${q(TIP.direct)}</div><div class="b">${c.filter(f => Math.max(...f.M) >= .7).length} 个字段达到</div></div></div></div>` + objChips() +
   `<div class="row"><div class="card f2"><h3>背景增益：${T().中文名}<span class="r">拖动 K，观察字段与其他字段组合后的作用</span></h3>
     <div style="display:flex;gap:18px;align-items:center;margin-bottom:6px"><div style="flex:1"><input type="range" id="K" min="0" max="${Kmax}" step="1" value="${S.K}"><div class="kval">${Ks.map(k => `<span>K = ${k.K}${k.K == 0 ? "（单独）" : ""}</span>`).join("")}</div></div>
      <div class="box b" style="min-width:200px"><div class="sub">接收方已有的其他字段数上限</div><div style="font-size:22px;font-weight:700">K = <span id="kv"></span></div><div class="sub" id="kd"></div></div></div>
     <div id="gb" style="height:${50 + order.length * 26}px"></div><div class="legend"><span><i style="background:#9fb3d4"></i>K = 0（单独）</span><span><i style="background:${C.blue}"></i>当前 K</span><span><i style="background:${C.red}"></i>达到直接定级线</span></div></div>
    <div class="card"><h3>字段详情<span class="r" id="fn"></span></h3><div id="gl" style="height:160px"></div><div id="fp"></div></div></div>
   <div class="card"><h3>敏感度矩阵（K = ${Math.min(2, Kmax)}）<span class="r">${c.length > 16 ? `按最大 M 取前 16 个，共 ${c.length} 个候选字段` : `${c.length} 个候选字段`} × ${D.敏感.length} 项敏感数据</span></h3><div id="hm" style="height:${70 + top.length * 28}px"></div></div>`;
  bindObj();
  const bar = chart($("#gb"), { grid: { left: 160, right: 50, top: 8, bottom: 24 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", inverse: true, data: order.map(i => c[i].中文名), axisTick: { show: false }, axisLabel: { fontSize: 11 } },
    series: [{ name: "当前 K", type: "bar", data: [], barWidth: 13, z: 1, label: { show: true, position: "right", fontSize: 11, formatter: p => f2(p.value) }, itemStyle: { borderRadius: [0, 3, 3, 0] }, markLine: { symbol: "none", silent: true, lineStyle: { color: C.red, type: "dashed" }, label: { formatter: "0.7", fontSize: 11 }, data: [{ xAxis: 0.7 }] }, animationDurationUpdate: 500 },
    { name: "K = 0", type: "bar", barGap: "-100%", data: order.map(i => Ks[0].M[i][t]), itemStyle: { color: "#9fb3d4", borderRadius: [0, 3, 3, 0] }, barWidth: 5, z: 2, silent: true }] });
  chart($("#gl"), { grid: { left: 36, right: 16, top: 16, bottom: 26 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: Ks.map(k => "K=" + k.K), boundaryGap: false }, yAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: C.grid } } },
    series: [{ type: "line", data: Ks.map(k => k.M[cur][t]), symbolSize: 8, lineStyle: { width: 3, color: C.blue }, itemStyle: { color: C.blue }, areaStyle: { color: "rgba(37,99,235,.08)" }, label: { show: true, formatter: p => f2(p.value), fontSize: 11 }, markLine: { symbol: "none", silent: true, lineStyle: { color: C.red, type: "dashed" }, label: { show: false }, data: [{ yAxis: 0.7 }] } }] });
  const panel = K => { const f = c[cur], m = Ks[K].M[cur][t], w = Ks[K].见证[cur][t], hasBase = D.字段.some(x => x.角色 == "公开基底");
    return `<div class="box ${m >= .7 ? "r" : "b"}"><div class="sub">M（K = ${K}）</div><div class="big ${m >= .7 ? "red" : ""}">${f3(m)}</div>${m >= .7 ? '<span class="tag r">达到直接定级线</span>' : ""}</div>
     <div class="kv" style="margin-top:8px"><span>${hasBase ? "与公开基底合用的推断精度" : "单独推断精度"}</span><span class="num">${f3(f.单独精度[t])}</span></div>
     <div class="kv"><span>作用最大时的已有字段</span><span>${w.length ? w.map(x => `<span class="tag">${x}</span>`).join("") : "无"}</span></div>
     <div class="kv"><span>等级</span><span>${lv(f.一次等级)} → ${lv(f.二次等级)} ${kindTag(upKind(f))}</span></div>` };
  const show = K => { S.K = K; $("#kv").textContent = K; const m = Ks[K].M, n7 = c.filter((_, i) => m[i][t] >= .7).length; $("#kd").innerHTML = `达到直接定级线：<b class="${n7 ? "red" : ""}">${n7}</b> 个字段`;
    bar.setOption({ series: [{ data: order.map(i => ({ value: m[i][t], itemStyle: { color: m[i][t] >= .7 ? C.red : C.blue, opacity: i == cur ? 1 : .8 } })) }] }); $("#fn").textContent = c[cur].中文名; $("#fp").innerHTML = panel(K) };
  show(S.K); $("#K").oninput = e => show(+e.target.value); bar.on("click", p => { S.sel = order[p.dataIndex]; render() });
  chart($("#hm"), { grid: { left: 160, right: 70, top: 30, bottom: 6 }, tooltip: { formatter: p => `${c[top[top.length - 1 - p.value[1]]].中文名} → ${D.敏感[p.value[0]]}<br>M = ${f3(p.value[2])}` }, xAxis: { type: "category", data: D.敏感, position: "top", axisTick: { show: false }, axisLine: { show: false }, axisLabel: { interval: 0, fontSize: 11 } }, yAxis: { type: "category", data: top.map(i => c[i].中文名).reverse(), axisTick: { show: false }, axisLine: { show: false }, axisLabel: { fontSize: 11 } },
    visualMap: { min: 0, max: 1, orient: "vertical", right: 0, top: "middle", itemHeight: 130, itemWidth: 10, text: ["1", "0"], inRange: { color: ["#eef3fb", "#bcd2f5", "#f3c1a6", "#e5484d"] } }, series: [{ type: "heatmap", data: hm, label: { show: true, fontSize: 10, formatter: p => f2(p.value[2]) }, itemStyle: { borderColor: "#fff", borderWidth: 2, borderRadius: 4 } }] });
}

/* ================= ④ 二次定级 ================= */
function pRegrade() {
  const c = cand(), up = c.filter(f => f.二次等级 > f.一次等级), G = D.GRPO, gap = G && G.参照最优 != null ? Math.abs((G.效用 - G.参照最优) / (G.参照最优 || 1)) * 100 : null;
  const list = c.slice().sort((a, b) => (b.二次等级 - b.一次等级) - (a.二次等级 - a.一次等级) || Math.max(...b.M) - Math.max(...a.M)), cur = (S.sel != null && c[S.sel]) || list[0], k = upKind(cur);
  let why = `<div class="empty">等级不变。</div>`;
  if (k) { const y = cur.依据, w = cur.整体核对上调;
    why = (k == "直接定级" ? `<div class="box r"><b>直接定级</b> ${q(TIP.direct)}<div class="sub">对“${y.对应敏感数据}”的 M = ${f3(Math.max(...cur.M))} ≥ 0.7</div></div>` : k == "联合评估" ? `<div class="box b"><b>联合评估上调</b> ${q(TIP.grpo)}<div class="sub">最大 M = ${f3(Math.max(...cur.M))}</div></div>` : "") +
      (w ? `<div class="box" style="background:var(--amber2);margin-top:8px"><b>整体核对上调</b> ${q(TIP.whole)}<div class="sub">若保持原等级，${w.接收方}可获取的全部字段对“${w.敏感数据}”的推断精度为 <b class="red">${f3(w.精度)}</b></div></div>` : "") +
      (y && y.重新成立的越线组合.length ? `<h3 style="margin-top:14px">若降回 ${LVN(cur.一次等级)}，重新成立的越线组合<span class="r">${y.重新成立的数量} 个</span></h3>` + y.重新成立的越线组合.map(x => `<div class="kv"><span>${x.接收方} → ${x.敏感数据}</span><span>${x.组合.map(n => `<span class="tag">${n}</span>`).join("")} <b class="red num">${f2(x.精度)}</b></span></div>`).join("") : "") }
  const nk = t => up.filter(f => upKind(f) == t).length;
  $("#main").innerHTML = `<div class="pipe"><div class="p"><span class="no">1</span><div><div class="a">直接定级 ${q(TIP.direct)}</div><div class="b">M ≥ 0.7 · ${nk("直接定级")} 个字段</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">2</span><div><div class="a">联合评估（GRPO） ${q(TIP.grpo)}</div><div class="b">其余字段整体确定等级 · ${nk("联合评估")} 个上调</div></div></div><div class="ar">›</div>
    <div class="p"><span class="no">3</span><div><div class="a">${G.严格模式 ? "整体核对 " + q(TIP.whole) : "剩余风险"}</div><div class="b">${G.严格模式 ? nk("整体核对") + " 个追加上调" : `保留 ${D.二次定级后的越线.length} 个越线组合，见“定级效果”`}</div></div></div></div>
   <div class="kpis">${kpi("调", "a", "调高等级的字段", `${up.length} <small>/ ${c.length}</small>`, `直接定级 ${nk("直接定级")} · 联合评估 ${nk("联合评估")} · 整体核对 ${nk("整体核对")}`)}
    ${kpi("组", "g", "越线组合切断比例", `${(G.切断比例 * 100).toFixed(1)}%`, `${D.一次定级下的越线.length} → ${D.二次定级后的越线.length} 个`)}
    ${G ? kpi("效", "b", "联合评估的综合效用 " + q(TIP.grpo), `${f2(G.效用)}`, `只做一次定级 ${f2(G.只做一次定级.效用)}`) + kpi("优", gap != null && gap < 1 ? "g" : "a", "与精确最优的差距", gap == null ? "—" : gap.toFixed(1) + "%", G.参照最优 != null ? `精确最优 ${f2(G.参照最优)}（${G.参照最优求法}）` : "含整体推断项且字段较多，未求精确解") : ""}</div>
   <div class="row"><div class="card f2"><h3>字段调整明细<span class="r">点击字段查看依据</span></h3><div class="scroll" style="max-height:430px"><table><tr><th>字段</th><th>一次等级</th><th>二次等级</th><th>调整方式</th><th>最大 M ${q(TIP.M)}</th></tr>
   ${list.map(f => `<tr class="c ${f == cur ? "sel" : ""}" data-i="${c.indexOf(f)}"><td><b>${f.中文名}</b></td><td>${lv(f.一次等级)}</td><td>${f.二次等级 > f.一次等级 ? lv(f.二次等级) : '<span class="sub">不变</span>'}</td><td>${kindTag(upKind(f))}</td><td class="num"><b class="${Math.max(...f.M) >= .7 ? "red" : ""}">${f3(Math.max(...f.M))}</b></td></tr>`).join("")}</table></div></div>
   <div class="card"><h3>调整依据<span class="r">${cur.中文名}　${lv(cur.一次等级)} → ${lv(cur.二次等级)}</span></h3>${why}</div></div>
   ${G ? `<div class="row"><div class="card f2"><h3>联合评估的训练过程 ${q(TIP.grpo)}<span class="r">每步采样 128 套完整等级方案</span></h3><div id="tc" style="height:220px"></div></div>
   <div class="card"><h3>综合效用的构成</h3><div id="uc" style="height:200px"></div><div class="sub">安全收益 ${q(TIP.S)}　可用性成本 ${q(TIP.Cc)}　聚合推断惩罚 ${q(TIP.P)}　整体推断惩罚 ${q(TIP.W)}</div></div></div>` : ""}`;
  $$("tr.c").forEach(r => r.onclick = () => { S.sel = +r.dataset.i; render() });
  if (!G) return;
  const cu = G.训练曲线; chart($("#tc"), { grid: { left: 56, right: 20, top: 30, bottom: 36 }, legend: { top: 0, right: 0 }, tooltip: { trigger: "axis" }, xAxis: { type: "category", data: cu.map(x => x.步), name: "训练步", nameLocation: "middle", nameGap: 24 }, yAxis: { type: "value", scale: true, name: "综合效用", splitLine: { lineStyle: { color: C.grid } } },
    series: [{ name: "组内平均", type: "line", data: cu.map(x => x.组内平均), showSymbol: false, lineStyle: { color: C.blue, width: 2 }, itemStyle: { color: C.blue } }, { name: "组内最好", type: "line", data: cu.map(x => x.组内最好), showSymbol: false, lineStyle: { color: "#9db8ee", width: 1.5 }, itemStyle: { color: "#9db8ee" } }].concat(G.参照最优 != null ? [{ name: "精确最优", type: "line", data: cu.map(() => G.参照最优), showSymbol: false, lineStyle: { color: C.green, type: "dashed", width: 1.5 }, itemStyle: { color: C.green } }] : []) });
  const a = G.只做一次定级.构成, b = G.效用构成, ks = ["安全收益", "可用性成本", "聚合推断惩罚", "整体推断惩罚"].filter(k => k in b), col = ["#7fa2e8", "#e6a532", "#e5484d", "#9b5de5"];
  chart($("#uc"), { grid: { left: 96, right: 30, top: 30, bottom: 24 }, legend: { top: 0, right: 0, itemWidth: 12, itemHeight: 8 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "value", splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", data: ["联合评估", "只做一次定级"], axisTick: { show: false } },
    series: ks.map((k, i) => ({ name: k, type: "bar", stack: "u", data: [b[k], a[k]], itemStyle: { color: col[i] }, barWidth: 26 })) });
}

/* ================= ⑤ 定级效果 ================= */
function pEffect() {
  const A = D.接收方能力.filter(x => !isRes(x.接收方, x.敏感数据)).slice().reverse(), R = D.换模型复测, res = D.仅凭公开基底可推出 || [], b0 = overCells("定级前"), b1 = overCells("定级后"), F = D.快速估计;
  const bad = R.filter(x => Math.max(x.神经网络, x.梯度提升树) > x.判定线 && !isRes(x.接收方, x.敏感数据)), mx = k => A.length ? Math.max(...A.map(x => x[k])) : 0;
  $("#main").innerHTML = `<div class="kpis">${kpi("险", b1 ? "r" : "g", "越线的“接收方 × 敏感数据”", `<span class="red">${b0}</span> <small>→</small> <span class="${b1 ? "red" : "green"}">${b1}</span>`, "一次定级 → 二次定级")}
    ${kpi("降", "g", "最高推断精度 " + q(TIP.V), `<span class="red">${f2(mx("定级前"))}</span> <small>→</small> <span class="green">${f2(mx("定级后"))}</span>`, "各接收方对无权获取的数据")}
    ${kpi("测", bad.length ? "r" : "g", "换模型复测 " + q("用未参与定级的梯度提升树，对各接收方最终可获取的全部字段重新推断。两种模型中任一超过判定线即视为越线。"), bad.length ? `${bad.length} 处越线` : "通过", `${R.length} 组，神经网络与梯度提升树`)}
    <div class="kpi"><div class="ic b">账</div><div><div class="k">定级台账</div><button class="btn" id="exp" style="margin-top:4px">导出 CSV</button></div></div></div>
   <div class="card"><h3>调级前后，各接收方对无权获取的数据的推断精度<span class="r"><span class="legend"><span><i style="background:#f1b4b4"></i>一次定级</span><span><i style="background:${C.green}"></i>二次定级</span><span><i style="background:${C.ink};width:2px"></i>判定线</span></span></span></h3><div id="wc" style="height:${70 + A.length * 30}px"></div></div>
   <div class="row"><div class="card"><h3>剩余的越线组合 ${q(TIP.combo)}<span class="r">${D.二次定级后的越线.length} 个，切断 ${(D.GRPO.切断比例 * 100).toFixed(1)}%</span></h3>
     ${D.二次定级后的越线.length ? `<div class="scroll" style="max-height:200px"><table><tr><th>接收方</th><th>字段组合</th><th>敏感数据</th><th>推断精度</th></tr>${D.二次定级后的越线.slice(0, 60).map(x => `<tr><td>${x.接收方}</td><td>${x.组合.map(n => `<span class="tag">${n}</span>`).join("")}</td><td>${x.敏感数据}</td><td class="num amber"><b>${f3(x.精度)}</b></td></tr>`).join("")}</table></div><p class="sub">这些组合超出判定线的幅度小，联合评估认为为它们继续上调字段的代价高于收益。如需全部消除，可在“强化学习策略”中提高惩罚系数或开启严格模式后重跑。</p>` : `<div class="empty">已核对的越线组合全部切断。</div>`}
     ${D.整体核对.length ? `<h3 style="margin-top:14px">整体核对 ${q(TIP.whole)}</h3><table><tr><th>接收方</th><th>核对前</th><th>撤出字段</th><th>放回字段</th><th>核对后</th></tr>${D.整体核对.map(r => `<tr><td>${r.接收方}</td><td class="num red"><b>${f3(r.核对前推断精度)}</b></td><td class="num">${r.撤出字段数}</td><td class="num">${r.放回字段数}</td><td class="num green"><b>${f3(r.核对后推断精度)}</b></td></tr>`).join("")}</table>` : ""}
     <h3 style="margin-top:16px">各接收方可获取的候选字段数</h3><table><tr><th>接收方</th><th>一次定级</th><th>二次定级</th></tr>${RECV3().map(r => `<tr><td>${r.名称}</td><td class="num">${cand().filter(f => f.一次等级 <= r.级).length}</td><td class="num"><b>${cand().filter(f => f.二次等级 <= r.级).length}</b></td></tr>`).join("")}</table></div>
    <div class="card" style="flex:1.4"><h3>换模型复测</h3><div class="scroll" style="max-height:330px"><table><tr><th>接收方</th><th>敏感数据</th><th>神经网络</th><th>梯度提升树</th><th>判定线</th><th>结论</th></tr>
     ${R.map(x => { const o = Math.max(x.神经网络, x.梯度提升树) > x.判定线, r = isRes(x.接收方, x.敏感数据); return `<tr><td>${x.接收方}</td><td>${x.敏感数据}</td><td class="num">${f3(x.神经网络)}</td><td class="num">${f3(x.梯度提升树)}</td><td class="num">${x.判定线}</td><td>${r ? `<span class="tag a">公开基底可推出</span>` : o ? '<span class="tag r">越线</span>' : '<span class="tag g">未越线</span>'}</td></tr>` }).join("")}</table></div>
     ${res.length ? `<p class="sub">标为“公开基底可推出”的 ${new Set(res.map(x => x.敏感数据)).size} 项数据由法定公开的信息即可推出 ${q(TIP.base)}，调整候选字段的等级不起作用，需由数据主管方另行评估。</p>` : ""}
     ${F ? `<p class="sub">本任务字段较多，组合的推断精度先由快速估计模型筛选（${F.估计的组合数} 个组合用时 ${F.估计用时秒} 秒），再对 ${F.重新训练核对的组合数} 个重新训练核对；与重新训练相比平均绝对误差 ${F.平均绝对误差}，随机抽查 ${F.随机抽查数} 个被筛掉的组合，实际越线 ${F.抽查中被筛掉却实际越线的} 个。</p>` : ""}</div></div>`;
  chart($("#wc"), { grid: { left: 200, right: 40, top: 8, bottom: 24 }, tooltip: { trigger: "axis", axisPointer: { type: "shadow" } }, xAxis: { type: "value", min: 0, max: 1, splitLine: { lineStyle: { color: C.grid } } }, yAxis: { type: "category", data: A.map(x => x.接收方 + " → " + x.敏感数据), axisTick: { show: false }, axisLabel: { fontSize: 11.5 } },
    series: [{ name: "一次定级", type: "bar", data: A.map(x => x.定级前), itemStyle: { color: "#f1b4b4", borderRadius: [0, 3, 3, 0] }, barWidth: 9, label: { show: true, position: "right", fontSize: 10, color: "#c97b7b", formatter: p => f2(p.value) } }, { name: "二次定级", type: "bar", data: A.map(x => ({ value: x.定级后, itemStyle: { color: x.定级后 > x.判定线 ? C.red : C.green } })), itemStyle: { borderRadius: [0, 3, 3, 0] }, barWidth: 9, label: { show: true, position: "right", fontSize: 10, formatter: p => f2(p.value) } }, { name: "判定线", type: "scatter", symbol: "rect", symbolSize: [2, 26], data: A.map(x => x.判定线), itemStyle: { color: C.ink }, z: 5 }] });
  $("#exp").onclick = () => { const rows = [["字段", "中文名", "类别", "角色", "公开情况", "影响对象", "影响程度", "一次等级", "二次等级", "调整方式", "最大M", "复核调整"]].concat(D.字段.map(f => [f.字段, f.中文名, f.类别, f.角色, f.公开情况, f.影响对象, f.影响程度, f.一次等级, f.二次等级, f.角色 == "候选" ? upKind(f) : "", f.M ? Math.max(...f.M) : "", f.复核调整 ? "是" : ""]));
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob(["﻿" + rows.map(r => r.join(",")).join("\n")], { type: "text/csv" })); a.download = D.id + "_定级台账.csv"; a.click() };
}
boot();
