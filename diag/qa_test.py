"""점검: 실제 사이트 첫 화면이 뜨는 시간과 오래 걸리는 요청"""
import time, json
from playwright.sync_api import sync_playwright
URL = 'https://junkim10293847.github.io/ipteuyoung/'
out = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 412, 'height': 860}, is_mobile=True)
    ctx.add_init_script("try{localStorage.setItem('nick','홍길동')}catch(e){}")
    for visit in (1, 2):
        pg = ctx.new_page(); reqs = []; t0 = time.time()
        pg.on('requestfinished', lambda r, reqs=reqs, t0=t0: reqs.append((round((time.time() - t0) * 1000), r.method, r.url[:100])))
        pg.goto(URL, wait_until='domcontentloaded'); dcl = round((time.time() - t0) * 1000)
        try:
            pg.wait_for_selector('li.card', timeout=60000); card = round((time.time() - t0) * 1000)
        except Exception:
            card = 'timeout'
        pg.wait_for_timeout(10000)
        js = pg.evaluate("()=>({longTasks:performance.getEntriesByType('longtask').length})")
        out.append(f'== visit {visit}: html {dcl}ms, first card {card}ms')
        for r in sorted(reqs, key=lambda x: -x[0])[:14]:
            out.append(f'  {r[0]}ms {r[1]} {r[2]}')
        pg.close()
    b.close()
open('diag/qa_result.txt', 'w').write('\n'.join(out)); print('\n'.join(out))
