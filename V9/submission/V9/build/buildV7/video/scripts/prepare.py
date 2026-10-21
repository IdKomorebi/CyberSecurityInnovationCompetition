"""Prepare takes first; align sound and captions to the completed screen recording."""
from pathlib import Path
import argparse, difflib, json, re, subprocess, wave
from functools import lru_cache

BASE = Path(__file__).resolve().parents[1]
FF = Path('/data1/duhaocun/projects/diantan/competition_materials/01_initial_20260907/work/deps/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2')
SPEED = 1.025

def stamp(t, ass=False):
    q = 100 if ass else 1000
    n = round(t*q)
    return f'{n//(3600*q)}:{n//(60*q)%60:02d}:{n//q%60:02d}.{n%q:02d}' if ass else f'{n//(3600*q):02d}:{n//(60*q)%60:02d}:{n//q%60:02d},{n%q:03d}'

def split_text(s):
    # Prefer complete clauses and balanced lines. No line breaks inside numbers.
    stops = [0]+[m.end() for m in re.finditer('[，；：。！？、]', s)]
    # A subtitle boundary only: preserve the approved narration verbatim.
    if 'DeepSeek V4.1 Flash 模型以国家标准' in s:
        stops.append(s.index('模型以国家标准')+2)
    stops = sorted(set(stops))
    if stops[-1] != len(s): stops.append(len(s))
    @lru_cache(None)
    def solve(i):
        if i == len(stops)-1: return (0, [])
        candidates=[]
        for j in range(i+1, len(stops)):
            n=stops[j]-stops[i]
            if n>30:break
            cost, parts=solve(j)
            candidates.append((cost+(n-23)**2+(150 if n<8 else 0),[(stops[i],stops[j],s[stops[i]:stops[j]])]+parts))
        return min(candidates,key=lambda x:x[0]) if candidates else (1e9,[])
    cost, parts=solve(0)
    assert cost<1e9, ('Clause needs editorial break',s)
    return parts

def local_captions(row, meta):
    ends={}
    for e in meta['events']:
        sent=e.get('output',{}).get('sentence',{}); words=sent.get('words',[])
        if len(words)>=len(ends.get(sent.get('index',0),[])): ends[sent.get('index',0)]=words
    spoken='';times=[]
    for _,ws in sorted(ends.items()):
        for w in ws:
            txt=w['text'];a=w['begin_time']/1000/SPEED;b=w['end_time']/1000/SPEED
            spoken+=txt;times.extend([a+(b-a)*j/max(1,len(txt)) for j in range(len(txt))])
    mapping={}
    for block in difflib.SequenceMatcher(None,row['text'],spoken,autojunk=False).get_matching_blocks():
        for j in range(block.size): mapping[block.a+j]=block.b+j
    parts=split_text(row['text']);starts=[]
    for a,b,txt in parts:
        near=next((k for k in range(a,min(a+12,len(row['text']))) if k in mapping),None)
        local=times[mapping[near]] if near is not None else row['duration']*a/len(row['text'])
        starts.append(0 if a==0 else local)
    return [dict(text=txt,start=starts[j],end=starts[j+1]-.015 if j+1<len(parts) else row['duration']) for j,(_,_,txt) in enumerate(parts)]

def takes():
    rows=json.loads((BASE/'work/narration.json').read_text())['items']
    out=BASE/'work/audio_processed';out.mkdir(exist_ok=True)
    for row in rows:
        p=out/f'{row["id"]:02d}.wav';meta=json.loads((BASE/f'audio/{row["id"]:02d}.json').read_text())
        subprocess.run([str(FF),'-loglevel','error','-y','-i',str(BASE/f'audio/{row["id"]:02d}.wav'),'-af',f'atempo={SPEED},aresample=48000','-ac','1','-c:a','pcm_s16le',str(p)],check=True)
        with wave.open(str(p)) as w: row['duration']=w.getnframes()/48000
        row['local_captions']=local_captions(row,meta)
    (BASE/'work/takes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    print('TAKES',len(rows),'speech seconds',round(sum(r['duration'] for r in rows),2),'captions',sum(len(r['local_captions']) for r in rows))

def assemble():
    rows=json.loads((BASE/'work/takes.json').read_text())
    rec=json.loads((BASE/'work/recorded_timeline.json').read_text())
    pcm=bytearray(round(rec['duration']*48000)*2);captions=[]
    for row, timing in zip(rows, rec['items']):
        assert row['id']==timing['id']
        row.update(timing)
        with wave.open(str(BASE/f'work/audio_processed/{row["id"]:02d}.wav')) as w:data=w.readframes(w.getnframes())
        a=round(row['start']*48000)*2;pcm[a:a+len(data)]=data
        for c in row.pop('local_captions'):
            captions.append(dict(utterance=row['id'],section=row['section'],text=c['text'],start=row['start']+c['start'],end=row['start']+c['end']))
    with wave.open(str(BASE/'配音.wav'),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(pcm)
    tl=dict(duration=rec['duration'],post_speed=SPEED,model='qwen-audio-3.1-tts-flash',voice='longanlingxin_v3.1',items=rows,captions=captions)
    (BASE/'work/timeline.json').write_text(json.dumps(tl,ensure_ascii=False,indent=2))
    (BASE/'演示视频.srt').write_text('\n\n'.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(captions,1))+'\n')
    ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Noto Sans CJK SC,54,&H00FFFFFF,&H00FFFFFF,&H60101D35,&H00101D35,-1,0,0,0,100,100,0,0,1,1,0,2,60,60,18,1
Style: Label,Noto Sans CJK SC,20,&H00E4BFA8,&H00FFFFFF,&H00101D35,&H00101D35,0,0,0,0,100,100,0,0,1,0,0,7,30,30,968,1
Style: Scope,Noto Sans CJK SC,20,&H00E4BFA8,&H00FFFFFF,&H00101D35,&H00101D35,0,0,0,0,100,100,0,0,1,0,0,9,30,30,968,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    for c in captions:ass+=f'Dialogue: 1,{stamp(c["start"],True)},{stamp(c["end"],True)},Caption,,0,0,0,,{c["text"]}\n'
    for i,r in enumerate(rows):
        if i and r['section']==rows[i-1]['section']:continue
        end=next((x['action_start'] for x in rows[i+1:] if x['section']!=r['section']),rec['duration'])
        ass+=f'Dialogue: 0,{stamp(r["action_start"],True)},{stamp(end,True)},Label,,0,0,0,,{r["section"]}\n'
    for a,b,t in [(17,23,'新建任务 · PJM 数据 · 实际操作'),(24,62,'NEM 2024 · 内置实测结果')]:
        ass+=f'Dialogue: 0,{stamp(rows[a-1]["action_start"],True)},{stamp(rows[b]["action_start"],True)},Scope,,0,0,0,,{t}\n'
    (BASE/'work/captions.ass').write_text(ass)
    chapters=[]
    for i,r in enumerate(rows):
        if i and r['section']==rows[i-1]['section']:continue
        end=next((x['action_start'] for x in rows[i+1:] if x['section']!=r['section']),rec['duration'])
        chapters.append(dict(title=r['section'],start=r['action_start'],end=end))
    (BASE/'work/chapters.json').write_text(json.dumps(chapters,ensure_ascii=False,indent=2))
    (BASE/'work/chapters.ffmeta').write_text(';FFMETADATA1\n'+''.join(
        f'[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c["start"]*1000)}\nEND={round(c["end"]*1000)}\ntitle={c["title"]}\n' for c in chapters))
    print('ASSEMBLED',round(rec['duration'],3),'seconds',len(captions),'captions')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--assemble',action='store_true');a=p.parse_args()
    assemble() if a.assemble else takes()
