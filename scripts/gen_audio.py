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


TEXTS = os.path.join(AUDIO, 'texts.json')
WEEKS = os.path.join(os.path.dirname(AUDIO), 'data', 'weeks.json')


def save_weeks(weeks):
    """화면이 바로 열리도록 주차 목록을 이 사이트(GitHub Pages)에 정적 파일로도 둠. 바뀐 경우에만 씀"""
    os.makedirs(os.path.dirname(WEEKS), exist_ok=True)
    new = json.dumps(weeks, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
    old = open(WEEKS, encoding='utf-8').read() if os.path.exists(WEEKS) else ''
    if new != old:
        open(WEEKS, 'w', encoding='utf-8').write(new)
        return True
    return False


def load_texts():
    try:
        return json.load(open(TEXTS, encoding='utf-8'))
    except Exception:
        return {}


def save_texts(t):
    new = json.dumps(t, ensure_ascii=False, sort_keys=True, indent=0)
    old = open(TEXTS, encoding='utf-8').read() if os.path.exists(TEXTS) else ''
    if new != old:
        open(TEXTS, 'w', encoding='utf-8').write(new)
        return True
    return False


def plan(weeks, have, texts=None):
    """화면이 찾을 음성 파일 중 없거나, 같은 이름인데 문장이 바뀐 것(같은 날짜에 새 지문을 올린 경우)을 고름.
    texts.json 에 파일별로 어떤 문장을 읽었는지 기록해 두고 비교함"""
    texts = {} if texts is None else texts
    jobs, longs = {}, []
    stale = lambda n, text: n in have and texts.get(n) not in (None, text)
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
                if n not in have or stale(n, en):
                    jobs[n] = (en, v)
                elif n not in texts:
                    texts[n] = en
            for vc in s.get('vocab') or []:
                n = name(vc.get('audio'), f'v-{vkey(vc.get("t"))}.mp3')
                t = clean(vc.get('t'))
                if n not in have or stale(n, t):
                    jobs[n] = (t, 'af')
                elif n not in texts:
                    texts[n] = t
        ln = name(w.get('longAudio'), f'{wk}-long2.mp3')
        sig = '|'.join(src)
        if src and (ln not in have or any(n in jobs for n in src) or stale(ln, sig)):
            longs.append((ln, src))
        elif src and ln not in texts:
            texts[ln] = sig
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
    if '--plan' in sys.argv and not os.environ.get('WEEKS_JSON') and weeks and save_weeks(weeks):
        out('data', 1)
    have = set(os.listdir(AUDIO))
    texts = load_texts()
    jobs, longs = plan(weeks, have, texts)
    todo = len(jobs) + len(longs)
    print(f'만들 음성 {len(jobs)}개, 연속 듣기 {len(longs)}개')
    out('todo', todo)
    if '--plan' in sys.argv:
        if not todo and (write_index() | save_texts(texts)):
            out('todo', 1)
        return
    sys.path.insert(0, os.path.dirname(__file__))
    from tts import synth, save_mp3
    for k, (name, (text, v)) in enumerate(sorted(jobs.items()), 1):
        print(f'[{k}/{len(jobs)}] {name}: {text[:60]}')
        save_mp3(synth(text, VOICE[v]), os.path.join(AUDIO, name))
        texts[name] = text
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
        texts[ln] = '|'.join(src)
        print('연속 듣기:', ln)
    save_texts(texts)
    write_index()


if __name__ == '__main__':
    main()
