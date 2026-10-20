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


# 점(.)이 들어간 약어는 문장 끝으로 잘못 끊겨 "에이. 엠." 처럼 이상하게 읽히므로 미리 바꿔 읽음
LETTER = {'a': 'ˈeɪ', 'b': 'bˈiː', 'c': 'sˈiː', 'd': 'dˈiː', 'e': 'ˈiː', 'f': 'ˈɛf', 'g': 'dʒˈiː', 'h': 'ˈeɪtʃ',
          'i': 'ˈaɪ', 'j': 'dʒˈeɪ', 'k': 'kˈeɪ', 'l': 'ˈɛl', 'm': 'ˈɛm', 'n': 'ˈɛn', 'o': 'ˈoʊ', 'p': 'pˈiː',
          'q': 'kjˈuː', 'r': 'ˈɑːɹ', 's': 'ˈɛs', 't': 'tˈiː', 'u': 'jˈuː', 'v': 'vˈiː', 'w': 'dˈʌbəljuː',
          'x': 'ˈɛks', 'y': 'wˈaɪ', 'z': 'zˈiː'}
WORDS = [(r'\bMrs\.', 'Missus'), (r'\bMr\.', 'Mister'), (r'\bMs\.', 'Miz'), (r'\bDr\.', 'Doctor'),
         (r'\bSt\.(?= [A-Z])', 'Saint'), (r'\bvs\.', 'versus'), (r'\betc\.(?=\s+[a-z])', 'et cetera'), (r'\betc\.', 'et cetera.'),
         (r'\be\.g\.', 'for example'), (r'\bi\.e\.', 'that is'), (r'\bNo\.(?= ?\d)', 'number')]
ACR = re.compile(r'\b((?:[A-Za-z]\.){2,})')


def spoken(text):
    """읽기 전에 약어를 소리 나는 말로 바꿈 (바뀐 게 없으면 그대로)"""
    t = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    for a, b in WORDS:
        t = re.sub(a, b, t)
    return t


def phonemize(text, lang='en-us'):
    text = spoken(text)
    res = ''
    for k, part in enumerate(ACR.split(text)):
        if k % 2:  # a.m. / p.m. / U.S. 같은 약어: 글자 이름으로 바로 읽음 (뒤에 문장이 끝나면 마침표 유지)
            letters = re.sub(r'[^A-Za-z]', '', part).lower()
            res += ' '.join(LETTER[c] for c in letters) + ' '
            continue
        for p in re.split(r'([,.!?;:])', part):
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
