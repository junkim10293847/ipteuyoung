import json, re, time, urllib.request, datetime
cfg = open('config.js').read(); url = re.search(r'https://script\.google\.com/[^"\']+', cfg).group(0)
def call(fn, *args):
  req = urllib.request.Request(url, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain', 'User-Agent': 'diag'})
  return json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
out = []
try:
  r = call('members', 'change-me-7528')
  if r.get('err'): out.append('err ' + r['err'])
  else:
    for m in r['res']:
      t = datetime.datetime.fromtimestamp(m['updated']/1000, datetime.timezone(datetime.timedelta(hours=9))).strftime('%m/%d %H:%M')
      out.append(f"{m.get('nick') or '(no name)'} | {t} | writes {m.get('writes')} | tests {m.get('tests')} | done {sum((m.get('done') or {}).values())}")
except Exception as e: out.append('EXC ' + repr(e)[:200])
open('diag/qa_result.txt', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
