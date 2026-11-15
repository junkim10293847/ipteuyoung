"""명화 인물만 오려 내기 (배경 장면 위에 두 인물을 함께 세우기 위함)
 - img/paint/{인물}-cut.png : 원본 그림 크기 그대로, 인물 밖은 투명
 - img/anim/{인물}-{idle|talk}-a.mp4 : 위쪽은 영상, 아래쪽은 흑백 가림판(흰색=인물). 화면에서 둘을 합쳐 인물만 그림
사용: python scripts/cutout.py [인물들(쉼표), 비우면 전부]"""
import os, sys, glob, json, subprocess, shutil
import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = ['mona', 'pearl', 'vincent', 'rembrandt', 'ermine', 'milkmaid', 'castiglione', 'blueboy']
want = [c for c in (sys.argv[1].split(',') if len(sys.argv) > 1 and sys.argv[1] else CHARS) if c]
MODEL = {'pearl': 'u2net_human_seg', 'vincent': 'u2net_human_seg', 'roulin': 'u2net_human_seg'}   # 인물별로 더 잘 오려지는 모델 (기본: isnet-general-use)
_S = {}
def sess(name):
    if name not in _S:
        _S[name] = new_session(name)
    return _S[name]
TEST = len(sys.argv) > 2 and sys.argv[2]   # 모델 비교: 그림만 diag/cut/{인물}-{모델}.png 로 저장
if TEST:
    os.makedirs(f'{REPO}/diag/cut', exist_ok=True)
    for k in want:
        im = Image.open(f'{REPO}/img/paint/{k}.jpg').convert('RGB')
        for mdl in TEST.split(','):
            try:
                m = remove(im, session=sess(mdl), only_mask=True, post_process_mask=True)
                Image.fromarray(np.dstack([np.asarray(im), np.asarray(m.convert('L'))])).save(f'{REPO}/diag/cut/{k}-{mdl}.png')
                print('test', k, mdl, flush=True)
            except Exception as e:
                print('test fail', k, mdl, e, flush=True)
    sys.exit(0)

def mask(img, k=''):
    m = remove(img.convert('RGB'), session=sess(MODEL.get(k, 'isnet-general-use')), only_mask=True, post_process_mask=True)
    return np.asarray(m.convert('L'), dtype=np.float32)

def tidy(m):
    # 가장자리를 2픽셀 안쪽으로 줄이고 부드럽게 → 원래 그림 배경이 테두리에 남는 티를 없앰
    im = Image.fromarray(np.clip(m, 0, 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.3))
    return np.asarray(im, dtype=np.float32)

XF = 20   # 반복 이음새: 끝 20장면을 처음 20장면에 겹쳐 녹여서, 되감기 없이 자연스럽게 반복

for k in want:
    src = f'{REPO}/img/paint/{k}.jpg'
    if os.path.exists(src):
        im = Image.open(src).convert('RGB'); m = tidy(mask(im, k))
        Image.fromarray(np.dstack([np.asarray(im), m.astype(np.uint8)])).save(f'{REPO}/img/paint/{k}-cut.png', optimize=True)
        print('still', k, flush=True)
    for t in ('idle', 'talk'):
        v = f'{REPO}/img/anim/{k}-{t}.mp4'
        if not os.path.exists(v):
            continue
        tmp = f'/tmp/cut/{k}-{t}'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        subprocess.run(['ffmpeg', '-v', 'error', '-i', v, f'{tmp}/f%04d.png'], check=True)
        fs = sorted(glob.glob(f'{tmp}/f*.png')); n = len(fs) // 2   # 앞뒤로 이어 붙인 영상이라 앞 절반만 처리
        ms = [mask(Image.open(f), k) for f in fs[:n]]
        out = f'{tmp}/o'; os.makedirs(out)
        cols = [np.asarray(Image.open(f).convert('RGB'), dtype=np.float32) for f in fs[:n]]
        mks = [tidy(np.mean(ms[max(0, i - 2):i + 3], axis=0)) for i in range(n)]   # 앞뒤 2장면과 평균 → 테두리 떨림 줄이기
        L = n - XF
        for j in range(L):
            c, g = cols[j], mks[j]
            if j < XF:
                a = (j + 1) / (XF + 1)
                c = cols[L + j] * (1 - a) + c * a; g = mks[L + j] * (1 - a) + g * a
            g3 = np.repeat(g[:, :, None], 3, axis=2)
            Image.fromarray(np.vstack([c, g3]).clip(0, 255).astype(np.uint8)).save(f'{out}/s{j:04d}.png')
        dst = f'{REPO}/img/anim/{k}-{t}-a.mp4'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '20', '-i', f'{out}/s%04d.png', '-vf', 'format=yuv420p',
                        '-c:v', 'libx264', '-crf', '24', '-preset', 'slow', '-movflags', '+faststart', dst], check=True)
        print(' ', k, t, n, 'frames ->', os.path.getsize(dst) // 1024, 'KB', flush=True)
if not (len(sys.argv) > 1 and sys.argv[1]):   # 전체 실행일 때만 목록 갱신 (시험 실행은 목록을 건드리지 않음)
  names = sorted(os.path.basename(v) for v in glob.glob(f'{REPO}/img/anim/*.mp4') + glob.glob(f'{REPO}/img/paint/*-cut.png'))
  json.dump(names, open(f'{REPO}/img/anim/index.json', 'w'), ensure_ascii=False)
