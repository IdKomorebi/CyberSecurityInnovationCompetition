"""Replace passage 4, re-encoding only its surrounding video GOPs."""
from pathlib import Path
import copy, hashlib, json, re, subprocess, sys, wave

REV = Path(__file__).resolve().parent
BASE = REV.parent
ROOT = BASE.parent
sys.path.insert(0, str(BASE / 'scripts'))
from prepare import FF, SPEED, local_captions, stamp

WORK = REV / 'work'
SOURCE = ROOT / '演示视频.mp4'
DEST = ROOT / '演示视频V2.mp4'

def run(args, log=None):
    r = subprocess.run([str(FF), '-hide_banner', '-nostdin', *map(str, args)], capture_output=True)
    if log:
        (WORK / log).write_bytes(r.stderr)
    assert r.returncode == 0, r.stderr.decode(errors='replace')[-4000:]
    return r

def read_wav(path):
    with wave.open(str(path)) as w:
        assert w.getnchannels() == 1 and w.getframerate() == 48000 and w.getsampwidth() == 2
        return w.readframes(w.getnframes())

def main():
    change = json.loads((WORK / 'change.json').read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == change['original_video_sha256']
    assert hashlib.sha256((ROOT / '视频讲稿.md').read_bytes()).hexdigest() == change['script_sha256']
    timeline = json.loads((BASE / 'work/timeline.json').read_text())
    old = timeline['items'][3]
    meta = json.loads((REV / 'audio/04.json').read_text())
    row = {**old, 'text': change['new']}

    take = WORK / '04_processed.wav'
    run(['-y', '-i', REV / 'audio/04.wav', '-af', f'atempo={SPEED},aresample=48000',
         '-ac', '1', '-c:a', 'pcm_s16le', take])
    row['duration'] = len(read_wav(take)) / 96000
    row['end'] = row['start'] + row['duration']
    assert row['duration'] <= old['duration'], 'Replacement exceeds its original slot.'
    caps = [dict(utterance=4, section=row['section'], text=c['text'],
                 start=row['start'] + c['start'], end=row['start'] + c['end'])
            for c in local_captions(row, meta)]
    updated = copy.deepcopy(timeline)
    updated['items'][3] = row
    updated['captions'] = sorted([c for c in timeline['captions'] if c['utterance'] != 4] + caps,
                                 key=lambda c: c['start'])
    (WORK / 'timeline.json').write_text(json.dumps(updated, ensure_ascii=False, indent=2))
    (ROOT / '演示视频V2.srt').write_text('\n\n'.join(
        f'{i}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}'
        for i, c in enumerate(updated['captions'], 1)) + '\n')

    # Keep the complete original timeline. The shorter sentence leaves a brief viewing pause.
    keyframes = json.loads((WORK / 'keyframes.json').read_text())
    first = round(max(t for t in keyframes if t <= old['start']) * 30)
    last = round(min(t for t in keyframes if t >= old['end']) * 30)
    a, b = first / 30, last / 30
    header = (BASE / 'work/captions.ass').read_text().split('Dialogue:', 1)[0]
    ass = header + ''.join(
        f'Dialogue: 1,{stamp(c["start"]-a,True)},{stamp(c["end"]-a,True)},Caption,,0,0,0,,{c["text"]}\n'
        for c in caps)
    (WORK / 'replacement.ass').write_text(ass)
    run(['-y', '-i', SOURCE, '-map', '0:v:0', '-c', 'copy', '-map_chapters', '-1',
         '-f', 'segment', '-segment_times', f'{a:.9f},{b:.9f}', '-reset_timestamps', '1',
         WORK / 'original_%02d.mp4'], 'split.log')
    print('Original video divided at', a, b, flush=True)

    # Cover only the old caption line; keep the original board and chapter label intact.
    vf = (f"setpts=PTS-STARTPTS,drawbox=x=0:y=998:w=1920:h=82:color=0x101D35:t=fill:"
          f"enable='between(t,{old['start']-a:.9f},{old['end']-a+.02:.9f})',"
          f"ass={WORK / 'replacement.ass'}")
    run(['-y', '-i', WORK / 'original_01.mp4', '-vf', vf, '-an', '-map_chapters', '-1',
         '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-threads', '6', '-r', '30',
         '-pix_fmt', 'yuv420p', '-video_track_timescale', '15360', '-frames:v', last-first,
         WORK / 'replacement.mp4'], 'patch_render.log')
    (WORK / 'join.ffconcat').write_text(
        f"ffconcat version 1.0\nfile 'original_00.mp4'\nduration {a:.9f}\n"
        f"file 'replacement.mp4'\nduration {b-a:.9f}\nfile 'original_02.mp4'\n")
    run(['-y', '-f', 'concat', '-safe', '0', '-i', WORK / 'join.ffconcat', '-map', '0:v:0',
         '-c', 'copy', '-map_chapters', '-1', WORK / 'video_joined.mp4'], 'join.log')
    print('Only', round(b-a, 3), 'seconds of video re-encoded.', flush=True)

    # Match the replacement voice to the original passage's measured loudness.
    measured = run(['-ss', old['start'], '-i', SOURCE, '-t', old['duration'], '-vn',
                    '-af', 'loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json', '-f', 'null', '-'])
    stats = json.loads(re.search(rb'\{\s*"input_i".*?\}', measured.stderr, re.S)[0])
    target = float(stats['input_i'])
    run(['-y', '-i', take, '-af', f'loudnorm=I={target}:TP=-1.5:LRA=9,aresample=48000',
         '-ac', '1', '-c:a', 'pcm_s16le', WORK / '04_matched.wav'])
    run(['-y', '-i', SOURCE, '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s16le',
         WORK / 'original_audio.wav'])
    original_pcm = read_wav(WORK / 'original_audio.wav')
    pcm = bytearray(original_pcm)
    sa, sb = round(old['start'] * 48000) * 2, round(old['end'] * 48000) * 2
    replacement = read_wav(WORK / '04_matched.wav')
    assert len(replacement) <= sb-sa
    pcm[sa:sb] = replacement + bytes(sb-sa-len(replacement))
    assert bytes(pcm[:sa]) == original_pcm[:sa] and bytes(pcm[sb:]) == original_pcm[sb:]
    with wave.open(str(WORK / 'patched_audio.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(pcm)
    run(['-y', '-i', WORK / 'video_joined.mp4', '-i', WORK / 'patched_audio.wav', '-i', SOURCE,
         '-map', '0:v:0', '-map', '1:a:0', '-map_metadata', '2', '-map_chapters', '2',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-ac', '1', '-ar', '48000',
         '-t', timeline['duration'], '-movflags', '+faststart', DEST], 'mux.log')
    report = dict(changed_passage=4, old_text=old['text'], new_text=row['text'],
                  old_audio_duration=old['duration'], new_audio_duration=row['duration'],
                  replacement_start=row['start'], replacement_end=row['end'],
                  original_slot_end=old['end'], video_patch_start_frame=first,
                  video_patch_end_frame=last, video_patch_seconds=b-a,
                  unchanged_pcm_outside_passage=True, target_loudness_lufs=target,
                  duration=timeline['duration'], subtitles=len(updated['captions']),
                  source_sha256=change['original_video_sha256'])
    (WORK / 'replacement_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('V2 CREATED', DEST, flush=True)

if __name__ == '__main__':
    main()
