# -*- coding: utf-8 -*-
"""系统服务。用法：python serve.py [端口] [显卡编号]，浏览器打开 http://127.0.0.1:端口/frontend/

演示方式：只读取内置的已算好结果，不需要显卡和深度学习库。
完整方式：本机装有深度学习库、且存在已缓存的推断精度时，界面上可以修改参数并重跑二次定级。
"""
import os, sys, json, subprocess, threading, importlib.util, http.server, functools
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PROJ = os.path.dirname(ROOT)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8782; GPU = sys.argv[2] if len(sys.argv) > 2 else "0"
FULL = importlib.util.find_spec("torch") is not None; JOB = dict(状态="空闲", 任务="", 日志="")
ALLOW = {"公众判定线": (0.5, 0.95), "其他判定线": (0.5, 0.95), "K": (0, 2), "直接定级线": (0.5, 0.95), "beta": (0, 10), "lam": (0.1, 3), "eta": (0, 10), "sigma": (0.1, 2),
         "rho": (0, 20), "rho_w": (0, 20), "steps": (50, 2000), "group": (16, 512)}


def cached(task):
    return os.path.exists(os.path.join(ROOT, "runtime", "cache", task + ".pkl"))


def run(task, params):
    JOB.update(状态="运行中", 任务=task, 日志="")
    p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_samples.py"), task, "--gpu", GPU, "--regrade", "--params", json.dumps(params, ensure_ascii=False)],
                       capture_output=True, text=True, cwd=PROJ)
    tail = [l for l in (p.stdout + p.stderr).splitlines() if "Warning" not in l][-6:]
    JOB.update(状态="完成" if p.returncode == 0 else "失败", 日志="\n".join(tail))


class H(http.server.SimpleHTTPRequestHandler):
    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode(); self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/api/status"):
            tasks = [f[:-5] for f in os.listdir(os.path.join(ROOT, "samples")) if f.endswith(".json")]
            return self._json(dict(完整方式=FULL, 可重跑=[t for t in tasks if FULL and cached(t)], 作业=JOB))
        return super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/api/rerun"):
            return self._json(dict(错误="未知接口"), 404)
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}"); task = str(body.get("任务", "")); raw = body.get("参数", {})
        if not FULL or not task.isalnum() or not cached(task):
            return self._json(dict(错误="当前为演示方式，或该任务没有缓存的推断精度，不能重跑"), 400)
        if JOB["状态"] == "运行中":
            return self._json(dict(错误="已有作业在运行"), 409)
        params = {"严格模式": bool(raw.get("严格模式", False))}
        for k, (lo, hi) in ALLOW.items():
            if k in raw:
                v = float(raw[k]); params[k] = int(v) if k in ("K", "steps", "group") else v
                if not lo <= v <= hi:
                    return self._json(dict(错误=f"参数 {k} 超出允许范围 {lo}~{hi}"), 400)
        threading.Thread(target=run, args=(task, params), daemon=True).start(); self._json(dict(已提交=True))

    def log_message(self, *a):
        pass


print(f"http://127.0.0.1:{port}/frontend/  （{'完整方式' if FULL else '演示方式'}）")
http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(H, directory=ROOT)).serve_forever()
