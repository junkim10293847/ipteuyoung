import json, sys
from playwright.sync_api import sync_playwright
out = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 820, 'height': 1180})
    pg.on('console', lambda m: out.append('console ' + m.type + ': ' + m.text[:300]))
    pg.on('pageerror', lambda e: out.append('pageerror: ' + str(e)[:300]))
    pg.on('requestfailed', lambda r: out.append('reqfail: ' + r.url[:120] + ' ' + str(r.failure)))
    pg.goto('https://junkim10293847.github.io/ipteuyoung/?t=1', wait_until='networkidle')
    pg.fill('#nickInput', '점검봇'); pg.click('#gateForm button[type=submit]'); pg.wait_for_timeout(6000)
    out.append('title: ' + pg.inner_text('h1'))
    card = pg.locator('#list .card').first
    card.locator('details.voc summary').first.click(); pg.wait_for_timeout(800)
    qa = card.locator('.qa').first
    out.append('qa before: ' + (qa.inner_text()[:300] if qa.count() else 'NO QA BLOCK'))
    if card.locator('.qa-form input').count():
        card.locator('.qa-form input').first.fill('이 표현 예문 하나만 알려 줘')
        card.locator('.qa-form .primary').first.click()
        pg.wait_for_timeout(25000)
        out.append('qa after: ' + pg.locator('#list .card').first.locator('.qa').first.inner_text()[:500])
        errs = pg.locator('#list .card').first.locator('.err, .status.err').all_inner_texts()
        out.append('err texts: ' + json.dumps(errs, ensure_ascii=False))
    pg.screenshot(path='diag/qa.png', full_page=False)
    b.close()
open('diag/qa_result.txt', 'w').write('\n'.join(out))
print('\n'.join(out))
