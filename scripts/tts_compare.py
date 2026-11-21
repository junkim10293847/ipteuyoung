"""음성 품질 비교: A 지금 방식(int8 모델 + espeak 발음기호) / B 고품질 모델(fp32) + espeak / C 고품질 모델 + misaki(Kokoro 공식 발음 변환)"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import tts
from misaki import en, espeak
OUT = os.path.join(os.path.dirname(__file__), '..', 'diag', 'tts'); os.makedirs(OUT, exist_ok=True)
S = ["Our Lulu is a six-year-old male cat.",
     "My younger sibling brought him home six years ago when he was so sick that he couldn't even open his eyes.",
     "I was planning to have him get a health checkup this year when I happened to learn about blood donation for cats."]
g2p = en.G2P(trf=False, british=False, fallback=espeak.EspeakFallback(british=False))
log = []
def run(model, mode, tag):
    tts._sess = None; tts.MODEL_DIR = os.environ['KK']
    os.environ['KMODEL'] = model
    import onnxruntime as rt
    tts._sess = rt.InferenceSession(os.path.join(os.environ['KK'], model), providers=['CPUExecutionProvider'])
    tts._voices = np.load(os.path.join(os.environ['KK'], 'voices.bin'))
    for k, t in enumerate(S):
        if mode == 'espeak':
            a = tts.synth(t, 'af_heart')
        else:
            ph, _ = g2p(t)
            log.append(f'{tag}{k} misaki: {ph}')
            orig = tts.phonemize; tts.phonemize = lambda text, lang='en-us', _p=ph: _p
            a = tts.synth(t, 'af_heart'); tts.phonemize = orig
        if mode == 'espeak': log.append(f'{tag}{k} espeak: {tts.phonemize(t)}')
        tts.save_mp3(a, os.path.join(OUT, f'{tag}{k+1}.mp3'), 64)
run('int8.onnx', 'espeak', 'A'); run('fp32.onnx', 'espeak', 'B'); run('fp32.onnx', 'misaki', 'C')
open(os.path.join(OUT, 'phonemes.txt'), 'w').write('\n'.join(log)); print('\n'.join(log))
