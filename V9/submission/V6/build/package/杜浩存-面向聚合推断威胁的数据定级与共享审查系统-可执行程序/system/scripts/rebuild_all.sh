#!/bin/bash
# 依次重新生成演示任务。用法：rebuild_all.sh <显卡编号> [任务...]
D="$(cd "$(dirname "$0")/.." && pwd)"
PY=${PY:-python}; G=${1:-0}; shift
for k in ${@:-insurance ieee30 pjm community}; do $PY "$D/scripts/build_samples.py" $k --gpu $G > "$D/runtime/logs/build_$k.log" 2>&1; done
