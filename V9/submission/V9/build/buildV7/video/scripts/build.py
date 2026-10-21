"""Render the continuous screen recording and run media/visual checks."""
from pathlib import Path
import concurrent.futures,json,re,subprocess
from PIL import Image,ImageDraw,ImageFont
from prepare import BASE,FF

def run(args,**kw):return subprocess.run([str(FF),'-hide_banner','-nostdin',*args],check=True,**kw)

def main():
    tl=json.loads((BASE/'work/timeline.json').read_text());src=Path((BASE/'work/recording_path.txt').read_text())
    pixels=run(['-loglevel','error','-i',str(src),'-t','25','-vf','fps=25,crop=2:2:0:0,format=rgb24','-an','-f','rawvideo','pipe:1'],capture_output=True).stdout
    marks=[i for i in range(len(pixels)//12) if pixels[i*12]>220 and pixels[i*12+1]<45 and pixels[i*12+2]>220]
    assert marks,'Missing synchronization marker';offset=(max(marks)+1)/25
    cuts=json.loads((BASE/'work/cuts.json').read_text());ranges=[];start=0
    for c in cuts:ranges.append([start,c['start']]);start=c['end']
    ranges.append([start,tl['duration']+sum(c['end']-c['start'] for c in cuts)])
    filters=[]
    for i,(a,b) in enumerate(ranges):filters.append(f'[0:v]trim=start={offset+a:.6f}:end={offset+b:.6f},setpts=PTS-STARTPTS[v{i}]')
    if len(ranges)>1:
        filters.append(''.join(f'[v{i}]' for i in range(len(ranges)))+f'concat=n={len(ranges)}:v=1:a=0[vj]');v='[vj]'
    else:v='[v0]'
    filters.append(v+f'scale=1920:960:flags=lanczos,pad=1920:1080:0:0:color=0x101D35,setsar=1,ass={BASE/"work/captions.ass"}[out]')
    dest=BASE.parent/'演示视频.mp4'
    args=['-y','-i',str(src),'-i',str(BASE/'配音.wav'),'-f','ffmetadata','-i',str(BASE/'work/chapters.ffmeta'),'-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map','[out]','-map','1:a:0','-map_chapters','2',
          '-af','loudnorm=I=-16:TP=-1.5:LRA=9','-c:v','libx264','-preset','fast','-crf','20','-threads','6','-r','30','-pix_fmt','yuv420p',
          '-c:a','aac','-b:a','160k','-ar','48000','-ac','1','-t',str(tl['duration']),'-movflags','+faststart','-map_metadata','2',str(dest)]
    (BASE/'work/build_plan.json').write_text(json.dumps(dict(source=str(src),sync_offset=offset,continuous_ranges=ranges,cuts=cuts,args=args),ensure_ascii=False,indent=2))
    with (BASE/'work/render.log').open('w') as log:run(args,stdout=log,stderr=log)
    print('RENDER COMPLETE',round(dest.stat().st_size/1e6,2),'MB',flush=True)
    with (BASE/'work/decode.log').open('w') as log:
        run(['-loglevel','info','-i',str(dest),'-vf','blackdetect=d=0.5:pix_th=0.05:pic_th=0.98',
             '-af','silencedetect=noise=-45dB:d=1.5','-f','null','-'],stdout=log,stderr=log)
    probe=subprocess.run([str(FF),'-hide_banner','-i',str(dest)],capture_output=True,text=True).stderr
    assert probe.count('Audio:')==1 and 'mono' in probe and '1920x1080' in probe
    chapters=json.loads((BASE/'work/chapters.json').read_text())
    assert 'Referenced QT' not in probe and all(c['title'] in probe for c in chapters)
    errors=json.loads((BASE/'work/browser_errors.json').read_text());assert not errors,errors
    media_log=(BASE/'work/decode.log').read_text();black=re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',media_log)
    silent=re.findall(r'silence_duration: ([\d.]+)',media_log)
    # Export every utterance midpoint and each synchronized visual cue.
    review=BASE/'review';review.mkdir(exist_ok=True)
    shots=[dict(id=f'{r["id"]:02d}',time=(r['start']+r['end'])/2,text=r['text']) for r in tl['items']]
    cues=json.loads((BASE/'work/events.json').read_text())
    shots.extend(dict(id=f'cue_{i:02d}',time=min(tl['duration']-.2,e['actual']+.5),text=e['label']) for i,e in enumerate(cues,1))
    def shot(s):
        run(['-loglevel','error','-y','-ss',str(s['time']),'-i',str(dest),'-frames:v','1',str(review/(s['id']+'.png'))],capture_output=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(shot,shots))
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14)
    tiles=[]
    for s in shots:
        tile=Image.new('RGB',(640,418),'#edf2fa');tile.paste(Image.open(review/(s['id']+'.png')).resize((640,360)),(0,0));d=ImageDraw.Draw(tile)
        text=f'{s["id"]} · {int(s["time"])//60}:{int(s["time"])%60:02d}  '+s['text']
        d.text((8,366),text[:42],font=font,fill='#1b3557');d.text((8,390),text[42:84],font=font,fill='#1b3557');tiles.append(tile)
    for i in range(0,len(tiles),8):
        sheet=Image.new('RGB',(1280,1672),'white')
        for j,tile in enumerate(tiles[i:i+8]):sheet.paste(tile,((j%2)*640,(j//2)*418))
        sheet.save(review/f'sheet_{i//8+1:02d}.jpg',quality=92)
    quality=dict(duration=tl['duration'],size_mb=dest.stat().st_size/1e6,model=tl['model'],voice=tl['voice'],
                 audio_tracks=1,channels=1,full_decode_ok=True,browser_errors=errors,utterances=len(tl['items']),subtitles=len(tl['captions']),
                 max_caption_length=max(len(c['text']) for c in tl['captions']),review_frames=len(shots),continuous_source_ranges=len(ranges),chapters_verified=len(chapters),probe=probe)
    quality.update(black_intervals=black,silences_over_1_5_seconds=silent,subtitle_font_size=54,local_zoom=False,post_speed=tl["post_speed"])
    (BASE/'work/quality_check.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2))
    print('MEDIA CHECK COMPLETE; review frames saved.',flush=True)

if __name__=='__main__':main()
