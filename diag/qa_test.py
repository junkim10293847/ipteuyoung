import json, time, urllib.request, re
api = re.search(r'https://script[^"]+', open('config.js').read()).group(0)
def call(fn, *args):
    t = time.time()
    try:
        req = urllib.request.Request(api, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain;charset=utf-8'})
        body = urllib.request.urlopen(req, timeout=180).read().decode()
        return f'{time.time()-t:.1f}s ' + body[:300]
    except Exception as e:
        return f'{time.time()-t:.1f}s EXC ' + repr(e)[:200]
p = "너는 영어 강사다. 질문: decide 다음에는 to 와 start 다음 ing 헷갈리네. 4~8줄, 영어 예문과 괄호 속 한국어 해석, 존댓말."
out=[]
for k in range(3): out.append(f'aiText #{k+1}: '+call('aiText', p))
open('diag/qa_result.txt','w').write('\n'.join(out))
