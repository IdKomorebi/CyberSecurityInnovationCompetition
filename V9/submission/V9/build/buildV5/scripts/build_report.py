# -*- coding: utf-8 -*-
"""把 作品报告.md 套入官方《作品报告》模板，生成 Word 与 PDF，并附上原创性声明。

用法：python scripts/build_report.py
输出：build/作品报告.docx、build/作品报告.pdf、deliverables/<队长姓名>-<作品名称>-作品文档.pdf，以及 build/previews/ 下的逐页预览。
版式按模板填写说明：A4，除标题外宋体小四、1.5 倍行距；模板的封面与“填写说明”页保留。目录分两遍生成：第一遍导出 PDF 查出各标题页码，第二遍写入。"""
import os, re, copy, subprocess, shutil
from pathlib import Path
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import fitz

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); BUILD = HERE
IMG = os.path.join(BUILD, "img")
PROJ = str(Path(HERE).parents[4]); OFFICIAL = os.path.join(PROJ, "reference", "官方文件")
TITLE = "面向聚合推断威胁的数据定级与共享审查系统"; DATE = "2026 年 10 月"; CAPTAIN = "杜浩存"          # 队长姓名确定后在这里填写
SONG, HEI = "宋体", "黑体"
os.makedirs(IMG, exist_ok=True); os.makedirs(os.path.join(HERE, "deliverables"), exist_ok=True)


# 本机没有宋体、黑体。LibreOffice 读取 Noto 字体集合时只用第一个（日文字形），所以从集合中取出简体中文那一份，
# 改名为构建专用字体，只在导出 PDF 时使用。只对构建过程生效，不改系统字体。
FDIR = os.path.join(BUILD, "fonts"); FONTS = os.path.join(BUILD, "fonts.conf"); NOTO = "/usr/share/fonts/opentype/noto"


def build_fonts():
    from fontTools.ttLib import TTCollection
    os.makedirs(FDIR, exist_ok=True)
    for src, fam, sub in (("NotoSerifCJK-Regular.ttc", "SongBuild", "Regular"), ("NotoSerifCJK-Bold.ttc", "SongBuild", "Bold"),
                          ("NotoSansCJK-Regular.ttc", "HeiBuild", "Regular"), ("NotoSansCJK-Bold.ttc", "HeiBuild", "Bold")):
        out = os.path.join(FDIR, f"{fam}-{sub}.otf")
        if os.path.exists(out):
            continue
        f = TTCollection(os.path.join(NOTO, src)).fonts[2]                      # 集合中第 3 个为简体中文（SC）
        nm = f["name"]
        for r in list(nm.names):
            if r.nameID in (16, 17, 21, 22):
                nm.removeNames(nameID=r.nameID)
        for pid, eid, lid in ((3, 1, 0x409), (1, 0, 0)):
            nm.setName(fam, 1, pid, eid, lid); nm.setName(sub, 2, pid, eid, lid); nm.setName(f"{fam} {sub}", 4, pid, eid, lid); nm.setName(f"{fam}-{sub}", 6, pid, eid, lid)
        f["OS/2"].usWeightClass = 700 if sub == "Bold" else 400
        f.save(out)
    open(FONTS, "w", encoding="utf-8").write(f"""<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>{FDIR}</dir></fontconfig>""")


build_fonts(); ENV = dict(os.environ, FONTCONFIG_FILE=FONTS)


def to_docx(src):
    out = os.path.join(BUILD, os.path.splitext(os.path.basename(src))[0] + ".docx")
    if not os.path.exists(out):
        subprocess.run(["soffice", "-env:UserInstallation=file:///tmp/buildV5-libreoffice", "--headless", "--convert-to", "docx", src, "--outdir", BUILD], check=True, capture_output=True, env=ENV)
    return out


def to_pdf(path):
    """Word 文件保持宋体、黑体（在装有这两种字体的电脑上编辑）；本机没有这两种字体，导出 PDF 时临时改写为 Noto 简体中文字体。"""
    import zipfile
    tmp = os.path.join(BUILD, "_pdf"); os.makedirs(tmp, exist_ok=True); src = os.path.join(tmp, os.path.basename(path))
    with zipfile.ZipFile(path) as zi, zipfile.ZipFile(src, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = zi.read(it.filename)
            if it.filename.endswith(".xml"):
                data = data.decode("utf-8").replace('="宋体"', '="SongBuild"').replace('="黑体"', '="HeiBuild"').encode("utf-8")   # 只改字体属性，不改正文里的“宋体”二字
            zo.writestr(it, data)
    subprocess.run(["soffice", "-env:UserInstallation=file:///tmp/buildV5-libreoffice", "--headless", "--convert-to", "pdf", src, "--outdir", BUILD], check=True, capture_output=True, env=ENV)
    return os.path.splitext(path)[0] + ".pdf"


def font(run, size=12, east=SONG, bold=None, color=None):
    run.font.size = Pt(size); run.font.name = "Times New Roman"
    rpr = run._element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    rf.set(qn("w:eastAsia"), east); rf.set(qn("w:ascii"), "Times New Roman"); rf.set(qn("w:hAnsi"), "Times New Roman")
    if bold is not None:
        run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def fmt(p, align=None, indent=True, before=0, after=0, spacing=1.5):
    pf = p.paragraph_format; pf.line_spacing = spacing; pf.space_before = Pt(before); pf.space_after = Pt(after)
    pf.first_line_indent = Pt(24) if indent else Pt(0)
    if align is not None:
        p.alignment = align


SUBSUP = re.compile(r"(_\{[^}]*\}|\^\{[^}]*\}|_[A-Za-z0-9θ]|\^[A-Za-z0-9])")


def add_text(p, text, size=12, east=SONG, bold=False):
    """支持 **加粗**，以及行内的下标 x_{..}、x_k 与上标 x^{..}。"""
    for k, seg in enumerate(re.split(r"\*\*", text)):
        for part in SUBSUP.split(seg):
            if not part:
                continue
            r = p.add_run(part[2:-1] if part[1:2] == "{" else part[1:]) if SUBSUP.fullmatch(part) else p.add_run(part)
            font(r, size, east, bold=bold or k % 2 == 1)
            if SUBSUP.fullmatch(part):
                (setattr(r.font, "subscript", True) if part[0] == "_" else setattr(r.font, "superscript", True))


def outline(p, level):
    ppr = p._p.get_or_add_pPr(); o = OxmlElement("w:outlineLvl"); o.set(qn("w:val"), str(level)); ppr.append(o)


def heading(doc, text, level):
    p = doc.add_paragraph(); size = {1: 16, 2: 14, 3: 12}[level]
    fmt(p, WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT, indent=False, before=12 if level == 1 else 8, after=12 if level == 1 else 4)
    font(p.add_run(text), size, HEI, bold=level > 1); outline(p, level - 1); p.paragraph_format.keep_with_next = True
    return p


def picture(path, width_cm=15.5):
    src = os.path.join(HERE, path)
    im = Image.open(src)
    h = im.height / im.width * width_cm
    if h > 21: width_cm *= 21 / h
    return src, width_cm


def formula(tex, n):
    out = os.path.join(IMG, f"formula_{n}.png")
    plt.rcParams["mathtext.fontset"] = "stix"
    fig = plt.figure(figsize=(0.01, 0.01)); fig.text(0, 0, f"${tex}$", fontsize=16)
    fig.savefig(out, dpi=300, bbox_inches="tight", pad_inches=0.06, facecolor="white"); plt.close(fig)
    w, h = Image.open(out).size
    return out, min(15.0, w / 300 * 2.54)


def shade(cell, color):
    tcpr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), color); tcpr.append(s)


def table(doc, rows, width_cm=15.5):
    """表格铺满版心，按各列文字长度分配列宽；表内按模板要求用宋体小四、1.5 倍行距；行不跨页，小表整体不跨页。"""
    n = len(rows[0]); t = doc.add_table(rows=len(rows), cols=n); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    need = [max(min(len(r[j].strip()), 40) for r in rows) + 4 for j in range(n)]; tot = sum(need)
    widths = [Cm(width_cm * x / tot) for x in need]
    for i, r in enumerate(rows):
        tr = t.rows[i]._tr; trpr = tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trpr.append(cs)
        if i == 0:
            hd = OxmlElement("w:tblHeader"); trpr.append(hd)
        for j, v in enumerate(r):
            c = t.cell(i, j); c.width = widths[j]; c.text = ""; p = c.paragraphs[0]
            fmt(p, WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT, indent=False, before=0, after=0, spacing=1.5)
            if len(rows) <= 5 and i < len(rows) - 1:                # 只有很小的表整体不跨页；大表允许跨页，表头重复
                p.paragraph_format.keep_with_next = True
            add_text(p, v.strip(), 12, SONG, bold=(i == 0))
            if i == 0:
                shade(c, "E8EEF7")
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(int(width_cm / 2.54 * 1440))); tw.set(qn("w:type"), "dxa"); t._tbl.tblPr.append(tw)
    borders(t)
    return t


def borders(t):
    tblpr = t._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        x = OxmlElement(f"w:{e}"); x.set(qn("w:val"), "single"); x.set(qn("w:sz"), "4"); x.set(qn("w:color"), "8A94A6"); b.append(x)
    tblpr.append(b)


def caption(doc, text):
    p = doc.add_paragraph(); fmt(p, WD_ALIGN_PARAGRAPH.CENTER, indent=False, after=6); add_text(p, text, 12, SONG)
    return p


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def field(run, instr):
    for kind, txt in (("begin", None), (None, instr), ("separate", None), (None, "1"), ("end", None)):
        if kind:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), kind); run._r.append(f)
        elif txt == instr:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" {instr} "; run._r.append(it)
        else:
            t = OxmlElement("w:t"); t.text = txt; run._r.append(t)


def build(toc_pages, total=0):
    doc = docx.Document(to_docx(os.path.join(OFFICIAL, "模板_作品报告.doc"))); body = doc.element.body; els = list(body.iterchildren())
    # 封面：作品名称、提交日期
    for p in doc.paragraphs[:16]:
        if p.text.startswith("作品名称") or p.text.startswith("提交日期"):
            r = p.runs[1]; r.text = "  " + (TITLE if p.text.startswith("作品名称") else DATE) + "  "; r.underline = True
            for x in p.runs[2:]:
                x.text = ""
    # 目录：模板自带的目录控件换成按实际页码生成的目录
    sdt = [e for e in els if e.tag == qn("w:sdt")][0]; idx = els.index(sdt)
    for e in els[idx + 1:]:
        if e.find(".//" + qn("w:sectPr")) is not None:
            stop = e; break
        body.remove(e)
    for title, lvl, pg in toc_pages:
        p = docx.text.paragraph.Paragraph(OxmlElement("w:p"), doc._body); stop.addprevious(p._p)
        fmt(p, indent=False, spacing=1.5); p.paragraph_format.left_indent = Pt(24 * (lvl - 1))
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.2), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        font(p.add_run(f"{title}\t{pg}"), 12, HEI if lvl == 1 else SONG)
    body.remove(sdt)
    # 删除模板的正文说明（摘要至参考文献），保留最后的节属性
    els = list(body.iterchildren()); start = els.index(stop) + 1
    for e in els[start:]:
        if e.tag != qn("w:sectPr"):
            body.remove(e)
    sect = doc.sections[-1]
    pg = sect._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType"); sect._sectPr.append(pg)
    pg.set(qn("w:start"), "1"); pg.set(qn("w:fmt"), "decimal")
    ft = sect.footer; ft.is_linked_to_previous = False
    for p in ft.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    fp = ft.paragraphs[0]
    for r in fp.runs:
        r._r.getparent().remove(r._r)
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(fp.add_run("第 "), 10.5); r = fp.add_run(); field(r, "PAGE"); font(r, 10.5); font(fp.add_run(f" 页 共 {total} 页"), 10.5)          # 总页数用第一遍查出的正文页数（LibreOffice 导出时不更新本节总页数域）
    # 正文
    lines = open(os.path.join(HERE, "作品报告.md"), encoding="utf-8").read()
    lines = re.sub(r"<!--.*?-->", "", lines, flags=re.S).splitlines()
    i, first, nf, heads = 0, True, 0, []
    while i < len(lines):
        s = lines[i].rstrip()
        if not s.strip():
            i += 1; continue
        if s.startswith("# "):
            h = heading(doc, s[2:].strip(), 1); heads.append((s[2:].strip(), 1))
            if not first:                                    # 用“段前分页”换章，上一章正好写满一页时不会多出空白页
                h.paragraph_format.page_break_before = True
            first = False
        elif s.startswith("## "):
            heading(doc, s[3:].strip(), 2); heads.append((s[3:].strip(), 2))
        elif s.startswith("### "):
            heading(doc, s[4:].strip(), 3); heads.append((s[4:].strip(), 3))          # 三级标题也进目录
        elif s.startswith("!["):
            cap, path = re.match(r"!\[(.*?)\]\((.*?)\)", s).groups(); f, w = picture(path)
            p = doc.add_paragraph(); fmt(p, WD_ALIGN_PARAGRAPH.CENTER, indent=False, before=6, spacing=1.0); p.add_run().add_picture(f, width=Cm(w)); p.paragraph_format.keep_with_next = True
            caption(doc, cap)
        elif s.startswith("```"):                    # 算法框：等宽字、浅灰底、单倍行距
            i += 1; block = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i]); i += 1
            tb = doc.add_table(rows=1, cols=1); tb.alignment = WD_TABLE_ALIGNMENT.CENTER; cell = tb.cell(0, 0); shade(cell, "F3F5F9"); borders(tb); cell.text = ""
            for k, ln in enumerate(block):
                p = cell.paragraphs[0] if k == 0 else cell.add_paragraph(); fmt(p, indent=False, spacing=1.5)
                bold = ln.startswith("算法") or ln.startswith("输入") or ln.startswith("输出")
                add_text(p, ln.replace("    ", "\u3000\u3000"), 12, SONG, bold=bold)
            doc.add_paragraph().paragraph_format.space_after = Pt(0)
        elif s.startswith("$$"):
            nf += 1; f, w = formula(s.strip("$").strip(), nf)
            p = doc.add_paragraph(); fmt(p, WD_ALIGN_PARAGRAPH.CENTER, indent=False, before=4, after=4, spacing=1.0); p.add_run().add_picture(f, width=Cm(w))
        elif s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s\-|:]+\|$", lines[i].strip()):
                    rows.append(lines[i].strip().strip("|").split("|"))
                i += 1
            table(doc, rows); doc.add_paragraph().paragraph_format.space_after = Pt(0); continue
        elif re.match(r"^表 [A-Z0-9]+-\d+", s):
            p = caption(doc, s); p.paragraph_format.keep_with_next = True
        elif re.match(r"^\[\d+\]", s):
            p = doc.add_paragraph(); fmt(p, WD_ALIGN_PARAGRAPH.JUSTIFY, indent=False); p.paragraph_format.left_indent = Pt(24); p.paragraph_format.first_line_indent = Pt(-24); add_text(p, s)
        else:
            p = doc.add_paragraph(); fmt(p, WD_ALIGN_PARAGRAPH.JUSTIFY); add_text(p, s.strip())
        i += 1
    out = os.path.join(BUILD, "作品报告.docx"); doc.save(out)
    return out, heads


SIGN_DATE = "2026 年 10 月 16 日"


def statement():
    return os.path.join(BUILD,"原创性声明.pdf")


def page_of(pdf, heads):
    """在 PDF 中查各标题所在页，换算成正文页码（正文第一个标题所在页为第 1 页）。"""
    doc = fitz.open(pdf); txt = [doc[k].get_text().replace(" ", "") for k in range(len(doc))]
    first = heads[0][0].replace(" ", "")                                    # 正文的第一个标题所在页为第 1 页
    start = next(k for k, t in enumerate(txt) if t.lstrip().startswith(first))
    page_of.total = len(doc) - start; out, k0 = [], start
    for title, lvl in heads:
        key = title.replace(" ", "")
        k = next((k for k in range(k0, len(txt)) if key in txt[k] or key in txt[k].replace("\n", "")), k0); k0 = k     # 标题折行时去掉换行再找
        out.append((title, lvl, k - start + 1))
    return out


if __name__ == "__main__":
    out, heads = build([(h, l, 0) for h, l in [("摘要", 1)]])          # 第一遍：目录占位
    _, heads = build([(h, l, 0) for h, l in heads]); pdf = to_pdf(os.path.join(BUILD, "作品报告.docx"))
    toc = page_of(pdf, heads); build(toc, page_of.total); pdf = to_pdf(os.path.join(BUILD, "作品报告.docx"))   # 第二遍：写入页码
    st = statement(); merged = fitz.open(pdf); merged.insert_pdf(fitz.open(st))
    merged.set_metadata({"title": TITLE, "author": "", "subject": "", "keywords": "", "creator": "", "producer": ""})
    final = os.path.join(HERE, "deliverables", f"{CAPTAIN}-{TITLE}-作品文档.pdf"); merged.save(final, garbage=4, deflate=True)
    shutil.copy2(final,os.path.join(BUILD,"作品文档_含原创性声明.pdf"))
    prev = os.path.join(BUILD, "previews"); os.makedirs(prev, exist_ok=True)
    for k, page in enumerate(merged):
        page.get_pixmap(dpi=60).save(os.path.join(prev, f"page_{k + 1:02d}.png"))
    print("页数", len(merged), "大小", round(os.path.getsize(final) / 2 ** 20, 2), "MB", "->", final)
    for t, l, p in toc:
        print("  " * (l - 1) + t, p)
