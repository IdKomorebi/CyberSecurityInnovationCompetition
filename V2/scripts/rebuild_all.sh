#!/bin/bash
# 依次重新生成演示任务。用法：rebuild_all.sh [显卡编号] [任务...]
set -euo pipefail
D="$(cd "$(dirname "$0")/.." && pwd)"
PY=${PY:-python}
G=${1:-0}
if [ "$#" -gt 0 ]; then shift; fi
if [ "$#" -eq 0 ]; then set -- insurance ieee30 pjm community; fi
mkdir -p "$D/runtime/logs"
for task in "$@"; do
    "$PY" "$D/scripts/build_samples.py" "$task" --gpu "$G" > "$D/runtime/logs/build_$task.log" 2>&1
done
