@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
set PY=python
where python >nul 2>nul || set PY=py
echo 正在启动数据定级与共享审查系统，浏览器将自动打开 http://127.0.0.1:8788/frontend/
echo 关闭本窗口即停止服务。
start "" http://127.0.0.1:8788/frontend/
%PY% system\scripts\serve.py 8788 自动
pause
