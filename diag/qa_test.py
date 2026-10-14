import json, os, time
from playwright.sync_api import sync_playwright
out = []
try:
  with sync_playwright() as p:
      b = p.chromium.launch()
      pg = b.new_page(viewport={'width': 820, 'height': 1180})
      pg.on('pageerror', lambda e: out.append('pageerror: ' + str(e)[:300]))
      pg.goto('https://junkim10293847.github.io/ipteuyoung/?t=9', wait_until='networkidle')
      out.append('example in page: ' + str(pg.evaluate("typeof DETAIL_EXAMPLE!=='undefined'")))
      pg.fill('#nickInput', '점검봇'); pg.click('#gateForm button[type=submit]'); pg.wait_for_timeout(6000)
      if pg.locator('[data-view="all"]').count():
          pg.locator('[data-view="all"]').first.click(); pg.wait_for_timeout(1500)
      tgt = pg.evaluate("""()=>{const w=weeks.find(x=>x.id===curId);for(let i=0;i<w.sentences.length;i++){const vs=w.sentences[i].vocab||[];for(let j=0;j<vs.length;j++){if(!vs[j].detail)return [i,j,vs[j].t,w.sentences[i].en]}}return null}""")
      out.append('target: ' + json.dumps(tgt, ensure_ascii=False))
      if tgt:
          i, j = tgt[0], tgt[1]
          card = pg.locator('#c%d' % i)
          card.locator('details.voc summary').first.click(); pg.wait_for_timeout(800)
          card.locator('.vmore[data-k="%d-%d"]' % (i, j)).click()
          t0 = time.time()
          while time.time() - t0 < 120 and card.locator('.vdet, .det').count() == 0 and '만드는 중' in card.inner_text(): pg.wait_for_timeout(2000)
          pg.wait_for_timeout(1500)
          out.append('detail seconds: %d' % (time.time() - t0))
          txt = card.inner_text(); k = txt.find('핵심 의미')
          out.append('DETAIL:\n' + txt[k:k+1800])
          form = card.locator('.qa-form').first
          form.locator('input').fill('이 표현 비슷한 말이랑 뭐가 달라요?'); form.locator('.primary').click()
          t0 = time.time()
          while time.time() - t0 < 120 and '생각하는 중' in card.locator('.qa').first.inner_text(): pg.wait_for_timeout(2000)
          out.append('qa seconds: %d' % (time.time() - t0))
          out.append('QA:\n' + card.locator('.qa').first.inner_text()[-1200:])
      b.close()
except Exception as e:
  out.append('EXC: '+repr(e)[:500])
open('diag/qa_result.txt', 'w').write('\n'.join(out))
