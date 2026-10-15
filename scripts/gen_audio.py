"""새 주차 음성 자동 생성 (GitHub Actions에서 실행)

1) config.js의 Apps Script 주소에서 주차 목록을 받아
2) audio 폴더에 없는 음성(문장 3가지 목소리, 단어·숙어, 한 주 연속 듣기)만 만들고
3) audio/index.json(음성 목록)을 갱신합니다. 화면은 이 목록을 보고 음성을 자동으로 붙입니다.

  python scripts/gen_audio.py --plan   # 만들 개수만 계산 (모델 설치 전 빠른 확인)
  python scripts/gen_audio.py          # 실제 생성
"""
import json, os, re, subprocess, sys, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
AUDIO = os.path.join(ROOT, 'audio')
VOICE = {'af': 'af_heart', 'am': 'am_michael', 'bf': 'bf_emma'}


def api_url():
    src = open(os.path.join(ROOT, 'config.js'), encoding='utf-8').read()
    m = re.search(r'api\s*:\s*["\']([^"\']+)["\']', src)
    url = m and m.group(1)
    if not url or not url.startswith('https://'):
        print('config.js에 Apps Script 주소가 아직 없습니다. 건너뜁니다.')
        return None
    return url


def get_weeks(url):
    if os.environ.get('WEEKS_JSON'):
        return json.load(open(os.environ['WEEKS_JSON'], encoding='utf-8'))
    req = urllib.request.Request(url + ('&' if '?' in url else '?') + 'fn=getWeeks', headers={'User-Agent': 'ipteuyoung-audio'})
    import time
    last = None
    for t in range(4):                      # 구글 서버가 잠깐 응답하지 않을 때 대비해 다시 시도
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                j = json.loads(r.read().decode('utf-8'))
            break
        except Exception as e:
            last = e
            print(f'주차 목록 받기 실패({t + 1}/4): {e}')
            time.sleep(10 * (t + 1))
    else:
        print('서버가 응답하지 않아 이번 확인은 건너뜁니다. 15분 뒤 다시 확인합니다.')
        return None
    if j.get('err'):
        raise SystemExit('Apps Script 오류: ' + j['err'])
    return j.get('res') or {}


def clean(t):
    t = str(t or '')
    x = re.sub(r'\(.*?\)', '', t); x = re.sub(r'[가-힣~]+', '', x); x = re.sub(r'\+.*$', '', x).strip()
    return x or t


def vkey(t):
    return re.sub(r'[^a-z0-9]+', '-', clean(t).lower()).strip('-') or 'x'


def plan(weeks, have):
    """화면이 찾을 음성 파일 중 audio 폴더에 없는 것을 모두 고름 (이미 경로가 적혀 있어도 파일이 없으면 만듦)"""
    jobs, longs = {}, []
    name = lambda path, default: os.path.basename(path) if path else default
    for wid, w in sorted(weeks.items()):
        if not isinstance(w, dict) or not w.get('sentences'):
            continue
        wk = 'w' + re.sub(r'\D', '', wid)
        src = []
        for i, s in enumerate(w['sentences']):
            en = (s.get('en') or '').strip()
            if not en:
                continue
            p = f'{i:02d}'
            alt = s.get('alt') or {}
            main = name(s.get('audio'), f'{wk}-s{p}.mp3')
            src.append(main)
            for n, v in ((main, 'af'), (name(alt.get('am'), f'{wk}-m-s{p}.mp3'), 'am'), (name(alt.get('bf'), f'{wk}-b-s{p}.mp3'), 'bf')):
                if n not in have:
                    jobs[n] = (en, v)
            for vc in s.get('vocab') or []:
                n = name(vc.get('audio'), f'v-{vkey(vc.get("t"))}.mp3')
                if n not in have:
                    jobs[n] = (clean(vc.get('t')), 'af')
        ln = name(w.get('longAudio'), f'{wk}-long2.mp3')
        if ln not in have and src:
            longs.append((ln, src))
    return jobs, longs


def write_index():
    names = sorted(f for f in os.listdir(AUDIO) if f.endswith('.mp3'))
    path = os.path.join(AUDIO, 'index.json')
    new = json.dumps(names, ensure_ascii=False, separators=(',', ':'))
    old = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
    if new != old:
        open(path, 'w', encoding='utf-8').write(new)
        return True
    return False


def out(key, val):
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f'{key}={val}\n')


def main():
    sys.stdout.reconfigure(line_buffering=True)  # GitHub 화면에 진행 상황이 실시간으로 보이게
    os.makedirs(AUDIO, exist_ok=True)
    url = api_url()
    if not url and not os.environ.get('WEEKS_JSON'):
        out('todo', 0); return
    weeks = get_weeks(url)
    if weeks is None:
        out('todo', 0); return
    have = set(os.listdir(AUDIO))
    jobs, longs = plan(weeks, have)
    todo = len(jobs) + len(longs)
    print(f'만들 음성 {len(jobs)}개, 연속 듣기 {len(longs)}개')
    out('todo', todo)
    if '--plan' in sys.argv:
        if not todo and write_index():
            out('todo', 1)
        return
    sys.path.insert(0, os.path.dirname(__file__))
    from tts import synth, save_mp3
    for k, (name, (text, v)) in enumerate(sorted(jobs.items()), 1):
        print(f'[{k}/{len(jobs)}] {name}: {text[:60]}')
        save_mp3(synth(text, VOICE[v]), os.path.join(AUDIO, name))
    for ln, src in longs:
        files = [os.path.join(AUDIO, n) for n in src if os.path.exists(os.path.join(AUDIO, n))]
        if len(files) != len(src):
            print('연속 듣기 건너뜀(문장 음성 부족):', ln); continue
        lst = os.path.join(AUDIO, '_list.txt')
        with open(lst, 'w') as f:
            for p in files:
                f.write(f"file '{p}'\n")
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst,
                        '-ar', '24000', '-ac', '1', '-b:a', '64k', os.path.join(AUDIO, ln)], check=True)
        os.remove(lst)
        print('연속 듣기:', ln)
    write_index()


if __name__ == '__main__':
    main()
