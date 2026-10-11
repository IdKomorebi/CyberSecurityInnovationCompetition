# 系统

## 查看（演示方式，不需要显卡）

```bash
python system/scripts/serve.py 8780      # 然后在浏览器打开 http://127.0.0.1:8780/frontend/
```

远程服务器上运行时，在编辑器的“端口”面板里转发 8780。

## 目录

- `frontend/`：界面。`index.html`、`app.css`、`app.js`；图表库在 `vendor/`，不连外网。
- `samples/`：内置演示任务的已算好结果，界面只读这里的文件。
- `scripts/build_samples.py`：重新生成演示任务（需要显卡）。`python system/scripts/build_samples.py ieee30 --gpu 0`
- `scripts/shots.py`：逐页截图并收集浏览器报错，输出到 `runtime/shots/`。

## 进度（2026-10-12）

已有页面：分类与一次定级、推断验证、字段推断敏感度、二次定级。已有任务：IEEE 30 节点、医疗保险个人数据。
未做：任务总览、共享审查与处置、核对与台账；PJM 和社区统计两个任务；上传数据从头运行。
