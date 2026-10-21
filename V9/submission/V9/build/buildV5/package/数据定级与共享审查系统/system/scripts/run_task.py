# -*- coding: utf-8 -*-
"""上传任务的全流程：一次定级（大语言模型初判）→ 复核 → 推断验证 → 二次定级 → 整体核对与换模型复测 → 聚合推断曲线。
复核方式在确认字段目录时选择：“大模型”由另配的大语言模型逐条复核；“人工”在这里跳过，之后在一次定级页的“人工复核”中修改并重算。
用法：python run_task.py <任务编号> [--gpu 自动|处理器|编号]。
进度写到 runtime/uploads/<任务>/进度.json，界面轮询读取。"""
import os, sys, json, time, subprocess, argparse
os.environ.setdefault("PYTHONUTF8", "1"); os.environ.setdefault("PYTHONIOENCODING", "utf-8")      # 子进程统一用 UTF-8，Windows 下中文日志不乱码
SYS = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); ROOT = os.path.dirname(SYS)
sys.path.insert(0, os.path.join(ROOT, "engine", "grading"))
import first_grade, llm_review
sys.path.insert(0, os.path.join(SYS, "scripts")); import device

STEPS = ["一次定级", "复核", "推断验证", "二次定级", "整体核对与复测", "推断曲线"]
TRIG = {"联合评估开始": "二次定级", "整体核对开始": "整体核对与复测"}            # 计算脚本日志中的阶段标记


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("task"); ap.add_argument("--gpu", default="自动")
    a = ap.parse_args(); up = os.path.join(SYS, "runtime", "uploads", a.task); P = os.path.join(up, "进度.json"); T0 = time.time()
    st = dict(状态="运行中", 步骤=[dict(名称=s, 状态="等待", 说明="") for s in STEPS], 日志=[], 设备="", 开始=time.strftime("%Y-%m-%d %H:%M:%S")); t_prev = 0
    how = json.load(open(os.path.join(up, "meta.json"), encoding="utf-8")).get("复核方式", "人工")

    def save():
        st["用时秒"] = t_prev + round(time.time() - T0); json.dump(st, open(P + ".tmp", "w", encoding="utf-8"), ensure_ascii=False); os.replace(P + ".tmp", P)

    def step(name, state, note=None):
        s = next(x for x in st["步骤"] if x["名称"] == name); s["状态"] = state
        if note is not None:
            s["说明"] = note
        save()

    def log(line):
        st["日志"] = (st["日志"] + [line])[-40:]; save()

    try:
        cat = os.path.join(up, a.task + ".csv"); n = sum(1 for _ in open(cat, encoding="utf-8")) - 1
        if not first_grade._env().get("DEEPSEEK_API_KEY"):
            raise RuntimeError("一次定级需要大语言模型，但没有找到密钥：请在 secrets/deepseek.env 中填写 DEEPSEEK_API_KEY（格式见 secrets/deepseek.env.example）")
        step("一次定级", "进行中", f"0 / {n}")
        rows, tokens = first_grade.main(cat, on_row=lambda k, r: (step("一次定级", "进行中", f"{k} / {n}"), log(f"一次定级 {r['中文名']}：{r.get('影响对象')} × {r.get('影响程度')} → {r['一次等级']} 级")))
        step("一次定级", "完成", f"{n} 个字段，消耗词元 {tokens}")
        if how == "大模型":
            step("复核", "进行中", f"0 / {n}")
            fix, tk, model = llm_review.review(rows, on_row=lambda k, r, x: (step("复核", "进行中", f"{k} / {n}"), log(f"复核 {r['中文名']}：" + (f"改为 {x['影响对象']} × {x['影响程度']}（{x['理由']}）" if x else "同意"))))
            json.dump(fix, open(cat[:-4] + "_复核.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            step("复核", "完成", f"{model} 调整 {len(fix)} 个字段，消耗词元 {tk}")
        else:
            step("复核", "完成", "人工复核：完成后可在一次定级页修改并重算")
        g, st["设备"] = device.pick(a.gpu); log(f"计算设备：{st['设备']}")
        py = sys.executable; bs = os.path.join(SYS, "scripts", "build_samples.py")
        cur = "推断验证"; step(cur, "进行中")
        p = subprocess.Popen([py, "-u", bs, a.task, "--gpu", str(g)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
        for line in p.stdout:
            line = line.rstrip()
            if not line or "Warning" in line or "warn(" in line:
                continue
            log(line)
            for k, name in TRIG.items():
                if k in line and STEPS.index(name) > STEPS.index(cur):
                    step(cur, "完成"); cur = name; step(cur, "进行中")
        if p.wait() != 0:
            raise RuntimeError("推断验证或二次定级失败，见日志")
        for s in st["步骤"][2:5]:
            s["状态"] = "完成"
        step("推断曲线", "进行中")
        q = subprocess.run([py, bs, a.task, "--gpu", str(g), "--curves"], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
        if q.returncode != 0:
            raise RuntimeError("推断曲线失败：" + q.stderr[-300:])
        step("推断曲线", "完成"); st["状态"] = "完成"; log(f"全部完成，累计用时 {st['用时秒']} 秒"); save()
    except Exception as e:
        for s in st["步骤"]:
            if s["状态"] == "进行中":
                s["状态"] = "失败"
        st["状态"] = "失败"; log("失败：" + str(e)[:400]); save(); sys.exit(1)


if __name__ == "__main__":
    main()
