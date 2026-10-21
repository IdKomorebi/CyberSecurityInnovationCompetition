"""Publish local subtitle and production notes after the finished MP4 passes checks."""
from pathlib import Path
import hashlib, json, re, shutil
from prepare import BASE, SPEED

root=BASE.parent
tl=json.loads((BASE/'work/timeline.json').read_text())
quality=json.loads((BASE/'work/quality_check.json').read_text())
protected=json.loads((BASE/'work/protected_files.json').read_text())
changed=[p for p,h in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
assert not changed, changed
original=json.loads((BASE/'work/narration.json').read_text())['items']
assert len(original)==len(tl['items'])==65
assert not quality['black_intervals'],quality['black_intervals']
for row in original:
    shown=''.join(c['text'] for c in tl['captions'] if c['utterance']==row['id'])
    assert shown==row['text'],row['id']
for i,row in enumerate(tl['items']):
    assert row['action_start']<=row['start']<row['end']<=tl['duration']
    if i:assert row['start']>=tl['items'][i-1]['end']
for c in tl['captions']:
    assert 0<=c['start']<c['end']<=tl['duration']
shutil.copy2(BASE/'演示视频.srt',root/'演示视频.srt')
chapters=json.loads((BASE/'work/chapters.json').read_text())
duration=round(tl['duration']);chapter_text='\n'.join(f'- {int(c["start"])//60:02d}:{int(c["start"])%60:02d}　{c["title"]}' for c in chapters)
notes=f'''# V7 演示视频

成片为 `演示视频.mp4`，时长 {duration//60} 分 {duration%60:02d} 秒，1920 × 1080，30 帧/秒，带内嵌字幕和八个章节。另附独立字幕 `演示视频.srt`。

使用 buildV4 的《视频讲稿V4.md》（65 段），在本目录保存为《视频讲稿.md》。配音和字幕保留编号正文，只对配音中的字母 M、国标编号做读音处理。

配音继续使用龙安灵心 3.1：`qwen-audio-3.1-tts-flash` / `longanlingxin_v3.1`。合成语速 1.1，国标所在句 1.18；后期播放速度 {SPEED}，比已确认的 videoV2 快 2.5%。字幕沿用 54 号白字与底部独立深色字幕区。

画面按讲稿逐步揭示开场案例；软件部分使用 V7 提交程序的独立副本实际录制。上传、目录确认和启动后台任务为实际操作，目录生成的等待被剪短；随后切换 NEM 已完成任务展示结果。K、背景曲线、越线组合、效用与调级效果均按对应语句展示，只做红色圈画，未使用局部放大。燃煤机组原始精度 0.825 按四舍五入显示为 0.83，计算数据保持原样。

原 V7 报告、声明、图片和软件提交包均未修改。制作脚本、配音、录屏与逐段检查画面保存在 `video/`。录制用临时服务与新建任务已在录制结束后停止，临时运行目录中的凭据已清理。

## 章节

{chapter_text}

## 检查

65 段配音、{len(tl['captions'])} 条字幕与讲稿正文逐段核对。成片已完成全片解码、音轨与黑帧检查，并抽取每段讲解及画面变化时刻进行检查。重点读音音频见 `video/读音核对.wav`。
'''
(root/'视频制作说明.md').write_text(notes)
files={}
for name in ['演示视频.mp4','演示视频.srt','视频讲稿.md','视频制作说明.md']:
    p=root/name;files[name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
out=dict(duration_seconds=tl['duration'],utterances=65,subtitles=len(tl['captions']),caption_text_matches_script=True,
         full_decode_ok=quality['full_decode_ok'],black_intervals=quality['black_intervals'],browser_errors=quality['browser_errors'],
         original_files_checked=len(protected),original_files_changed=changed,post_speed=SPEED,subtitle_font=54,no_local_zoom=True,files=files)
(root/'视频成片检查.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print('READY',root/'演示视频.mp4',f'{duration//60}:{duration%60:02d}',flush=True)
