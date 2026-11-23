"""미국 육군 군악대(U.S. Army Band) 캐럴 녹음 — 미국 정부 저작물이라 퍼블릭 도메인. 위키미디어 공용에서 받아 mp3로 → diag/pdcarol/"""
import json, os, subprocess, time, urllib.error, urllib.parse, urllib.request
OUT = 'diag/pdcarol'; os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'ipteuyoung-study-app/1.0 (github.com/junkim10293847/ipteuyoung; one-time download of 8 files)'}
FILES = ['U.S. Army Band - Hark! The Herald Angels Sing.ogg', 'U.S. Army Band - O Tannenbaum.ogg',
         'U.S. Army Band - Angels We Have Heard on High.ogg', 'U.S. Army Band - Good King Wenceslaus.ogg',
         'U.S. Army Band - Here We Come A-wassailing.ogg', 'U.S. Army Band - Fum, Fum, Fum.ogg',
         'Auld Lang Syne - U.S. Army Band.ogg', 'U.S. Army Band - Il est ne, le divin Enfant.ogg']
keep = []
for i, f in enumerate(FILES):
    u = 'https://commons.wikimedia.org/wiki/Special:FilePath/' + urllib.parse.quote(f.replace(' ', '_'))
    for k in range(5):
        time.sleep(12)
        try:
            data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read(); break
        except urllib.error.HTTPError as e:
            print('retry', f, e.code); time.sleep(60 * (k + 1)); data = None
    if not data: continue
    src = f'/tmp/{i:02d}.ogg'; open(src, 'wb').write(data)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-t', '90', '-ac', '1', '-ar', '32000', '-b:a', '64k', f'{OUT}/{i:02d}.mp3'], check=True)
    keep.append({'file': f'{i:02d}.mp3', 'title': f}); print('ok', f)
json.dump(keep, open(f'{OUT}/list.json', 'w'), ensure_ascii=False, indent=1)
