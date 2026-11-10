import json, time, urllib.request, re
api = re.search(r'https://script[^"]+', open('config.js').read()).group(0)
def call(fn, *args):
    try:
        req = urllib.request.Request(api, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain;charset=utf-8'})
        return urllib.request.urlopen(req, timeout=180).read().decode()[:1500]
    except Exception as e:
        return 'EXC ' + repr(e)[:200]
lst=[{"n":0,"en":"The government announced on Monday that it will expand financial support for small businesses struggling with rising interest rates."},
     {"n":1,"en":"Experts say the measure could ease the burden on owners, but some raised concerns about the long-term cost to taxpayers."}]
p='''영어 뉴스 듣기를 연습하는 한국인 학습자를 위해, 각 문장을 앞에서부터 순서대로 이해할 수 있는 의미 덩어리(sense group)로 나눈다.
규칙: 원문 단어와 문장부호를 하나도 바꾸거나 빼거나 더하지 말고, 덩어리 사이에만 " / "를 넣는다. 한 덩어리는 보통 2~6단어. 주어부 / 동사부 / 목적어·보어 / 전치사구 / 접속사·관계사절 앞에서 끊는다. 아주 짧은 문장은 그대로 둬도 된다.
'''+json.dumps(lst)+'''
{"items":[{"n":번호,"ch":"덩어리 / 덩어리 / ..."}]} 형태의 JSON으로만 답한다.'''
open('diag/qa_result.txt','w').write(call('aiJson',p))
