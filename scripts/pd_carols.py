"""위키미디어 공용에서 '퍼블릭 도메인' 캐럴 녹음(미국 군악대 등)을 찾아 받아 mp3로 바꿈 → diag/pdcarol/"""
import json, os, re, subprocess, time, urllib.error, urllib.parse, urllib.request
OUT = 'diag/pdcarol'; os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'ipteuyoung-study-app/1.0 (github.com/junkim10293847/ipteuyoung)'}
def get(u, timeout=60):
    for k in range(6):
        time.sleep(2.5)
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(20 * (k + 1))
    raise RuntimeError('429 계속')
def api(**q):
    q.update(format='json'); u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(q)
    return json.loads(get(u))
QUERIES = ['"Army Band" carol', '"Army Band" Christmas', '"Navy Band" Christmas', '"Air Force Band" Christmas', '"Marine Band" Christmas',
           'Jingle Bells', '"We Wish You a Merry Christmas"', '"Deck the Halls"', '"Joy to the World"', '"Hark the Herald"',
           '"O Tannenbaum"', '"God Rest"', '"Carol of the Bells"', '"Jingle Bells" 1898', '"Jingle Bells" Edison']
seen, rows = set(), []
for q in QUERIES:
    try: r = api(action='query', list='search', srsearch=q + ' filetype:audio' if 'filetype' not in q else q, srnamespace=6, srlimit=40)
    except Exception as e: print('search fail', q, e); continue
    for h in r.get('query', {}).get('search', []):
        t = h['title']
        if t in seen: continue
        seen.add(t)
        try:
            ii = api(action='query', titles=t, prop='imageinfo', iiprop='url|size|extmetadata|mediatype')['query']['pages']
            info = list(ii.values())[0]['imageinfo'][0]
        except Exception as e: print('info fail', t, e); continue
        md = info.get('extmetadata', {})
        lic = (md.get('LicenseShortName', {}).get('value') or '')
        if not re.search(r'public domain|^PD|CC0', lic, re.I): continue
        if info.get('size', 0) > 40_000_000: continue
        rows.append({'title': t, 'url': info['url'], 'license': lic,
                     'artist': re.sub('<[^>]+>', '', md.get('Artist', {}).get('value', ''))[:120],
                     'date': re.sub('<[^>]+>', '', md.get('DateTimeOriginal', {}).get('value', ''))[:40]})
print(len(rows), 'public-domain audio files')
keep = []
for i, r in enumerate(rows[:40]):
    name = f'{i:02d}'
    src = f'/tmp/{name}' + os.path.splitext(r['url'])[1]
    try:
        open(src, 'wb').write(get(r['url'], 180))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-t', '75', '-ac', '1', '-ar', '32000', '-b:a', '64k', f'{OUT}/{name}.mp3'], check=True)
        r['file'] = name + '.mp3'; keep.append(r)
    except Exception as e: print('dl fail', r['title'], e)
json.dump(keep, open(f'{OUT}/list.json', 'w'), ensure_ascii=False, indent=1)
for r in keep: print(r['file'], r['license'], '|', r['title'], '|', r['artist'], r['date'])
