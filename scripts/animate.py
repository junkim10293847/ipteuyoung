"""명화 인물 움직이는 영상 만들기 (LivePortrait, CPU)
사용: python scripts/animate.py "mona,pearl" "talking.pkl:all:talk,talking.pkl:pose:idle"
 - 드라이버 표기: 파일:움직일부분(all/pose/eyes/lip/exp):이름표
 - 결과: img/anim/{인물}-{이름표}.mp4 (가로 360, 소리 없음, 앞뒤로 이어 붙여 끊김 없이 반복)"""
import os, sys, subprocess, glob, shutil, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LP = os.environ.get('LP', '/tmp/lp')
chars = [c for c in sys.argv[1].split(',') if c]
drivers = [d for d in sys.argv[2].split(',') if d]
os.makedirs(f'{REPO}/img/anim', exist_ok=True)
for k in chars:
    src = f'{REPO}/img/paint/{k}.jpg'
    for spec in drivers:
        p = spec.split(':'); drv = p[0]; region = p[1] if len(p) > 1 else 'all'; tag = p[2] if len(p) > 2 else drv.split('.')[0]
        out = f'/tmp/out/{k}-{tag}'; shutil.rmtree(out, ignore_errors=True)
        t = time.time()
        cmd = ['python', 'inference.py', '-s', src, '-d', f'assets/examples/driving/{drv}', '-o', out,
               '--flag_force_cpu', '--animation_region', region]
        if os.environ.get('MULT'):   # 움직임 세기 (1=원래, 0.6=차분하게) — 가만히·말하기 모두 같은 값을 써야 고개 움직임이 맞음
            cmd += ['--driving_multiplier', os.environ['MULT']]
        try:
            r = subprocess.run(cmd, cwd=LP, capture_output=True, text=True, timeout=int(os.environ.get('CLIP_TIMEOUT', '2400')))
        except subprocess.TimeoutExpired:
            print(k, tag, '시간 초과', flush=True); continue
        vids = [v for v in glob.glob(f'{out}/*.mp4') if 'concat' not in v]
        print(k, tag, 'rc', r.returncode, f'{time.time()-t:.0f}s', vids, flush=True)
        if r.returncode or not vids:
            print(r.stdout[-1500:], r.stderr[-2500:], flush=True); continue
        dst = f'{REPO}/img/anim/{k}-{tag}.mp4'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vids[0], '-filter_complex',
                        '[0:v]scale=360:-2,split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1,format=yuv420p[v]',
                        '-map', '[v]', '-an', '-c:v', 'libx264', '-crf', '27', '-preset', 'slow', '-movflags', '+faststart', dst], check=True)
        print('  ->', dst, os.path.getsize(dst)//1024, 'KB', flush=True)
        if os.environ.get('SAVE_EACH'):   # 하나 만들 때마다 바로 저장 (중간에 멈춰도 남도록)
            subprocess.run(f'cd {REPO} && git add img/anim && git commit -qm "움직이는 인물 영상: {k}-{tag}" && (for i in 1 2 3 4 5; do git pull -q --rebase origin main && git push -q origin HEAD:main && break; sleep 5; done)', shell=True)
import json
names = sorted(os.path.basename(v) for v in glob.glob(f'{REPO}/img/anim/*.mp4') + glob.glob(f'{REPO}/img/paint/*-cut.png'))
json.dump(names, open(f'{REPO}/img/anim/index.json', 'w'), ensure_ascii=False)
print('index', len(names))
