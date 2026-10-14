"""Kokoro(오픈소스, 무료) 음성 합성 — espeak-ng로 발음기호를 만든 뒤 ONNX 모델로 읽음"""
import json, os, re, subprocess, wave
import numpy as np
import onnxruntime as rt

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.environ.get('KOKORO_DIR', os.path.join(HERE, '..', '.kokoro'))
ESPEAK = os.environ.get('ESPEAK', 'espeak-ng')
VOCAB = json.load(open(os.path.join(HERE, 'kokoro_vocab.json'), encoding='utf-8'))['vocab']
_sess = None
_voices = None


def _load():
    global _sess, _voices
    if _sess is None:
        _sess = rt.InferenceSession(os.path.join(MODEL_DIR, 'kokoro.onnx'), providers=['CPUExecutionProvider'])
        _voices = np.load(os.path.join(MODEL_DIR, 'voices.bin'))
    return _sess, _voices


def _ipa(chunk, lang):
    out = subprocess.run([ESPEAK, '-q', '--ipa', '-v', lang, chunk], capture_output=True, text=True).stdout
    return ' '.join(out.split())


def phonemize(text, lang='en-us'):
    text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    res = ''
    for p in re.split(r'([,.!?;:])', text):
        if not p.strip():
            continue
        if re.fullmatch(r'[,.!?;:]', p):
            res = res.rstrip() + p + ' '
        else:
            res += _ipa(p, lang) + ' '
    return ''.join(c for c in res.strip() if c in VOCAB)


def synth(text, voice='af_heart', speed=1.0):
    sess, voices = _load()
    names = {i.name: i for i in sess.get_inputs()}
    tok_in = 'input_ids' if 'input_ids' in names else 'tokens'
    dt = lambda n: np.int64 if 'int64' in names[n].type else (np.int32 if 'int32' in names[n].type else np.float32)
    ph = phonemize(text, 'en-gb' if voice.startswith('b') else 'en-us')
    toks = [VOCAB[c] for c in ph][:510]
    v = voices[voice]
    style = v[min(len(toks), len(v)) - 1]
    inputs = {tok_in: np.array([[0, *toks, 0]], dtype=dt(tok_in)),
              'style': np.asarray(style, dtype=np.float32),
              'speed': np.array([speed], dtype=dt('speed'))}
    return sess.run(None, inputs)[0].squeeze()


def save_mp3(audio, path):
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    wav = path + '.wav'
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm.tobytes())
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-af', 'apad=pad_dur=0.25', '-b:a', '48k', '-ac', '1', path], check=True)
    os.remove(wav)
