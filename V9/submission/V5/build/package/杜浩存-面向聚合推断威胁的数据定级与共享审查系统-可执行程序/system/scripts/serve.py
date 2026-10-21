# -*- coding: utf-8 -*-
"""系统服务。用法：python serve.py [端口] [显卡编号|自动]，浏览器打开 http://127.0.0.1:端口/frontend/

演示方式：只读取内置的已算好结果，不需要显卡和深度学习库。
完整方式：本机装有深度学习库时，可以修改参数重跑二次定级，也可以上传数据表新建任务（全流程在后台运行，自动选择显卡或处理器）。

接口：
  GET  /api/status                    服务状态、任务列表、当前作业
  POST /api/rerun                     {任务, 参数}：改参数重跑二次定级及之后的步骤
  POST /api/upload?name=&title=       请求体为数据表文件（CSV 或 Excel）：保存并逐列画像
  POST /api/draft                     {任务, 说明}：大语言模型起草字段目录（后台作业）
  GET  /api/upload?任务=              上传任务的画像、目录草稿、进度
  POST /api/start                     {任务, 目录, 时间序列, 设备, 复核方式, 说明}：用户确认目录后开始全流程（后台作业）
  POST /api/fix                       {任务, 调整}：保存一次定级的人工复核意见，按复核后的等级重做二次定级及之后的步骤（后台作业）
  POST /api/llmreview                 {任务}：请另配的大模型逐条复核一次定级的初判（后台作业），意见供人工采纳
  GET  /api/llmreview?任务=           读取大模型复核意见
  POST /api/combos                    {任务, 保护对象, 规模}：用估计器当场计算规模更大的最小越线组合（后台作业）
  GET  /api/combos?任务=&保护对象=&规模=  读取已算好的结果
  POST /api/order                     {顺序}：保存任务卡片的排列顺序
  POST /api/delete                    {任务}：删除任务（相关文件移到 runtime/回收站/，可手动恢复）
"""
import os, sys, json, time, subprocess, threading, importlib.util, http.server, functools, urllib.parse
os.environ.setdefault("PYTHONUTF8", "1"); os.environ.setdefault("PYTHONIOENCODING", "utf-8")      # 子进程统一用 UTF-8，Windows 下中文日志不乱码
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PROJ = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, os.path.join(PROJ, "engine", "grading"))
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8788; GPU = sys.argv[2] if len(sys.argv) > 2 else "自动"            # 自动 / 处理器 / 显卡编号
FULL = importlib.util.find_spec("torch") is not None; JOB = dict(状态="空闲", 任务="", 类型="", 日志="")
UP = os.path.join(ROOT, "runtime", "uploads"); os.makedirs(UP, exist_ok=True)
ALLOW = {"公众判定线": (0.5, 0.95), "其他判定线": (0.5, 0.95), "K": (0, 4), "直接定级线": (0.5, 0.95), "beta": (0, 10), "lam": (0.1, 3), "eta": (0, 10), "sigma": (0.1, 2),
         "rho": (0, 20), "rho_w": (0, 20), "steps": (50, 2000), "group": (16, 512)}
CATS, OPEN, ROLES = ("行业数据", "个人信息", "公共数据", "组织数据"), ("已公开", "有条件开放", "未公开"), ("候选字段", "保护对象", "不参与")


def cached(task):
    return os.path.exists(os.path.join(ROOT, "runtime", "cache", task + ".pkl"))


def jload(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


def jsave(p, obj):
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


ORDER = os.path.join(ROOT, "runtime", "任务顺序.json"); BUILTIN = ["nem", "ieee30", "pjm", "community", "insurance"]


def task_list():
    names = [f[:-5] for f in os.listdir(os.path.join(ROOT, "samples")) if f.endswith(".json") and "_组合曲线" not in f]
    order = jload(ORDER, []) or BUILTIN
    return [k for k in order if k in names] + sorted((k for k in names if k not in order), key=lambda k: (k not in BUILTIN, k))


def uploads():
    out = []
    for t in sorted(os.listdir(UP)):
        m = jload(os.path.join(UP, t, "meta.json"))
        if m:
            out.append(dict(任务=t, 名称=m["名称"], 状态=m["状态"], 行数=m["行数"], 列数=m["列数"]))
    return out


def gpu_arg():
    return "自动" if GPU == "自动" else GPU


def run(task, params):
    JOB.update(状态="运行中", 任务=task, 类型="重跑", 日志="")
    import device
    g, _ = device.pick(GPU)
    p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_samples.py"), task, "--gpu", str(g), "--regrade", "--params", json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROJ)
    tail = [l for l in (p.stdout + p.stderr).splitlines() if "Warning" not in l][-6:]
    JOB.update(状态="完成" if p.returncode == 0 else "失败", 日志="\n".join(tail))


def draft(task, note):
    JOB.update(状态="运行中", 任务=task, 类型="起草目录", 日志="大语言模型正在起草字段目录…")
    d = os.path.join(UP, task); m = jload(os.path.join(d, "meta.json"))
    try:
        import catalog_draft
        rows, ts, tokens, model = catalog_draft.draft(jload(os.path.join(d, "画像.json")), m["名称"], note)
        ts = ts or any(r["类型"] == "时间" for r in rows)
        jsave(os.path.join(d, "目录草稿.json"), dict(字段=rows, 时间序列=ts, 模型=model, 词元=tokens, 说明=note))
        m["状态"] = "待确认"; jsave(os.path.join(d, "meta.json"), m); JOB.update(状态="完成", 日志=f"起草完成，消耗词元 {tokens}")
    except Exception as e:                                           # 大模型不可用时退回手工填写：列名作中文名，其余取保守的默认值
        rows = [dict(字段=p["字段"], 类型=p["类型"], 中文名=p["字段"], 说明="", 类别="行业数据", 公开情况="未公开", 建议角色="不参与" if p["类型"] in ("时间", "文本") else "候选字段", 理由="")
                for p in jload(os.path.join(d, "画像.json"))]
        jsave(os.path.join(d, "目录草稿.json"), dict(字段=rows, 时间序列=any(r["类型"] == "时间" for r in rows), 模型="未使用", 词元=0, 说明=note, 提示="大语言模型不可用，请手工填写字段目录。原因：" + str(e)[:200]))
        m["状态"] = "待确认"; jsave(os.path.join(d, "meta.json"), m); JOB.update(状态="完成", 日志="大语言模型不可用，已生成空白目录供手工填写")


def pipeline(task):
    JOB.update(状态="运行中", 任务=task, 类型="新建", 日志="")
    d = os.path.join(UP, task); m = jload(os.path.join(d, "meta.json")); m["状态"] = "运行中"; jsave(os.path.join(d, "meta.json"), m)
    p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "run_task.py"), task, "--gpu", m.get("设备") or gpu_arg()], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROJ)
    ok = p.returncode == 0; m["状态"] = (jload(os.path.join(d, "进度.json"), {}).get("状态") or "完成") if ok else "失败"; jsave(os.path.join(d, "meta.json"), m)
    JOB.update(状态="完成" if ok else "失败", 日志="\n".join((p.stdout + p.stderr).splitlines()[-4:]))


def fix_file(task):
    """复核意见保存位置：上传任务在自己的目录；内置任务在本版本的 runtime/复核/（不改各版本共用的 data/catalog/）。"""
    up = os.path.join(UP, task)
    if os.path.isdir(up):
        return os.path.join(up, task + "_复核.json")
    os.makedirs(os.path.join(ROOT, "runtime", "复核"), exist_ok=True); return os.path.join(ROOT, "runtime", "复核", task + "_复核.json")


def opinion_file(task):
    up = os.path.join(UP, task)
    if os.path.isdir(up):
        return os.path.join(up, "大模型复核意见.json")
    os.makedirs(os.path.join(ROOT, "runtime", "复核"), exist_ok=True); return os.path.join(ROOT, "runtime", "复核", task + "_大模型复核意见.json")


def combos_file(task, target, k):
    return os.path.join(ROOT, "runtime", "cache", f"{task}_组合_{target}_k{k}.json")


def combos_job(task, target, k):
    JOB.update(状态="运行中", 任务=task, 类型="越线组合", 日志=f"正在用估计器计算规模不超过 {k} 的越线组合…")
    p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "combos.py"), task, "--target", target, "--k", str(k), "--gpu", gpu_arg()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROJ)
    tail = [l for l in (p.stdout + p.stderr).splitlines() if "Warning" not in l and "warn(" not in l][-4:]
    JOB.update(状态="完成" if p.returncode == 0 else "失败", 日志="\n".join(tail))


def llm_review_job(task):
    JOB.update(状态="运行中", 任务=task, 类型="大模型复核", 日志="另配的大模型正在逐条复核…")
    try:
        import llm_review
        D = jload(os.path.join(ROOT, "samples", task + ".json"))
        rows = [dict(字段=f["字段"], 中文名=f["中文名"], 类别=f["类别"], 公开情况=f["公开情况"], 说明=f.get("说明", ""), 角色="保护对象" if f["角色"] == "敏感" else "候选字段",
                     影响对象=f["初判"]["影响对象"], 影响程度=f["初判"]["影响程度"], 理由=f["初判"]["理由"]) for f in D["字段"] if f["角色"] in ("候选", "敏感")]
        fix, tokens, model = llm_review.review(rows, on_row=lambda k, r, x: JOB.update(日志=f"已复核 {k} / {len(rows)}"))
        jsave(opinion_file(task), dict(模型=model, 时间=time.strftime("%Y-%m-%d %H:%M"), 字段数=len(rows), 词元=tokens, 意见=fix))
        JOB.update(状态="完成", 日志=f"{model} 复核 {len(rows)} 个字段，提出 {len(fix)} 条不同意见")
    except Exception as e:
        JOB.update(状态="失败", 日志="大模型复核失败：" + str(e)[:300])


class H(http.server.SimpleHTTPRequestHandler):
    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode(); self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def _body(self, limit=None):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if limit and n > limit:
            raise ValueError("文件超过 200 MB")
        return self.rfile.read(n)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); qs = urllib.parse.parse_qs(u.query)
        if u.path == "/api/status":
            tasks = task_list()
            try:
                import llm_review; rv = llm_review.config()["model"]
            except Exception:
                rv = ""
            return self._json(dict(完整方式=FULL, 复核模型=rv, 任务列表=tasks, 可重跑=[t for t in tasks if FULL and cached(t)], 上传任务=uploads(), 作业=JOB))
        if u.path == "/api/combos":
            t, y, k = (qs.get("任务") or [""])[0], (qs.get("保护对象") or [""])[0], (qs.get("规模") or ["0"])[0]
            return self._json(dict(结果=jload(combos_file(t, y, k)) if t.isalnum() and k.isdigit() else None))
        if u.path == "/api/llmreview":
            t = (qs.get("任务") or [""])[0]
            return self._json(dict(意见=jload(opinion_file(t)) if t.isalnum() else None))
        if u.path == "/api/upload":
            t = (qs.get("任务") or [""])[0]; d = os.path.join(UP, t)
            if not t.isalnum() or not os.path.isdir(d):
                return self._json(dict(错误="没有这个上传任务"), 404)
            return self._json(dict(任务=t, 信息=jload(os.path.join(d, "meta.json")), 画像=jload(os.path.join(d, "画像.json")), 草稿=jload(os.path.join(d, "目录草稿.json")),
                                   目录=jload(os.path.join(d, "目录.json")), 进度=jload(os.path.join(d, "进度.json"))))
        return super().do_GET()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path); qs = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/api/upload":
                return self.upload(qs)
            body = json.loads(self._body() or b"{}")
            if u.path == "/api/rerun":
                return self.rerun(body)
            if u.path == "/api/draft":
                return self.start_job(draft, str(body.get("任务", "")), str(body.get("说明", ""))[:500])
            if u.path == "/api/start":
                return self.start(body)
            if u.path == "/api/fix":
                return self.fix(body)
            if u.path == "/api/order":
                names = set(task_list()); order = [str(k) for k in body.get("顺序", []) if str(k) in names]
                jsave(ORDER, order + [k for k in task_list() if k not in order]); return self._json(dict(顺序=task_list()))
            if u.path == "/api/delete":
                return self.delete(str(body.get("任务", "")))
            if u.path == "/api/combos":
                t, y, k = str(body.get("任务", "")), str(body.get("保护对象", "")), int(body.get("规模", 4))
                if not FULL or not t.isalnum() or not cached(t):
                    return self._json(dict(错误="当前为演示方式，或该任务没有推断缓存，不能当场计算"), 400)
                if not 2 <= k <= 6:
                    return self._json(dict(错误="组合规模取 2 至 6"), 400)
                return self.start_job(combos_job, t, y, k)
            if u.path == "/api/llmreview":
                t = str(body.get("任务", ""))
                if not t.isalnum() or not os.path.exists(os.path.join(ROOT, "samples", t + ".json")):
                    return self._json(dict(错误="没有这个任务"), 404)
                return self.start_job(llm_review_job, t)
            return self._json(dict(错误="未知接口"), 404)
        except Exception as e:
            return self._json(dict(错误=str(e)[:300]), 400)

    def upload(self, qs):
        if not FULL:
            return self._json(dict(错误="当前为演示方式，不能新建任务"), 400)
        name = (qs.get("name") or ["data.csv"])[0]; title = ((qs.get("title") or [""])[0] or os.path.splitext(name)[0])[:60]; ext = os.path.splitext(name)[1].lower()
        if ext not in (".csv", ".xlsx", ".xlsm", ".xls"):
            return self._json(dict(错误="只支持 CSV 或 Excel（xlsx）表格"), 400)
        import tabular
        t = "u" + time.strftime("%Y%m%d%H%M%S"); d = os.path.join(UP, t); os.makedirs(d); fn = "数据" + ext
        open(os.path.join(d, fn), "wb").write(self._body(200 << 20))
        try:
            df = tabular.read_table(os.path.join(d, fn))
        except Exception as e:
            return self._json(dict(错误="读不出这个表格：" + str(e)[:200]), 400)
        if len(df) < 50 or df.shape[1] < 2:
            return self._json(dict(错误=f"表格只有 {len(df)} 行、{df.shape[1]} 列；至少需要 50 行、2 列才能做推断验证"), 400)
        prof = tabular.profile(df); jsave(os.path.join(d, "画像.json"), prof)
        jsave(os.path.join(d, "meta.json"), dict(名称=title, 原文件名=name, 数据文件=fn, 行数=len(df), 列数=df.shape[1], 状态="待起草", 创建时间=time.strftime("%Y-%m-%d %H:%M:%S")))
        return self._json(dict(任务=t, 行数=len(df), 列数=df.shape[1], 画像=prof))

    def rerun(self, body):
        task = str(body.get("任务", "")); raw = body.get("参数", {})
        if not FULL or not task.isalnum() or not cached(task):
            return self._json(dict(错误="当前为演示方式，或该任务没有缓存的推断精度，不能重跑"), 400)
        D = jload(os.path.join(ROOT, "samples", task + ".json"), {}); kmax = max(3, min(int(D.get("组合上限", 3)) - 1, 4))
        params = {"严格模式": bool(raw.get("严格模式", False))}
        if str(raw.get("K", "自动")) == "自动":                              # 背景预算 K：自动在 2、3 中选定，或手动指定
            raw = {k: v for k, v in raw.items() if k != "K"}; params["K"] = "自动"
        elif float(raw["K"]) > kmax:
            return self._json(dict(错误=f"这个任务的背景字段数上限 K 最大为 {kmax}"), 400)
        if raw.get("只保护"):
            params["只保护"] = str(raw["只保护"])[:64]
        for k, (lo, hi) in ALLOW.items():
            if k in raw:
                v = float(raw[k]); params[k] = int(v) if k in ("K", "steps", "group") else v
                if not lo <= v <= hi:
                    return self._json(dict(错误=f"参数 {k} 超出允许范围 {lo}~{hi}"), 400)
        return self.start_job(run, task, params)

    def start(self, body):
        t = str(body.get("任务", "")); d = os.path.join(UP, t)
        if not t.isalnum() or not os.path.isdir(d):
            return self._json(dict(错误="没有这个上传任务"), 404)
        prof = {p["字段"]: p for p in jload(os.path.join(d, "画像.json"))}; rows = []
        for r in body.get("目录", []):
            c = str(r.get("字段"))
            if c not in prof:
                return self._json(dict(错误=f"表格中没有列 {c}"), 400)
            row = dict(字段=c, 中文名=str(r.get("中文名") or c)[:40], 类别=r.get("类别") if r.get("类别") in CATS else "行业数据", 公开情况=r.get("公开情况") if r.get("公开情况") in OPEN else "未公开",
                       说明=str(r.get("说明", ""))[:120], 角色=r.get("角色") if r.get("角色") in ROLES else "候选字段", 类型=prof[c]["类型"])
            if row["类型"] in ("时间", "文本"):
                row["角色"] = "不参与"
            rows.append(row)
        nc, nt = sum(r["角色"] == "候选字段" for r in rows), sum(r["角色"] == "保护对象" for r in rows)
        if not nc or not nt:
            return self._json(dict(错误="至少需要一个候选字段和一个保护对象"), 400)
        jsave(os.path.join(d, "目录.json"), rows)
        import csv
        with open(os.path.join(d, t + ".csv"), "w", encoding="utf-8", newline="") as f:          # 一次定级只看参与推断的字段
            w = csv.DictWriter(f, fieldnames=["字段", "中文名", "类别", "公开情况", "说明", "角色"], extrasaction="ignore"); w.writeheader(); w.writerows([r for r in rows if r["角色"] != "不参与"])
        m = jload(os.path.join(d, "meta.json")); m.update(设备="处理器" if body.get("设备") == "处理器" else "", 复核方式="大模型" if body.get("复核方式") == "大模型" else "人工", 时间序列=bool(body.get("时间序列")), 说明=str(body.get("说明", ""))[:300], 类别=max(CATS, key=lambda k: sum(r["类别"] == k for r in rows)))
        jsave(os.path.join(d, "meta.json"), m)
        return self.start_job(pipeline, t)

    def fix(self, body):
        from first_grade import RULES
        task = str(body.get("任务", "")); D = jload(os.path.join(ROOT, "samples", task + ".json")) if task.isalnum() else None
        if not FULL or not D or not cached(task):
            return self._json(dict(错误="当前为演示方式，或该任务没有缓存的推断精度，不能重算"), 400)
        names = {f["字段"] for f in D["字段"]}; fix = []
        for x in body.get("调整", []):
            if x.get("字段") not in names or x.get("影响对象") not in RULES["影响对象"] or x.get("影响程度") not in RULES["影响程度"]:
                return self._json(dict(错误=f"复核意见不完整：{x.get('字段')}"), 400)
            if not str(x.get("理由", "")).strip():
                return self._json(dict(错误=f"请写明复核理由：{x.get('字段')}"), 400)
            fix.append(dict(字段=x["字段"], 影响对象=x["影响对象"], 影响程度=x["影响程度"], 理由=str(x["理由"])[:200], 来源=str(x.get("来源") or "人工复核")[:40]))
        jsave(fix_file(task), fix)
        params = {k: v for k, v in D["参数"].items() if k != "只保护"}
        return self.start_job(run, task, params)

    def delete(self, t):
        import shutil
        if not t.isalnum():
            return self._json(dict(错误="任务编号不对"), 400)
        if JOB["状态"] == "运行中" and JOB["任务"] == t:
            return self._json(dict(错误="这个任务正在计算，不能删除"), 409)
        bin_ = os.path.join(ROOT, "runtime", "回收站", t + "_" + time.strftime("%Y%m%d%H%M%S")); moved = []
        for p in [os.path.join(ROOT, "samples", t + ".json"), os.path.join(ROOT, "samples", t + "_组合曲线.json"), os.path.join(ROOT, "runtime", "cache", t + ".pkl"),
                  os.path.join(UP, t), fix_file(t) if not os.path.isdir(os.path.join(UP, t)) else "", opinion_file(t) if not os.path.isdir(os.path.join(UP, t)) else ""]:
            if p and os.path.exists(p):
                os.makedirs(bin_, exist_ok=True); shutil.move(p, os.path.join(bin_, os.path.basename(p))); moved.append(os.path.basename(p))
        if not moved:
            return self._json(dict(错误="没有这个任务"), 404)
        jsave(ORDER, [k for k in jload(ORDER, []) if k != t])
        return self._json(dict(已删除=t, 移到=os.path.relpath(bin_, ROOT), 文件=moved))

    def start_job(self, fn, *args):
        if JOB["状态"] == "运行中":
            return self._json(dict(错误="已有作业在运行，请稍候"), 409)
        threading.Thread(target=fn, args=args, daemon=True).start(); JOB.update(状态="运行中", 任务=args[0]); return self._json(dict(已提交=True))

    def log_message(self, *a):
        pass


print(f"http://127.0.0.1:{port}/frontend/  （{'完整方式' if FULL else '演示方式'}）")
http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(H, directory=ROOT)).serve_forever()
