"""점검: 휴대폰 수준(CPU 4배 느림·4G)에서 첫 화면 시간과 오래 걸리는 작업"""
import time
from playwright.sync_api import sync_playwright
URL = 'https://junkim10293847.github.io/ipteuyoung/'
out = []
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 412, 'height': 860}, is_mobile=True)
    ctx.add_init_script("""try{localStorage.setItem('nick','홍길동')}catch(e){}
      window.__lt=[];new PerformanceObserver(l=>l.getEntries().forEach(e=>window.__lt.push([Math.round(e.startTime),Math.round(e.duration)]))).observe({type:'longtask',buffered:true});""")
    for visit in (1, 2):
        pg = ctx.new_page(); cdp = ctx.new_cdp_session(pg)
        cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
        cdp.send('Network.enable'); cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 150, 'downloadThroughput': 1.5e6 / 8 * 4, 'uploadThroughput': 750e3 / 8 * 4})
        reqs = []; t0 = time.time()
        pg.on('requestfinished', lambda r, reqs=reqs, t0=t0: reqs.append((round((time.time() - t0) * 1000), r.url.split('?')[0][-60:])))
        pg.goto(URL, wait_until='domcontentloaded'); dcl = round((time.time() - t0) * 1000)
        try:
            pg.wait_for_selector('li.card', timeout=60000); card = round((time.time() - t0) * 1000)
        except Exception:
            card = 'timeout'
        pg.wait_for_timeout(12000)
        lt = pg.evaluate('window.__lt')
        out.append(f'== visit {visit}: html {dcl}ms, first card {card}ms, long tasks(ms start,dur): {sorted(lt, key=lambda x: -x[1])[:8]}')
        for r in sorted(reqs, key=lambda x: -x[0])[:8]:
            out.append(f'  {r[0]}ms {r[1]}')
        pg.close()
    b.close()
open('diag/qa_result.txt', 'w').write('\n'.join(out)); print('\n'.join(out))
