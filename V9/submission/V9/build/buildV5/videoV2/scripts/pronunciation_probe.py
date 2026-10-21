"""Compare short pronunciation variants before committing the narration."""
import base64, concurrent.futures, json, wave, requests
from tts import BASE,key,MODEL,VOICE,stream_events

def review(path, prompt, output):
    s=requests.Session();s.trust_env=False
    body={'model':'qwen3.5-omni-plus','messages':[{'role':'user','content':[{'type':'input_audio','input_audio':{'data':'data:audio/wav;base64,'+base64.b64encode(path.read_bytes()).decode(),'format':'wav'}},{'type':'text','text':prompt}]}],'stream':True,'modalities':['text']}
    r=s.post('https://maas.qianwenaiapi.com/compatible-mode/v1/chat/completions',headers={'Authorization':'Bearer '+key()},json=body,stream=True,timeout=120)
    r.raise_for_status();out=''
    for line in r.iter_lines():
        if line.startswith(b'data:') and line[5:].strip()!=b'[DONE]':
            e=json.loads(line[5:]);out+=''.join(c.get('delta',{}).get('content','') or '' for c in e.get('choices',[]))
    output.write_text(out);print(out,flush=True)

def one(v):
    n,word,pron=v;s=requests.Session();s.trust_env=False
    inp={'text':f'系统用{word}表示这个字段能够带来的最大提升。','voice':VOICE,'format':'pcm','sample_rate':24000,'rate':1.1,'word_timestamp_enabled':True,'seed':2026,'instruction':'标准普通话，清楚自然地讲解软件演示。'}
    inp['language_hints']=['zh']
    inp['hot_fix']={'pronunciation':[{'M':pron}] if pron else [],'replace':[]}
    r=s.post('https://maas.qianwenaiapi.com/api/v1/services/audio/tts/SpeechSynthesizer',headers={'Authorization':'Bearer '+key(),'X-DashScope-SSE':'enable','Content-Type':'application/json'},json={'model':MODEL,'input':inp},stream=True,timeout=120)
    r.raise_for_status();pcm=b''
    for e in stream_events(r):
        d=(e.get('output',{}).get('audio') or {}).get('data')
        if d:pcm+=base64.b64decode(d)
    assert pcm
    p=BASE/f'work/pronunciation_variant_{n}.wav'
    with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(pcm)
    print('Variant',n,len(pcm)/48000,flush=True)
    return pcm

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        audios=list(pool.map(one,[(1,' M ',None),(2,' M ','ai3 mu3'),(3,'矮姆',None),(4,'矮木',None)]))
    p=BASE/'work/pronunciation_variants.wav'
    with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes((b'\0'*48000).join(audios))
    review(p,'这里有四句语音，都是“系统用……表示这个字段能够带来的最大提升”。请根据实际听到的音频，逐句给出中间那个词听起来是什么（拼音和声调），不要按含义自动纠错。这里期望读的是英文字母 M，中文习惯音“矮姆”，第一个音节是第三声。哪一段最接近期望、自然清楚？若听不清声调，请明确表示不确定。',BASE/'work/pronunciation_variant_review.txt')
