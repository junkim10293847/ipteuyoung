"""점검: AI 첨삭 응답 시간·오류"""
import json, re, time, urllib.request
cfg = open('config.js', encoding='utf-8').read()
url = re.search(r'https://script\.google\.com[^\'"]+', cfg).group(0)
def call(fn, args, t=120):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, data=json.dumps({'fn': fn, 'args': args}).encode(), headers={'Content-Type': 'text/plain'})
        r = json.loads(urllib.request.urlopen(req, timeout=t).read())
        return round(time.time() - t0, 1), json.dumps(r, ensure_ascii=False)[:300]
    except Exception as e:
        return round(time.time() - t0, 1), 'ERR ' + repr(e)[:300]
out = []
out.append('features ' + str(call('features', [])))
p = '학습자 답을 채점한다. 문제: \'내일 오전에는 큰 수술이 있습니다.\'를 영어로. 학습자: "I had a big surgery tomorrow morning." JSON만: {"ok":true/false,"fixed":"...","tip":"..."}'
for i in range(3):
    out.append(f'aiJson#{i} ' + str(call('aiJson', [p, {'modelTier': 'default'}])))
out.append('aiText ' + str(call('aiText', ['Say hi in one word.'])))
open('diag/qa_result.txt', 'w').write('\n'.join(out)); print('\n'.join(out))
