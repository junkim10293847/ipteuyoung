import json, time, urllib.request, re
api = re.search(r'https://script[^"]+', open('config.js').read()).group(0)
def call(fn, *args):
    t = time.time()
    try:
        req = urllib.request.Request(api, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain;charset=utf-8'})
        return f'{time.time()-t:.1f}s ' + urllib.request.urlopen(req, timeout=180).read().decode()[:1500]
    except Exception as e:
        return 'EXC ' + repr(e)[:200]
lst = [{"n":0,"en":"Just before returning to work, we also spent two weeks living in Jeju Island.","ko":"복직 직전에는 제주도에서 두 달이 아니라 두 주 동안 살기도 했다."},
       {"n":1,"en":"I had postpartum depression.","ko":"나는 산후우울증을 겪었다."}]
prompt = '''너는 꼼꼼한 영한 번역 검수자다. 아래는 영어 원문과 한국어 해석 쌍이다.
해석이 다음 중 하나에 해당하는 것만 골라 고친다.
- 원문에 없는 내용(대조 '~이 아니라', 강조, 추측, 부연 설명)을 덧붙임
- 원문의 내용 일부를 빠뜨림
- 뜻·숫자·기간·시제·주어를 잘못 옮김
- 한국어로 매우 어색함
문제없는 항목은 답에 넣지 않는다. 고칠 때는 원문 뜻 그대로 자연스러운 한국어 한 문장으로.
''' + json.dumps(lst, ensure_ascii=False) + '''
{"fix":[{"n":번호,"ko":"고친 해석","why":"짧은 이유"}]} 형태의 JSON으로만 답한다. 고칠 것이 없으면 {"fix":[]}.'''
open('diag/qa_result.txt', 'w').write('koCheck: ' + call('aiJson', prompt))
