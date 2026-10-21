"""Assemble mono narration and captions from actual Qwen word timestamps."""
from pathlib import Path
import difflib,json,re,subprocess,wave

BASE=Path(__file__).resolve().parents[1]
FF=Path('/data1/duhaocun/projects/diantan/competition_materials/01_initial_20260907/work/deps/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2')

def stamp(t,ass=False):
    q=100 if ass else 1000;n=round(t*q)
    return f'{n//(3600*q)}:{n//(60*q)%60:02d}:{n//q%60:02d}.{n%q:02d}' if ass else f'{n//(3600*q):02d}:{n//(60*q)%60:02d}:{n//q%60:02d},{n%q:03d}'

def split_text(text):
    if len(text)<=40:return [(0,len(text),text)]
    # Break only at a real punctuation boundary, retaining every character.
    chunks=[];start=0
    while len(text)-start>40:
        stops=[m.end()+start for m in re.finditer('[，；：。！？]',text[start:start+40])]
        end=stops[-1] if stops else start+38
        chunks.append((start,end,text[start:end]));start=end
    if start<len(text):chunks.append((start,len(text),text[start:]))
    return chunks

def main():
    rows=json.loads((BASE/'work/narration.json').read_text())['items']
    raw=[]
    for r in rows:
        d=json.loads((BASE/f'audio/{r["id"]:02d}.json').read_text());r['source_duration']=d['duration'];r['tts']=d
        raw.append(d['duration'])
    gaps=[.5 if i==54 or rows[i+1]['section']!=r['section'] else .09 for i,r in enumerate(rows)]
    speed=max(1.0,sum(raw)/(296.8-sum(gaps)-1.6))
    cursor=.8;pieces=[];captions=[];pcm=b'\0'*int(cursor*48000)*2
    out=BASE/'work/audio_processed';out.mkdir(exist_ok=True)
    for i,r in enumerate(rows):
        dest=out/f'{r["id"]:02d}.wav'
        subprocess.run([str(FF),'-loglevel','error','-y','-i',str(BASE/f'audio/{r["id"]:02d}.wav'),'-af',f'atempo={speed:.9f},aresample=48000',
                        '-ac','1','-c:a','pcm_s16le',str(dest)],check=True)
        with wave.open(str(dest)) as w:data=w.readframes(w.getnframes());dur=w.getnframes()/48000
        r['start']=round(cursor,6);r['end']=round(cursor+dur,6);r['gap_after']=gaps[i]
        pcm+=data+b'\0'*round(gaps[i]*48000)*2
        # Each synthesis event repeats the cumulative word list; retain the
        # final, complete list for each sentence only.
        ends={}
        for e in r['tts']['events']:
            o=e.get('output',{});s=o.get('sentence',{});ws=s.get('words',[])
            if ws and len(ws)>=len(ends.get(s.get('index',0),[])):ends[s.get('index',0)]=ws
        words=[]
        for k,ws in sorted(ends.items()):words+=ws
        spoken='';times=[]
        for w in words:
            txt=w['text'];a=w['begin_time']/1000/speed;b=w['end_time']/1000/speed
            spoken+=txt;times.extend([a+(b-a)*j/max(1,len(txt)) for j in range(len(txt))])
        mapping={}
        for block in difflib.SequenceMatcher(None,r['text'],spoken,autojunk=False).get_matching_blocks():
            for j in range(block.size):mapping[block.a+j]=block.b+j
        parts=split_text(r['text']);starts=[]
        for a,b,txt in parts:
            if a==0:local=0
            else:
                near=next((k for k in range(a,min(a+12,len(r['text']))) if k in mapping),None)
                local=times[mapping[near]] if near is not None and times else dur*a/len(r['text'])
            starts.append(local)
        for j,(a,b,txt) in enumerate(parts):
            captions.append(dict(utterance=r['id'],section=r['section'],text=txt,start=cursor+starts[j],
                                 end=cursor+(starts[j+1]-.015 if j+1<len(parts) else dur)))
        r.pop('tts');r['caption_parts']=len(parts);cursor+=dur+gaps[i]
    pcm+=b'\0'*int(.8*48000)*2;duration=len(pcm)/2/48000
    with wave.open(str(BASE/'配音.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes(pcm)
    timeline=dict(duration=duration,post_speed=speed,model='qwen-audio-3.1-tts-flash',voice='longanlingxin_v3.1',items=rows,captions=captions)
    (BASE/'work/timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
    (BASE/'演示视频.srt').write_text('\n\n'.join(f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(captions,1))+'\n')
    ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Noto Sans CJK SC,40,&H00FFFFFF,&H00FFFFFF,&H60101D35,&H00101D35,-1,0,0,0,100,100,0,0,1,1,0,2,60,60,25,1
Style: Label,Noto Sans CJK SC,18,&H00A8BFE4,&H00FFFFFF,&H00101D35,&H00101D35,0,0,0,0,100,100,0,0,1,0,0,7,30,30,967,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    for c in captions:ass+=f'Dialogue: 1,{stamp(c["start"],True)},{stamp(c["end"],True)},Caption,,0,0,0,,{c["text"]}\n'
    for i,r in enumerate(rows):
        if i and r['section']==rows[i-1]['section']:continue
        end=next((x['start'] for x in rows[i+1:] if x['section']!=r['section']),duration)
        ass+=f'Dialogue: 0,{stamp(r["start"],True)},{stamp(end,True)},Label,,0,0,0,,{r["section"]}\n'
    (BASE/'work/captions.ass').write_text(ass)
    print(json.dumps(dict(duration=duration,post_speed=speed,utterances=len(rows),captions=len(captions),max_caption=max(len(c['text']) for c in captions)),ensure_ascii=False))

if __name__=='__main__':main()
