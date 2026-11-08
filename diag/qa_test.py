import json, time, urllib.request, re
api = re.search(r'https://script[^"]+', open('config.js').read()).group(0)
def call(fn, *args):
    t = time.time()
    try:
        req = urllib.request.Request(api, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain;charset=utf-8'})
        return f'{time.time()-t:.1f}s ' + urllib.request.urlopen(req, timeout=180).read().decode()[:600]
    except Exception as e:
        return f'{time.time()-t:.1f}s EXC ' + repr(e)[:200]
p = '''너는 한국인 초보 영어 학습자를 다정하게 가르치는 영어 강사다.
앞서 학습자가 한 질문: Return to work to 들어간 이유는
그에 대한 설명 끝에 낸 확인 퀴즈: '다음 주에 직장으로 복귀합니다'를 영어로 말해 보세요.
학습자의 답: I am going to return to work.
규칙: "ok","fixed","better","tip"
JSON만 답한다: {"ok":true,"fixed":"...","better":"...","tip":"..."}'''
out=[]
out.append('features: '+call('features'))
for k in range(3): out.append(f'quiz #{k+1}: '+call('aiJson', p))
open('diag/qa_result.txt', 'w').write('\n'.join(out))
