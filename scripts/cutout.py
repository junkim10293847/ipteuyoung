"""명화 인물만 오려 내기 (배경 장면 위에 두 인물을 함께 세우기 위함)
 - img/paint/{인물}-cut.png : 원본 그림 크기 그대로, 인물 밖은 투명
 - img/anim/{인물}-{idle|talk}-a.mp4 : 위쪽은 영상, 아래쪽은 흑백 가림판(흰색=인물). 화면에서 둘을 합쳐 인물만 그림
사용: python scripts/cutout.py [인물들(쉼표), 비우면 전부]"""
import os, sys, glob, json, subprocess, shutil
import numpy as np
from PIL import Image
from rembg import new_session, remove
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = ['mona', 'pearl', 'vincent', 'rembrandt', 'ermine', 'milkmaid', 'castiglione', 'blueboy']
want = [c for c in (sys.argv[1].split(',') if len(sys.argv) > 1 and sys.argv[1] else CHARS) if c]
S = new_session(os.environ.get('MODEL', 'isnet-general-use'))

def mask(img):
    m = remove(img.convert('RGB'), session=S, only_mask=True, post_process_mask=True)
    return np.asarray(m.convert('L'), dtype=np.float32)

for k in want:
    src = f'{REPO}/img/paint/{k}.jpg'
    if os.path.exists(src):
        im = Image.open(src).convert('RGB'); m = mask(im)
        Image.fromarray(np.dstack([np.asarray(im), m.astype(np.uint8)])).save(f'{REPO}/img/paint/{k}-cut.png', optimize=True)
        print('still', k, flush=True)
    for t in ('idle', 'talk'):
        v = f'{REPO}/img/anim/{k}-{t}.mp4'
        if not os.path.exists(v):
            continue
        tmp = f'/tmp/cut/{k}-{t}'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        subprocess.run(['ffmpeg', '-v', 'error', '-i', v, f'{tmp}/f%04d.png'], check=True)
        fs = sorted(glob.glob(f'{tmp}/f*.png')); n = len(fs) // 2   # 앞뒤로 이어 붙인 영상이라 앞 절반만 처리
        ms = [mask(Image.open(f)) for f in fs[:n]]
        out = f'{tmp}/o'; os.makedirs(out)
        for i in range(n):
            mm = np.mean(ms[max(0, i - 1):i + 2], axis=0)   # 앞뒤 프레임과 평균 → 가장자리 떨림 줄이기
            c = np.asarray(Image.open(fs[i]).convert('RGB'))
            g = np.repeat(mm[:, :, None], 3, axis=2).astype(np.uint8)
            Image.fromarray(np.vstack([c, g])).save(f'{out}/s{i:04d}.png')
        dst = f'{REPO}/img/anim/{k}-{t}-a.mp4'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '20', '-i', f'{out}/s%04d.png', '-filter_complex',
                        '[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1,format=yuv420p[v]', '-map', '[v]',
                        '-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-movflags', '+faststart', dst], check=True)
        print(' ', k, t, n, 'frames ->', os.path.getsize(dst) // 1024, 'KB', flush=True)
names = sorted(os.path.basename(v) for v in glob.glob(f'{REPO}/img/anim/*.mp4'))
json.dump(names, open(f'{REPO}/img/anim/index.json', 'w'), ensure_ascii=False)
