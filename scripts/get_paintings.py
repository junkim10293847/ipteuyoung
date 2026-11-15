"""저작권이 끝난 명화(퍼블릭 도메인)를 위키미디어 공용에서 작은 크기로 받아 img/paint/ 에 저장 (GitHub Actions에서 실행)
   scripts/paintings.json 의 검색어로 그림을 찾고, 제목·화가·출처·이용 조건을 img/paint/index.json 에 기록"""
import json, os, urllib.parse, urllib.request
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'img', 'paint')
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'ipteuyoung-study-app/1.0 (GitHub Actions; public-domain painting thumbnails)'}
API = 'https://commons.wikimedia.org/w/api.php?'


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def main():
    items = json.load(open(os.path.join(ROOT, 'scripts', 'paintings.json'), encoding='utf-8'))
    try:
        idx = json.load(open(os.path.join(OUT, 'index.json'), encoding='utf-8'))
    except Exception:
        idx = {}
    for it in items:
        if it['id'] in idx and os.path.exists(os.path.join(OUT, it['id'] + '.jpg')) and not os.environ.get('FORCE'):
            continue   # 이미 받은 그림은 그대로 (얼굴 위치 맞춰 둔 것이 바뀌지 않도록)
        q = {'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': it['search'] + ' filetype:bitmap',
             'gsrnamespace': 6, 'gsrlimit': 5, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': it.get('w', 480)}
        j = json.loads(get(API + urllib.parse.urlencode(q)))
        pages = sorted((j.get('query') or {}).get('pages', {}).values(), key=lambda p: p.get('index', 99))
        pick = None
        for p in pages:
            ii = (p.get('imageinfo') or [{}])[0]
            md = ii.get('extmetadata') or {}
            lic = (md.get('LicenseShortName') or {}).get('value', '')
            if 'public domain' in lic.lower() or lic.upper().startswith('PD'):
                pick = (p, ii, lic)
                break
        if not pick:
            print('못 찾음(퍼블릭 도메인 아님):', it['id'], [p.get('title') for p in pages])
            continue
        p, ii, lic = pick
        open(os.path.join(OUT, it['id'] + '.jpg'), 'wb').write(get(ii['thumburl']))
        idx[it['id']] = {**{k: it[k] for k in ('name', 'title', 'artist', 'year')}, **({'bg': True} if it.get('bg') else {}), 'file': p['title'], 'source': ii.get('descriptionurl'), 'license': lic}
        print('저장', it['id'], p['title'], lic)
    json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
