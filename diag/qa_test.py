"""점검: 귀트영 이번 주 문장별 음성 연결 상태"""
import json, re, urllib.request, os
cfg = open('config.js', encoding='utf-8').read()
url = re.search(r'https://script\.google\.com[^\'"]+', cfg).group(0)
req = urllib.request.Request(url, data=json.dumps({'fn': 'getWeeks', 'args': []}).encode(), headers={'Content-Type': 'text/plain'})
res = json.loads(urllib.request.urlopen(req, timeout=60).read())['res']
ws = res if isinstance(res, list) else list(res.values())
out = []
for w in sorted(ws, key=lambda x: x.get('id', ''))[-4:]:
    out.append(f"{w.get('id')} prog={w.get('prog')} title={w.get('title')!r} n={len(w.get('sentences') or [])} longAudio={bool(w.get('longAudio'))}")
    for i, s in enumerate(w.get('sentences') or []):
        a = s.get('audio')
        out.append(f"  {i} T={bool(s.get('isTitle'))} audio={a} exists={bool(a) and os.path.exists('audio/' + a)} {s.get('en', '')[:60]}")
open('diag/qa_result.txt', 'w').write('\n'.join(out))
print('\n'.join(out))
