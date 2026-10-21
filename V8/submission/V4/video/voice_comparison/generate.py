"""Generate two short, otherwise identical Long An Lingxin comparison samples."""
from pathlib import Path
import base64
import concurrent.futures
import json
import math
import re
import shutil
import subprocess
import time
import wave

import requests

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
FFMPEG = Path('/data1/duhaocun/projects/diantan/competition_materials/01_initial_20260907/work/deps/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2')
TEXT = '本视频演示系统的五个阶段，如何发现并处理推断型泄露风险。它指的是敏感字段本身不发布，却被更低等级字段的组合还原出来。'
ARCHIVE = Path('/data1/duhaocun/projects/diantan/competition_materials/09/video3_qwen_work')
SAMPLES = [
    ('Qwen3.0_Plus_龙安灵心', 'qwen-audio-3.0-tts-plus', 'longanlingxin'),
    ('Qwen3.1_龙安灵心', 'qwen-audio-3.1-tts-flash', 'longanlingxin_v3.1'),
]
COMMON = dict(text=TEXT, format='pcm', sample_rate=48000, rate=1.0, volume=50,
              pitch=1.0, seed=2026, language_hints=['zh'])


def api_key():
    values = {}
    for line in (ROOT / 'secrets/deepseek.env').read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            values[k.strip()] = v.strip().strip('\"\'')
    return values['REVIEW_API_KEY']


def generate(sample):
    name, model, voice = sample
    dest = BASE / (name + '_原始.wav')
    meta = BASE / (name + '.json')
    if meta.exists() and json.loads(meta.read_text()).get('input', {}).get('text') != TEXT:
        prior = BASE / '前一段文案样本'
        prior.mkdir(exist_ok=True)
        for old in [dest, meta, BASE / (name + '.mp3')]:
            if old.exists():
                shutil.move(str(old), str(prior / old.name))
    if model == 'qwen-audio-3.0-tts-plus' and not dest.exists():
        manifest = json.loads((ARCHIVE / 'tts_manifest.json').read_text())[:2]
        assert ''.join(row['text'] for row in manifest) == TEXT
        assert all(row['model'] == model and row['voice'] == voice for row in manifest)
        originals = [ARCHIVE / 'audio_raw' / (row['id'] + '.mp3') for row in manifest]
        assert all(path.stat().st_size == row['bytes'] for path, row in zip(originals, manifest))
        subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y',
            '-i', str(originals[0]), '-i', str(originals[1]),
            '-filter_complex', '[0:a][1:a]concat=n=2:v=0:a=1[a]', '-map', '[a]',
            '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', str(dest)], check=True)
        meta.write_text(json.dumps(dict(model=model, voice=voice, input=COMMON,
            source='Archived original per-sentence synthesis, reused without time stretch.',
            source_files=[str(path) for path in originals],
            source_manifest=str(ARCHIVE / 'tts_manifest.json'),
            source_generator='/data1/duhaocun/projects/diantan/competition_materials/09/scripts/video2_tts.py',
            source_parameters='Original SDK defaults; no instruction or speed modification.',
            reason='New call rejected with AllocationQuota.FreeTierOnly. Account settings unchanged.'),
            ensure_ascii=False, indent=2))
    if not dest.exists():
        session = requests.Session()
        session.trust_env = False
        for attempt in range(3):
            response = session.post(
                'https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer',
                headers={'Authorization': 'Bearer ' + api_key(),
                         'Content-Type': 'application/json', 'X-DashScope-SSE': 'enable'},
                json={'model': model, 'input': dict(COMMON, voice=voice)},
                stream=True, timeout=(15, 120))
            if response.status_code < 500:
                break
            print(model, 'HTTP', response.status_code, 'retry', attempt + 1, flush=True)
            response.close()
            time.sleep(2)
        if response.status_code != 200:
            try:
                error = response.json()
                detail = {k: error.get(k) for k in ['code', 'message', 'request_id']}
            except ValueError:
                detail = response.text[:300]
            raise RuntimeError(f'{model} HTTP {response.status_code}: {detail}')
        chunks, request_ids, usage, url = [], [], {}, None
        for line in response.iter_lines():
            if not line.startswith(b'data:'):
                continue
            event = json.loads(line[5:].strip())
            if event.get('code'):
                raise RuntimeError(str({k: event.get(k) for k in ['code', 'message']}))
            if event.get('request_id') and event['request_id'] not in request_ids:
                request_ids.append(event['request_id'])
            usage.update(event.get('usage') or {})
            audio = (event.get('output') or {}).get('audio') or {}
            if audio.get('data'):
                chunks.append(base64.b64decode(audio['data']))
            if audio.get('url'):
                url = audio['url']
        pcm = b''.join(chunks)
        if not pcm and url:
            download = session.get(url, timeout=90)
            download.raise_for_status()
            pcm = download.content
        if not pcm:
            raise RuntimeError('No audio returned for ' + model)
        if pcm[:4] == b'RIFF':
            dest.write_bytes(pcm)
        else:
            with wave.open(str(dest), 'wb') as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(48000)
                output.writeframes(pcm)
        meta.write_text(json.dumps(dict(model=model, voice=voice, input=COMMON,
                                        request_ids=request_ids, usage=usage),
                                   ensure_ascii=False, indent=2))
    result = json.loads(meta.read_text())
    with wave.open(str(dest)) as source:
        result['duration_seconds'] = source.getnframes() / source.getframerate()
        result['sample_rate'] = source.getframerate()
    measurement = subprocess.run([str(FFMPEG), '-hide_banner', '-i', str(dest),
        '-af', 'loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
        capture_output=True, text=True, check=True)
    measured = json.loads(re.findall(r'\{[^{}]+\}', measurement.stderr)[-1])
    gain = min(-18 - float(measured['input_i']), -1.5 - float(measured['input_tp']))
    assert math.isfinite(gain)
    subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(dest),
        '-af', f'volume={gain:.6f}dB', '-c:a', 'libmp3lame', '-b:a', '192k',
        str(BASE / (name + '.mp3'))], check=True)
    result['comparison_processing'] = dict(gain_db=gain, target_lufs=-18,
        original_lufs=float(measured['input_i']), speed_change=False,
        note='Only constant gain adjustment for level matching; no time stretch or dynamic processing.')
    meta.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(model, voice, round(result['duration_seconds'], 2), 'seconds', flush=True)
    return result


if __name__ == '__main__':
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / '试听文本.txt').write_text(TEXT + '\n')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(generate, SAMPLES))
    (BASE / 'comparison.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
