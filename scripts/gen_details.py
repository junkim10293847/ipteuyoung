"""단어·숙어 '자세히' 설명을 미리 만들어 두기 (GitHub Actions에서 30분마다 실행)

앱에서 '자세히'를 누를 때 AI가 그제야 설명을 만들면 15~25초를 기다려야 함.
그래서 이번 주·다음 주 지문의 단어·숙어 중 아직 설명이 없는 것을 미리 만들어 주차 자료에 넣어 둠
→ 누르면 바로 보임. 앱과 똑같은 지시문(index.html의 DETAIL_EXAMPLE 포함)을 씀.

  python scripts/gen_details.py          # 실제 생성
  python scripts/gen_details.py --plan   # 만들 개수만 확인
"""
import datetime, json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MAX_PER_RUN = int(os.environ.get('MAX_DETAILS', '40'))   # 한 번에 최대 개수 (AI 하루 한도 보호)


def api_url():
    src = open(os.path.join(ROOT, 'config.js'), encoding='utf-8').read()
    m = re.search(r'api\s*:\s*["\']([^"\']+)["\']', src)
    return m and m.group(1)


def call(url, fn, *args, timeout=150):
    """서버 호출. 주차 목록은 GET(앱 음성 생성과 같은 방식), 나머지는 POST. 구글 서버가 잠깐 오류를 내면 다시 시도"""
    last = None
    for t in range(3):
        try:
            if fn == 'getWeeks' and not args:
                req = urllib.request.Request(url + ('&' if '?' in url else '?') + 'fn=getWeeks', headers={'User-Agent': 'ipteuyoung-details'})
            else:
                body = json.dumps({'fn': fn, 'args': list(args)}).encode()
                req = urllib.request.Request(url, data=body, headers={'Content-Type': 'text/plain;charset=utf-8'})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                j = json.loads(r.read().decode('utf-8'))
            break
        except urllib.error.HTTPError as e:
            last = e; print(f'  서버 응답 오류({fn}, {t + 1}/3): {e}'); time.sleep(5 * (t + 1))
    else:
        raise last
    if isinstance(j, dict) and j.get('err'):
        raise RuntimeError(j['err'])
    return j.get('res') if isinstance(j, dict) and 'res' in j else j


def example():
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    m = re.search(r'const DETAIL_EXAMPLE=("(?:[^"\\]|\\.)*");', s)
    return json.loads(m.group(1)) if m else ''


def prompt(s, v, ex):
    return f"""너는 한국 성인 학습자(중급)의 영어 암기를 돕는 노련한 강사다. 학습자가 아래 지문 문장을 통째로 외우고 있다. 문장 속 표현 하나를 깊이 이해하도록 설명한다.

[지문 문장] {s.get('en', '')}
[해석] {s.get('ko', '')}
[설명할 표현] {v.get('t', '')}
[간단한 뜻] {v.get('m', '')}

작성 규칙
- 모든 항목(core, usage, examples, similar, tip)을 빠짐없이 채운다.
- core: 핵심 의미와 뉘앙스, 주로 쓰이는 상황을 한국어 2문장으로.
- usage: 이 지문 문장 안에서 어떤 구조로, 무엇과 연결되어, 어떤 뜻으로 쓰였는지 문장 일부를 작은따옴표로 인용해 한국어 2문장으로.
- examples: 일상·업무 상황의 짧고 자연스러운 영어 예문 3개. en은 영어 알파벳으로, ko는 자연스러운 한국어 해석.
- similar: 비슷한 영어 표현 최대 3개. m에는 뜻과 함께 이 표현과의 차이(뉘앙스·격식·쓰임)를 한국어 1~2문장으로.
- tip: 외우는 요령과 학습자가 자주 하는 실수를 한국어 2문장으로.
- 영어를 한글 발음으로 적지 않는다. 존댓말(~입니다, ~합니다)로 쓴다.

[좋은 답의 예시] 지문 문장 "To make rice in a pot, first measure out 240 grams of rice for a family of four."의 표현 "To + 동사원형, ..."에 대한 답:
{ex}

위 예시와 같은 깊이·문체·분량으로, 같은 JSON 형태로만 답한다."""


def norm(d):
    if isinstance(d, list):
        d = d[0] if d else {}
    if not isinstance(d, dict):
        d = {}
    pick = lambda *ks: next((d[k] if isinstance(d[k], str) else json.dumps(d[k], ensure_ascii=False) for k in ks if d.get(k)), '')
    ex = d.get('examples') if isinstance(d.get('examples'), list) else []
    sim = d.get('similar') if isinstance(d.get('similar'), list) else []
    return {'core': pick('core', 'meaning'), 'usage': pick('usage', 'in_sentence', 'usage_in_sentence'), 'tip': pick('tip', 'tips', 'memory_tip'),
            'examples': [{'en': str(x.get('en', '')), 'ko': str(x.get('ko', ''))} for x in ex[:3] if isinstance(x, dict)],
            'similar': [{'t': str(x.get('t', x.get('expression', ''))), 'm': str(x.get('m', x.get('meaning', '')))} for x in sim[:3] if isinstance(x, dict)]}


def good(d):
    return len(d['core']) >= 20 and len(d['usage']) >= 20 and re.search(r'[A-Za-z]{2,}', d['usage']) \
        and sum(1 for x in d['examples'] if re.search(r'[A-Za-z]{3,}', x['en']) and x['ko']) >= 2 and d['tip']


def todo(weeks):
    """이번 주·다음 주(월요일이 2주 전 이후인 주차)의 설명 없는 단어·숙어"""
    since = (datetime.date.today() - datetime.timedelta(days=14)).isoformat()
    out = []
    for wid, w in sorted(weeks.items(), reverse=True):
        if not isinstance(w, dict) or wid < since:
            continue
        for i, s in enumerate(w.get('sentences') or []):
            for j, v in enumerate(s.get('vocab') or []):
                d = v.get('detail') or {}
                if v.get('t') and not (d.get('core') and d.get('usage')):
                    out.append((wid, i, j))
    return out


def flush(url, pend):
    """모아 둔 설명 저장: 저장 직전에 최신 자료를 다시 받아, 그사이 누가 고친 내용은 덮지 않고 설명만 끼워 넣음"""
    if not pend:
        return 0
    fresh = call(url, 'getWeeks') or {}
    n, touched = 0, set()
    for (wid, i, j), (t, d) in pend.items():
        try:
            fv = fresh[wid]['sentences'][i]['vocab'][j]
        except Exception:
            continue
        if fv.get('t') != t or (fv.get('detail') or {}).get('usage'):
            continue
        fv['detail'] = d; touched.add(wid); n += 1
    for wid in touched:
        call(url, 'saveWeek', wid, {'sentences': fresh[wid]['sentences']}, True)
    pend.clear()
    print(f'  → {n}개 저장')
    return n


def main():
    sys.stdout.reconfigure(line_buffering=True)
    url = api_url()
    if not url or not url.startswith('https://'):
        print('서버 주소 없음'); return
    weeks = call(url, 'getWeeks') or {}
    jobs = todo(weeks)
    print(f'설명이 없는 단어·숙어 {len(jobs)}개 (이번에 최대 {MAX_PER_RUN}개)')
    if '--plan' in sys.argv or not jobs:
        return
    ex = example()
    made, pend = 0, {}
    for wid, i, j in jobs[:MAX_PER_RUN]:
        s = weeks[wid]['sentences'][i]; v = s['vocab'][j]
        t0 = time.time()
        try:
            d = norm(call(url, 'aiJson', prompt(s, v, ex)))
            if not good(d):
                d2 = norm(call(url, 'aiJson', prompt(s, v, ex) + '\n\n[주의] 직전 답에서 빠진 항목이 있었다. 모든 항목을 채워 다시 답한다.'))
                d = d2 if good(d2) else d
        except Exception as e:
            print(f'  {wid} {v.get("t")}: 실패 {e}')
            if 'rate_limited' in str(e):
                break
            continue
        if not (d['core'] and d['usage']):
            print(f'  {wid} {v.get("t")}: 내용 부족, 건너뜀'); continue
        pend[(wid, i, j)] = (v.get('t'), d)
        print(f'  {wid} #{i} {v.get("t")}: 완료 ({time.time() - t0:.0f}초)')
        if len(pend) >= 5:
            made += flush(url, pend)
    made += flush(url, pend)
    print(f'설명 {made}개 저장')


if __name__ == '__main__':
    main()
