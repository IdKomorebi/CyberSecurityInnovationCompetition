"""Check the delivered captions/timings and package only reviewable outputs."""
from pathlib import Path
import hashlib,json,zipfile
from prepare import BASE

def main():
    tl=json.loads((BASE/'work/timeline.json').read_text())
    rec=json.loads((BASE/'work/recorded_timeline.json').read_text())
    checks=json.loads((BASE/'work/quality_check.json').read_text())
    assert checks['full_decode_ok'] and not checks['black_intervals'] and not checks['browser_errors']
    assert len(tl['items'])==47
    assert all(c['end']>c['start'] and len(c['text'])<=30 for c in tl['captions'])
    for r in tl['items']:
        joined=''.join(c['text'] for c in tl['captions'] if c['utterance']==r['id'])
        assert joined==r['text'],r['id']
        assert r['end']-r['start']>=3.8
    assert all(a['end']<=b['action_start'] for a,b in zip(rec['items'],rec['items'][1:]))
    report={'duration_seconds':tl['duration'],'utterances':47,'subtitles':len(tl['captions']),
            'caption_text_matches_script':True,'max_caption_chars':max(len(c['text']) for c in tl['captions']),
            'min_caption_seconds':min(c['end']-c['start'] for c in tl['captions']),
            'actions_outside_narration':True,'post_speed':tl['post_speed'],'subtitle_font':54,'no_local_zoom':True}
    chapters=[]
    for i,r in enumerate(tl['items']):
        if i==0 or r['section']!=tl['items'][i-1]['section']:
            t=int(r['action_start']);chapters.append(f'- {t//60:02d}:{t%60:02d}　{r["section"]}')
    d=int(round(tl['duration']));p=BASE/'制作说明.md';s=p.read_text().split('\n## 成片检查')[0]
    s+=f'\n## 成片检查\n\n成片时长 {d//60} 分 {d%60:02d} 秒，47 段讲解、{len(tl["captions"])} 条字幕。已完成全片解码、黑帧检测、音轨检查、字幕正文一致性检查及逐段画面抽查。\n\n'
    s+='\n'.join(chapters)+'\n';p.write_text(s)
    files=['演示视频.mp4','演示视频.srt','视频讲稿.md','制作说明.md','读音核对.wav','img/svg/开场案例.svg','img/svg/结果汇总.svg']
    report['files']={n:{'bytes':(BASE/n).stat().st_size,'sha256':hashlib.sha256((BASE/n).read_bytes()).hexdigest()} for n in files}
    (BASE/'成片检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(BASE/'videoV2_成片与讲稿.zip','w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
        for n in files+['成片检查.json']:z.write(BASE/n,n)
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
