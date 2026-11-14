import json, time, urllib.request, re
api = re.search(r'https://script[^"]+', open('config.js').read()).group(0)
def call(fn, *args):
    t = time.time()
    try:
        req = urllib.request.Request(api, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain;charset=utf-8'})
        body = urllib.request.urlopen(req, timeout=180).read().decode()
        return f'{time.time()-t:.1f}s ' + body[:160]
    except Exception as e:
        return f'{time.time()-t:.1f}s EXC ' + repr(e)[:200]
p = '''너는 영어 강사다. [확인 퀴즈] '내일 복직해요'를 영어로 말해 보세요. [학습자 답] I return to work tomorrow.
JSON만: {"ok":true,"fixed":"...","better":"...","tip":"..."}'''
out=[]
for k in range(4):
    out.append(f'첨삭 #{k+1}: ' + call('aiJson', p))
out.append('features: ' + call('features'))
open('diag/qa_result.txt','w').write('\n'.join(out))
