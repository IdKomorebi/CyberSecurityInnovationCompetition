# 提交材料 V1

作品：面向聚合推断威胁的数据定级与共享审查系统。本版生成作品文档（按官方《作品报告》模板）和演示视频讲稿，系统本身为 V8。

## 先看这些

| 文件 | 内容 |
|---|---|
| [deliverables/](deliverables/) | 作品文档 PDF（48 页，3.6 MB；含封面、填写说明、目录、正文 43 页、原创性声明） |
| [作品报告.md](作品报告.md) | 报告正文的源文件，修改这里后重新构建 |
| [视频讲稿.md](视频讲稿.md) | 约 5 分钟的演示视频讲稿：每节有“这节回答”“画面”和编号配音 |
| [分工.md](分工.md) | 4 人分工与提交前剩余工作 |
| build/作品报告.docx | 套好官方模板的 Word 版，可在装有宋体的电脑上直接编辑 |

## 目录

```text
作品报告.md        报告正文（Markdown）
视频讲稿.md        视频讲稿
分工.md            团队分工
evidence.json      报告引用的数字，从系统结果中提取
figures/           示意图（fig_*）、测试结果图（chart_*）、系统截图（ui_*）；src/ 为示意图源文件
scripts/           构建脚本
build/             中间文件：Word 版、各页预览、构建用字体（不提交）
deliverables/      最终提交文件
```

## 构建

需要 V8 服务在 8788 端口运行（截图用），以及 LibreOffice、python-docx、PyMuPDF、Playwright。

```bash
cd V8/submission/V1
python scripts/collect_evidence.py     # 从系统结果提取数字
python scripts/render_figures.py       # 渲染示意图
python scripts/make_charts.py          # 画测试结果图
python scripts/shoot_ui.py             # 截系统界面（会临时上传一份数据，截完自动删除）
python scripts/build_report.py         # 套模板，生成 Word 与 PDF
```

## 版式说明

- 按模板填写说明：A4，除标题外宋体小四、1.5 倍行距；封面与“填写说明”页保留；章标题黑体三号居中。
- **表格内用五号字、单倍行距**。全部按小四、1.5 倍行距时，5 列的表格会拉长到两三页，难以阅读。这是本版唯一偏离模板文字要求的地方，如需严格执行，把 `build_report.py` 中 `table()` 的字号和行距改掉即可。
- 本机没有宋体和黑体，PDF 用 Noto 字体的简体中文版代替（已核对字形为中文规范写法）。在装有宋体的 Windows 电脑上用 Word 打开 `build/作品报告.docx` 另存为 PDF，可得到真正的宋体版本。
- 目录页码由脚本两遍构建后写入；页脚为“第 x 页 共 y 页”，从摘要开始计页。

## 待办

1. 确认队长姓名，填入 `scripts/build_report.py` 的 `CAPTAIN`，重新构建。
2. 原创性声明 4 人手写签名，扫描后替换 PDF 最后一页。
3. 全体审阅报告；确认视频讲稿。
4. 程序包尚未整理（另做）。

## 匿名检查（本版已做）

PDF 全文搜索“大学、学院、导师、实验室、课题组”和委托单位名称，除官方原创性声明模板自带的“指导老师”外均未出现；文档属性中的作者、单位已清空；截图中没有主机名、用户名和路径。
