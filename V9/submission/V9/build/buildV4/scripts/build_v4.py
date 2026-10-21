"""Replace only the five principle images in buildV3 and verify preservation.

No report typesetting is regenerated: DOCX media and PDF image objects are replaced
in place. This keeps body text, formulae, screenshots, captions and pagination.
"""
from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
import json
import re
import shutil
import pymupdf as fitz
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent/'buildV3'
V9 = ROOT.parents[1]
REPLACEMENTS = {
    'fig_batch': ('word/media/image12.jpg','图 2-5 遮挡'),
    'fig_gate': ('word/media/image15.jpg','图 2-6 门控'),
    'fig_readout': ('word/media/image18.jpg','图 2-7 闭式'),
    'fig_grpo3': ('word/media/image31.jpg','图 2-10 联合'),
    'fig_whole': ('word/media/image35.jpg','图 2-11 整体'),
}


def main():
    for src in (BASE/'img').iterdir():
        if src.is_file() and src.stem not in REPLACEMENTS:
            shutil.copy2(src,ROOT/'img'/src.name)
    for name in ['原创性声明.docx','原创性声明.pdf']:
        shutil.copy2(BASE/name,ROOT/name)

    original = (V9/'作品报告.md').read_text(encoding='utf-8')
    updated = re.sub(r'\]\(figures/([^()]+)\.png\)',r'](img/\1.jpg)',original)
    assert re.sub(r'\]\(img/([^()]+)\.jpg\)',r'](figures/\1.png)',updated) == original
    for p in re.findall(r'^!\[[^\]]*\]\(([^)]+)\)',updated,re.M): assert (ROOT/p).exists(),p
    (ROOT/'作品报告.md').write_text(updated,encoding='utf-8')

    mapping = {v[0]:(ROOT/'img'/f'{k}.jpg').read_bytes() for k,v in REPLACEMENTS.items()}
    with ZipFile(BASE/'作品报告.docx') as zi, ZipFile(ROOT/'作品报告.docx','w') as zo:
        for it in zi.infolist(): zo.writestr(it,mapping.get(it.filename,zi.read(it)))
    with ZipFile(BASE/'作品报告.docx') as zi, ZipFile(ROOT/'作品报告.docx') as zo:
        assert zi.namelist()==zo.namelist()
        changed=[p for p in zi.namelist() if zi.read(p)!=zo.read(p)]
        assert set(changed)==set(mapping),changed

    doc=fitz.open(BASE/'作品报告.pdf')
    changes=[]
    for name,(_,caption) in REPLACEMENTS.items():
        matches=[i for i,p in enumerate(doc) if caption in p.get_text()]
        assert len(matches)==1,(name,matches)
        page=doc[matches[0]]
        size=Image.open(BASE/'img'/f'{name}.jpg').size
        imgs=[im for im in page.get_image_info(xrefs=True) if im['xref'] and im['bbox'][2]-im['bbox'][0]>400 and abs(im['height']/im['width']-size[1]/size[0])<.003]
        assert len(imgs)==1,(name,imgs)
        im=imgs[0]
        page.replace_image(im['xref'],filename=str(ROOT/'img'/f'{name}.jpg'))
        changes.append({'figure':name,'pdf_page':matches[0]+1,'rect':list(im['bbox'])})
    doc.save(ROOT/'作品报告.pdf',garbage=4,deflate=True)
    doc.close()

    # Check page text, original images, and every rendered pixel outside the five
    # figure rectangles. A narrow margin accounts for antialiasing at the edge.
    old=fitz.open(BASE/'作品报告.pdf'); new=fitz.open(ROOT/'作品报告.pdf')
    assert len(old)==len(new)
    bypage={v['pdf_page']-1:v['rect'] for v in changes}
    unchanged_pages=0
    for i,(a,b) in enumerate(zip(old,new)):
        assert a.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)==b.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES),(i,'text or position changed')
        ia=Image.frombytes('RGB',[a.get_pixmap().width,a.get_pixmap().height],a.get_pixmap().samples)
        pb=b.get_pixmap(); ib=Image.frombytes('RGB',[pb.width,pb.height],pb.samples)
        diff=ImageChops.difference(ia,ib)
        if i in bypage:
            x0,y0,x1,y1=bypage[i]
            assert diff.getbbox(),(i,'figure was not replaced')
            ImageDraw.Draw(diff).rectangle((int(x0)-2,int(y0)-2,int(x1)+2,int(y1)+2),fill='black')
            b.get_pixmap(dpi=110).save(ROOT/'previews'/f'page_{i+1:02d}.png')
        else: unchanged_pages+=1
        assert not diff.getbbox(),(i,'pixels changed outside replacement')

    preserved=[p.name for p in (BASE/'img').iterdir() if p.is_file() and p.stem not in REPLACEMENTS]
    assert all((BASE/'img'/p).read_bytes()==(ROOT/'img'/p).read_bytes() for p in preserved)
    screenshot_names=sorted(p for p in preserved if p.startswith('ui_'))
    merged=fitz.open(ROOT/'作品报告.pdf')
    with fitz.open(ROOT/'原创性声明.pdf') as st: merged.insert_pdf(st)
    merged.save(ROOT/'作品文档_含原创性声明.pdf',garbage=4,deflate=True)

    script=(ROOT/'视频讲稿.md').read_text(encoding='utf-8')
    voice=re.findall(r'^(\d+)\. (.+)$',script,re.M)
    assert [int(n) for n,_ in voice]==list(range(1,len(voice)+1))
    plain='\n\n'.join(t.replace('【放大】','') for _,t in voice)+'\n'
    (ROOT/'视频讲稿_纯配音.txt').write_text(plain,encoding='utf-8')
    count=len(re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]','',plain))
    result={
        'baseline':'../buildV3',
        'report_pages':len(new),
        'combined_pages':len(merged),
        'replaced_figures':changes,
        'docx_changed_entries_only':changed,
        'pdf_text_and_positions_identical':True,
        'unchanged_pages_pixel_identical':unchanged_pages,
        'changed_pages_pixels_outside_figure_identical':True,
        'preserved_image_files':len(preserved),
        'screenshots_byte_identical':screenshot_names,
        'markdown_body_and_captions_identical_except_image_paths':True,
        'source_report_sha256':sha256(original.encode()).hexdigest(),
        'voice_segments':len(voice),'voice_characters_excluding_punctuation':count,
    }
    (ROOT/'核对结果.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

    captions=['图 2-5｜遮挡输入的成批训练','图 2-6｜门控网络与诱饵门槛','图 2-7｜闭式读出估计器','图 2-10｜组相对策略优化','图 2-11｜整体核对']
    cards=''.join(f'<section><h2>{cap}</h2><a href="img/svg/{name}.svg"><img src="img/svg/{name}.svg" alt="{cap}"></a><p><a href="img/svg/{name}.svg" download>下载 SVG</a> · <a href="img/{name}.png" download>下载 PNG</a></p></section>' for name,cap in zip(REPLACEMENTS,captions))
    html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>buildV4 原理图</title><style>body{margin:0;background:#edf1f6;color:#182b45;font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif}main{max-width:1100px;margin:48px auto;padding:0 24px}h1{font-size:30px}h2{font-size:21px}section{padding:22px 28px;background:white;margin:28px 0;border-radius:12px;border:1px solid #dae3ed}img{display:block;width:100%;height:auto;margin-top:20px}a{color:#2463b6}p{color:#52647a;font-size:16px}</style><main><h1>buildV4 · 五张原理图</h1><p>原生矢量图，可单独下载并编辑；图号、图注与报告对应。</p>'''+cards+'</main></html>'
    (ROOT/'原理图预览.html').write_text(html,encoding='utf-8')


if __name__=='__main__': main()
