import json, time, urllib.request, re
api = re.search(r'https://script[^"]+', open('config.js').read()).group(0)
P = '한국인 영어 학습자 모임에서 \'영어로 설명하고 맞히기\' 게임을 한다. 설명을 듣고 표현을 맞혀야 하므로, 학습자용 영영사전(Oxford Learner\'s, Longman, Cambridge 학습자 사전) 수준으로 정확하고 섬세하게 풀어 준다. 사전 문장을 그대로 베끼지 말고 쉬운 말로 다시 쓴다.\n표현마다 아래 항목을 만든다.\n- "def": 영영사전식 정의 2~3문장(25~45단어). 핵심 의미 → 어떤 느낌·정도인지 → 주로 누가/무엇이 하는지까지. 중학~고1 수준 단어.\n- "use": 이 표현을 쓰는 구체적인 상황 한 문장(영어). 예: "You might say this when ..."\n- "ex": 표현 자리를 ____ 로 비운 자연스러운 영어 예문 하나.\n- "syn": 비슷한 말 1~2개와(있으면) 반대말 1개. 예: "similar: resume, go back / opposite: quit"\n- "pos": 품사·형태 (예: "phrasal verb", "idiom", "noun phrase", "verb + to-infinitive")\n- "reg": 말투 (예: "informal, spoken", "neutral", "formal, news")\n- "col": 자주 함께 쓰는 말 2~3개 배열 (예: ["return to work after maternity leave","be ready to return to work"])\n- "nu": 한국어 2~3문장. 비슷한 표현과의 차이, 한국인이 자주 틀리는 점(전치사·관사·시제 등).\n- "ex2": 실제로 쓰는 예문 2개 [{"en":"...","ko":"..."}]\n규칙: def·use·syn·ex 에는 표현에 들어 있는 단어(관사·전치사·대명사 제외)를 절대 쓰지 않는다. ex2·col 에는 써도 된다.\n입력과 같은 순서, 같은 개수로 답한다.\nJSON만: {"items":[{"def":"...","use":"...","ex":"...","syn":"...","pos":"...","reg":"...","col":["..."],"nu":"...","ex2":[{"en":"...","ko":"..."}]}]}\n'
def call(fn, *args):
    t = time.time()
    try:
        req = urllib.request.Request(api, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain;charset=utf-8'})
        return f'{time.time()-t:.1f}s ' + urllib.request.urlopen(req, timeout=180).read().decode()
    except Exception as e:
        return f'{time.time()-t:.1f}s EXC ' + repr(e)[:200]
p = P + '표현 목록: ' + json.dumps(['make the most of (최대한 활용하다)', 'nap time (낮잠 시간)'], ensure_ascii=False)
open('diag/qa_result.txt','w').write(call('aiJson', p))
