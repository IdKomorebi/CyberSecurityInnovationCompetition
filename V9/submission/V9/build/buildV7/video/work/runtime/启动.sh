#!/usr/bin/env bash
cd "$(dirname "$0")"
export PYTHONUTF8=1
echo "数据定级与共享审查系统：浏览器打开 http://127.0.0.1:8788/frontend/ ，按 Ctrl+C 停止服务。"
( sleep 2; (xdg-open http://127.0.0.1:8788/frontend/ || open http://127.0.0.1:8788/frontend/) >/dev/null 2>&1 ) &
python3 system/scripts/serve.py 8788 自动
