import json, time
from playwright.sync_api import sync_playwright
out = []
try:
  with sync_playwright() as p:
    b = p.chromium.launch()
    for vw in [(390, 844), (820, 1180)]:
      pg = b.new_page(viewport={'width': vw[0], 'height': vw[1]})
      errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
      bad = []; pg.on('response', lambda r: bad.append(f'{r.status} {r.url[-60:]}') if r.status >= 400 else None)
      t0 = time.time(); pg.goto('https://junkim10293847.github.io/ipteuyoung/?final=1', wait_until='networkidle')
      pg.fill('#nickInput', '점검봇'); pg.click('#gateForm button[type=submit]')
      pg.wait_for_selector('#list .card', timeout=30000); out.append(f'[{vw[0]}px] load+data {time.time()-t0:.1f}s, cards {pg.locator("#list .card").count()}')
      out.append('  add panel hidden: ' + str(not pg.is_visible('#addPanel')))
      la = pg.evaluate("(document.getElementById('longAudio')||{}).src||''")
      st = pg.evaluate("async u=>u?(await fetch(u,{method:'HEAD'})).status:0", la); out.append(f'  long audio {la[-30:]} -> {st}')
      first = pg.evaluate("(()=>{const w=weeks.find(x=>x.id===curId);return w.sentences.filter(s=>!s.isTitle).map(s=>[s.audio,(s.alt||{}).am,(s.alt||{}).bf])})()")
      miss = 0
      for trio in first:
        for u in trio:
          if not u or pg.evaluate("async u=>(await fetch(u,{method:'HEAD'})).status", u) != 200: miss += 1
      out.append(f'  sentence audio files missing: {miss} of {len(first)*3}')
      c = pg.locator('#list .card').first; c.locator('button.write').click(); pg.wait_for_timeout(300)
      c.locator('textarea').fill('test'); c.locator('.wr-check').click(); pg.wait_for_timeout(400)
      out.append('  grading shown: ' + str(pg.locator('#list .card').first.locator('.wr-res').count() == 1))
      out.append('  page errors: ' + json.dumps(errs[:3])); out.append('  http errors: ' + json.dumps(bad[:5]))
      pg.close()
    b.close()
except Exception as e:
  out.append('EXC: ' + repr(e)[:400])
open('diag/qa_result.txt', 'w').write('\n'.join(out))
