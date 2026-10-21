"""Qwen 3.1 TTS with word timestamps; credentials are read only at runtime."""
from pathlib import Path
import argparse, base64, concurrent.futures, json, re, time, wave
import requests

BASE = Path(__file__).resolve().parents[1]
PROJ = BASE.parents[3]
MODEL = 'qwen-audio-3.1-tts-flash'
VOICE = 'longanlingxin_v3.1'

def manifest():
    rows=[]; section=''
    for line in (BASE.parent/'视频讲稿.md').read_text().splitlines():
        m=re.match(r'## (\d\d)｜(.+)',line)
        if m: section=m.group(1)+' '+m.group(2)
        m=re.match(r'^(\d+)\. (.+)$',line)
        if m and section:
            rows.append(dict(id=int(m.group(1)),section=section,text=m.group(2)))
    assert [r['id'] for r in rows]==list(range(1,56))
    (BASE/'work').mkdir(exist_ok=True)
    (BASE/'audio').mkdir(exist_ok=True)
    (BASE/'work/narration.json').write_text(json.dumps(dict(model=MODEL,voice=VOICE,rate=1.1,items=rows),ensure_ascii=False,indent=2))
    return rows

def key():
    env={}
    for line in (PROJ/'secrets/deepseek.env').read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1);env[k.strip()]=v.strip().strip('\"\'')
    return env['REVIEW_API_KEY']

def synth(row):
    dest=BASE/f'audio/{row["id"]:02d}.wav';meta=dest.with_suffix('.json')
    if dest.exists() and meta.exists():return json.loads(meta.read_text())
    session=requests.Session();session.trust_env=False
    body={'model':MODEL,'input':{'text':row['text'],'voice':VOICE,'format':'pcm','sample_rate':24000,'rate':1.1,
        'word_timestamp_enabled':True,'language_hints':['zh'],'seed':2026,
        'instruction':'用标准普通话自然地讲解科研系统演示，清楚、从容、亲切，有自然的轻重和停顿。数字和术语清晰，句子完整收尾，不使用广告腔。',
        'hot_fix':{'pronunciation':[{'重新训练':'chong2 xin1 xun4 lian4'},{'调级':'tiao2 ji2'}],
                   'replace':[{'GB/T 43697':'G B T 四三六九七'},{'PJM':'P J M'}]}}}
    headers={'Authorization':'Bearer '+key(),'Content-Type':'application/json','X-DashScope-SSE':'enable'}
    last=None
    for endpoint in ['https://maas.qianwenaiapi.com/api/v1/services/audio/tts/SpeechSynthesizer',
                     'https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer']:
        try:
            response=session.post(endpoint,headers=headers,json=body,stream=True,timeout=(15,120))
            if response.status_code!=200:
                err=response.json();last={k:err.get(k) for k in ['code','message','request_id']}
                print('TTS endpoint status',response.status_code,last,flush=True);continue
            chunks=[];events=[];url=None
            for line in response.iter_lines():
                if not line or not line.startswith(b'data:'):continue
                event=json.loads(line[5:].strip());out=event.get('output',{})
                if event.get('code'):raise RuntimeError(str({k:event.get(k) for k in ['code','message']}))
                a=out.get('audio') or {}
                if a.get('data'):chunks.append(base64.b64decode(a['data']))
                if a.get('url'):url=a['url']
                events.append({k:v for k,v in event.items() if k!='output'}|{'output':{k:v for k,v in out.items() if k!='audio'}})
            pcm=b''.join(chunks)
            if not pcm and url:
                rr=session.get(url,timeout=90);rr.raise_for_status();pcm=rr.content
            if not pcm:raise RuntimeError('No audio returned')
            if pcm[:4]==b'RIFF':dest.write_bytes(pcm)
            else:
                with wave.open(str(dest),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(pcm)
            with wave.open(str(dest)) as w:duration=w.getnframes()/w.getframerate()
            result={**row,'model':MODEL,'voice':VOICE,'endpoint':endpoint,'duration':duration,'events':events}
            meta.write_text(json.dumps(result,ensure_ascii=False,indent=2))
            print('TTS',row['id'],round(duration,2),'seconds',flush=True)
            return result
        except Exception as e:last=str(e)[:300]
    raise RuntimeError('TTS failed: '+str(last))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');args=p.parse_args()
    rows=manifest()
    if args.test: rows=[rows[3]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(synth,rows))
    print('Completed',len(results),'utterances',flush=True)
