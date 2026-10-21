# -*- coding: utf-8 -*-
"""打包可执行程序：系统（当前版本）、算法、规则与数据、大模型配置、启动脚本与使用说明。
用法：python scripts/make_package.py
输出：deliverables/<队长>-<作品名称>-可执行程序.zip"""
import os, shutil, zipfile, json

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); V8 = os.path.dirname(os.path.dirname(HERE)); PROJ = os.path.dirname(V8)
NAME = "杜浩存-面向聚合推断威胁的数据定级与共享审查系统-可执行程序"; STAGE = os.path.join(HERE, "build", "package", NAME)
SKIP_DIRS = {"__pycache__", "shots", "logs", "回收站", "submission", ".git"}

def copy(src, dst):
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith((".pyc", ".log", ".pid")):
                continue
            s = os.path.join(root, f); d = os.path.join(dst, os.path.relpath(s, src)); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(s, d)

shutil.rmtree(os.path.dirname(STAGE), ignore_errors=True); os.makedirs(STAGE)
copy(V8, os.path.join(STAGE, "system"))                                   # 系统：界面、服务端与脚本、内置任务结果、推断缓存
copy(os.path.join(PROJ, "engine"), os.path.join(STAGE, "engine"))          # 算法
for sub in ("rules", "catalog", "raw", "upload_examples"):
    copy(os.path.join(PROJ, "data", sub), os.path.join(STAGE, "data", sub))
os.makedirs(os.path.join(STAGE, "secrets")); shutil.copy2(os.path.join(PROJ, "secrets", "deepseek.env"), os.path.join(STAGE, "secrets", "deepseek.env"))
for f in ("README.md", "CHANGELOG.md"):                                    # 系统目录下的开发记录不放入
    p = os.path.join(STAGE, "system", f)
    if os.path.exists(p):
        os.remove(p)

open(os.path.join(STAGE, "requirements.txt"), "w", encoding="utf-8").write("numpy\npandas\nscikit-learn\nscipy\ntorch\nopenpyxl\n")
open(os.path.join(STAGE, "启动.bat"), "w", encoding="gbk", newline="\r\n").write("""@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
set PY=python
where python >nul 2>nul || set PY=py
echo 正在启动数据定级与共享审查系统，浏览器将自动打开 http://127.0.0.1:8788/frontend/
echo 关闭本窗口即停止服务。
start "" http://127.0.0.1:8788/frontend/
%PY% system\\scripts\\serve.py 8788 自动
pause
""")
open(os.path.join(STAGE, "启动.sh"), "w", encoding="utf-8", newline="\n").write("""#!/usr/bin/env bash
cd "$(dirname "$0")"
export PYTHONUTF8=1
echo "数据定级与共享审查系统：浏览器打开 http://127.0.0.1:8788/frontend/ ，按 Ctrl+C 停止服务。"
( sleep 2; (xdg-open http://127.0.0.1:8788/frontend/ || open http://127.0.0.1:8788/frontend/) >/dev/null 2>&1 ) &
python3 system/scripts/serve.py 8788 自动
""")
os.chmod(os.path.join(STAGE, "启动.sh"), 0o755)
open(os.path.join(STAGE, "使用说明.txt"), "w", encoding="utf-8-sig").write("""面向聚合推断威胁的数据定级与共享审查系统 · 使用说明

一、运行环境
  Python 3.10 或更高版本（Windows、Linux、macOS 均可）。有无显卡均可，有显卡时自动选用空闲显存最多的一张，没有时用处理器。

二、安装依赖（首次运行前执行一次）
  在本目录打开命令行，执行：
    pip install -r requirements.txt
  说明：只想查看内置结果时可以跳过这一步，系统会以“演示方式”运行，只需 Python 自带的标准库。

三、启动
  Windows：双击“启动.bat”。
  Linux / macOS：在本目录执行 bash 启动.sh。
  也可以手动执行：python system/scripts/serve.py 8788
  启动后浏览器打开 http://127.0.0.1:8788/frontend/ 。关闭命令行窗口即停止服务。
  第二个参数可指定计算设备：自动（默认）、处理器，或显卡编号，例如 python system/scripts/serve.py 8788 处理器

四、大模型配置
  secrets/deepseek.env 中已写好一次定级与起草字段目录所用的 DeepSeek 接口密钥，以及复核所用的阿里云百炼 Qwen 接口密钥，开箱即可使用新建任务和大模型复核。如需换用自己的密钥，修改该文件即可。

五、使用
  1. 查看内置结果：启动后默认打开 NEM 2024 任务，也可在左侧“任务管理”中点击任务卡片切换，依次查看六页：字段本身（一次定级、单独推断）、聚合推断风险（考虑背景知识的单字段风险、越线组合）、定级与效果（二次定级、定级效果）。每页右上角“本页导览与参数”有页面说明与可调参数。
  2. 新建任务：任务管理页点“新建任务”，上传一张 CSV 或 Excel 表格（data/upload_examples 下有 3 份示例数据），确认大模型起草的字段目录（重点确认公开情况和保护对象），点“确认目录，开始定级”，后台自动完成全流程。
  3. 复核：一次定级页点“人工复核”的“详情”，可请另一个大模型复核，或逐条修改，保存后自动重算。
  4. 调参重算：在“本页导览与参数”的“参数调整”页修改后点“应用并重跑”。背景字段数上限 K 默认“自动”，由系统在 2、3 中选定。
  5. 越线组合页可选组合最大字段数，超出已重新训练范围的由估计器当场打分，可点“重新训练 N 个组合”核对（需完整依赖）。

六、目录
  system/   系统：界面 frontend/、服务端与计算脚本 scripts/、内置任务结果 samples/、推断缓存与上传任务 runtime/
  engine/   算法：一次定级与复核、二次定级与强化学习、推断模型与快速估计、换模型复测
  data/     规则库（GB/T 43697）、字段目录、原始数据、示例数据
  secrets/  大模型接口配置

七、常见问题
  1. 页面提示“演示方式”：说明没有装好依赖（主要是 torch），按第二步安装后重新启动。
  2. 端口被占用：把命令中的 8788 换成其他端口，例如 8790，浏览器地址同步修改。
  3. 大模型调用失败：检查网络；程序在经代理和直连之间会自动切换重试。
""")
out = os.path.join(HERE, "deliverables", NAME + ".zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(os.path.dirname(STAGE)):
        for f in files:
            p = os.path.join(root, f); z.write(p, os.path.relpath(p, os.path.dirname(STAGE)))
print(out, round(os.path.getsize(out) / 2 ** 20, 1), "MB")
