"""산타 'Ho ho ho!' 효과음 후보 만들기 (Kokoro 남성 목소리 → 낮고 굵게 + 울림 + 썰매 방울)"""
import os, subprocess, wave, numpy as np, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts

OUT = 'diag/santa'; os.makedirs(OUT, exist_ok=True)
SR = 24000
def sleigh(n_sec, start=0.0, shakes=10, gap=0.11, vol=0.10):
    rng = np.random.default_rng(7); out = np.zeros(int(SR * n_sec))
    L = int(SR * 0.08)
    env = (1 - np.arange(L) / L) ** 2.4
    for k in range(shakes):
        s = int(SR * (start + k * gap)); burst = rng.standard_normal(L) * env * (1.0 if k % 2 == 0 else 0.6) * (1 - k / (shakes + 4))
        # 방울처럼 높은 대역만: 1차 차분 두 번 (고역 강조)
        burst = np.diff(np.diff(burst, prepend=0), prepend=0)
        out[s:s + L] += burst[: len(out[s:s + L])]
    return out / (np.abs(out).max() + 1e-9) * vol

def write_wav(a, p):
    pcm = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

CANDS = [
    ('A_michael', 'am_michael', 'Ho, ho, ho! Merry Christmas!', 0.82, 0.84),
    ('B_onyx', 'am_onyx', 'Ho, ho, ho! Merry Christmas!', 0.82, 0.86),
    ('C_george', 'bm_george', 'Ho, ho, ho! Merry Christmas!', 0.84, 0.86),
    ('D_fenrir', 'am_fenrir', 'Ho! Ho! Ho! Well done!', 0.85, 0.84),
    ('E_lewis', 'bm_lewis', 'Ho, ho, ho! Well done!', 0.84, 0.86),
    ('F_short', 'am_onyx', 'Ho, ho, ho!', 0.8, 0.84),
]
for name, voice, text, speed, pitch in CANDS:
    a = tts.synth(text, voice=voice, speed=speed).astype(np.float64)
    a = a / (np.abs(a).max() + 1e-9) * 0.8
    raw = f'{OUT}/{name}_raw.wav'; write_wav(a, raw)
    # 낮고 굵게(pitch), 따뜻하게(저역 살짝 올리고 치찰음 줄임), 큰 방 울림(aecho)
    proc = f'{OUT}/{name}_proc.wav'
    af = (f'asetrate={int(SR*pitch)},aresample={SR},atempo={1/pitch:.4f},'
          'bass=g=4:f=140,treble=g=-3:f=6000,aecho=0.8:0.55:45|90:0.25|0.15,loudnorm=I=-14:TP=-1.5')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', af, '-ar', str(SR), '-ac', '1', proc], check=True)
    with wave.open(proc) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32767
    total = len(v) / SR + 0.6
    mix = np.zeros(int(SR * total)); mix[:len(v)] += v
    mix += sleigh(total, start=0.0, shakes=int(total / 0.11) - 2)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
    fin = f'{OUT}/{name}.wav'; write_wav(mix, fin)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', fin, '-b:a', '96k', '-ac', '1', f'{OUT}/{name}.mp3'], check=True)
    for p in (raw, proc, fin): os.remove(p)
    print(name, round(total, 2), 's')
