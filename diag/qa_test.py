import json, urllib.request, re, time
t0=time.time()
api = re.search(r'https://script[^"]+', open('config.js').read()).group(0)
req = urllib.request.Request(api, data=json.dumps({'fn':'aiJson','args':['한국인 영어 학습자가 아래 표현들을 외웠다. 표현마다 직접 써 보게 하는 확인 퀴즈를 난이도별로 3개씩 만든다.\n규칙: q는 학습자에게 주는 한국어 지시, a는 그 표현을 꼭 쓰는 영어 정답 한 문장.\n세 문제는 문제 모양·주어·시제·장면이 모두 서로 달라야 한다(같은 틀 반복 금지). ① 쉬움(바로 말하기): 짧은 한국어 문장(8~15자)을 영어로. 주어 I, 현재나 과거 평서문. q 예: "\'(한국어)\'를 영어로 말해 보세요." ② 보통(대화 속 대답): 짧은 상황과 상대의 말을 주고 이 표현으로 대답하게 한다. 주어는 he/she/we/they 중 하나, 시제는 미래(will·be going to)나 현재완료. q 예: "친구가 \'요즘 회사 다시 나가?\'라고 물어요. 이 표현을 써서 \'응, 다음 달부터 다시 나가\'라고 대답해 보세요." ③ 도전(응용): 다음 중 하나를 골라 바꿔 가며 낸다 — 상대에게 묻는 질문 만들기 / 부정문으로 말하기 / because·when·if 로 두 생각을 이어 한 문장 / 내 경험을 이 표현으로 한 문장. 20~35자 분량의 한국어 지시로 주고, a는 그에 맞는 영어 한 문장. a(정답)에는 표현을 반드시 넣고, 지문 문장을 그대로 베끼지 않는다.\n[{"n": 0, "t": "return to work", "m": "복직하다", "sentence": "Just before returning to work, we also spent two weeks living in Jeju Island."}, {"n": 1, "t": "make the most of", "m": "최대한 활용하다", "sentence": "I decided to make the most of my time."}]\nJSON만: {"items":[{"n":번호,"quizzes":[{"q":"...","a":"..."},{"q":"...","a":"..."},{"q":"...","a":"..."}]}]}']}).encode(), headers={'Content-Type':'text/plain;charset=utf-8'})
try:
    body=urllib.request.urlopen(req, timeout=300).read().decode()
except Exception as e:
    body='EXC '+repr(e)
open('diag/qa_result.txt','w').write(f'{time.time()-t0:.1f}s\n'+body)
