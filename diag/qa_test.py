import json, os
from playwright.sync_api import sync_playwright
Q = os.environ.get('Q', 'drain이 잘 머리속에 안들어오네')
WORD = os.environ.get('WORD', 'drain')
out = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 820, 'height': 1180})
    pg.on('pageerror', lambda e: out.append('pageerror: ' + str(e)[:300]))
    pg.goto('https://junkim10293847.github.io/ipteuyoung/?t=2', wait_until='networkidle')
    pg.fill('#nickInput', '점검봇'); pg.click('#gateForm button[type=submit]'); pg.wait_for_timeout(6000)
    if pg.locator('[data-view="all"]').count():
        pg.locator('[data-view="all"]').first.click(); pg.wait_for_timeout(1500)
    card = pg.locator('#list .card', has_text=WORD).first
    card.locator('details.voc summary').first.click(); pg.wait_for_timeout(800)
    btns = card.locator('.vmore')
    idx = 0
    for i in range(btns.count()):
        if WORD in btns.nth(i).evaluate("e=>e.closest('li,div').innerText"):
            idx = i; break
    btns.nth(idx).click(); pg.wait_for_timeout(20000)
    form = card.locator('.qa-form').first
    form.locator('input').fill(Q); form.locator('.primary').click()
    pg.wait_for_timeout(30000)
    out.append('Q: ' + Q)
    out.append(card.locator('.qa').first.inner_text()[-1500:])
    b.close()
open('diag/qa_result.txt', 'w').write('\n'.join(out))
print('\n'.join(out))
