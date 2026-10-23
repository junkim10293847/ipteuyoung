import json, time, urllib.request, re
api = re.search(r'https://script[^"]+', open('config.js').read()).group(0)
out = []
def call(fn, *args):
    t = time.time()
    try:
        req = urllib.request.Request(api, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain;charset=utf-8'})
        r = urllib.request.urlopen(req, timeout=180).read().decode()
        return f'{time.time()-t:.1f}s ' + r[:300]
    except Exception as e:
        return f'{time.time()-t:.1f}s EXC ' + repr(e)[:200]
out.append('features: ' + call('features'))
out.append('aiText short: ' + call('aiText', 'Say OK in one word.'))
p = '''너는 영어 강사다. [지문 문장] At the forest we can enjoy forest activities and go on walks. [설명할 표현] go on walks [간단한 뜻] 산책을 가다
core, usage, examples(en,ko 3개), similar(t,m 3개), tip 키를 가진 JSON으로 한국어로 자세히 답한다.'''
EX = ''
long = p + "\n\n[좋은 답의 예시]\n" + EX + "\n위 예시와 같은 깊이·문체·분량으로, 같은 JSON 형태로만 답한다."
for k in range(2):
    out.append(f'aiJson short #{k+1}: ' + call('aiJson', p))
out.append('aiJson real-length: ' + call('aiJson', long))
open('diag/qa_result.txt', 'w').write('\n'.join(out))
