import json, time, re, urllib.request
out = []
cfg = open('config.js').read(); url = re.search(r'https://script\.google\.com/[^"\']+', cfg).group(0)
def call(fn, args=None, method='POST'):
  if method == 'GET':
    req = urllib.request.Request(url + '?fn=' + fn, headers={'User-Agent': 'diag'})
  else:
    req = urllib.request.Request(url, data=json.dumps({'fn': fn, 'args': args or []}).encode(), headers={'Content-Type': 'text/plain', 'User-Agent': 'diag'})
  t = time.time(); r = urllib.request.urlopen(req, timeout=60).read().decode()
  return r, time.time() - t
for k in range(4):
  for m in ['POST', 'GET']:
    try:
      r, dt = call('getWeeks', method=m)
      try:
        j = json.loads(r); d = j.get('data', j) if isinstance(j, dict) else j
        if isinstance(d, dict) and 'weeks' in d: d = d['weeks']
        info = f'weeks={len(d) if isinstance(d, list) else type(d).__name__} ' + (json.dumps([w.get("title") for w in d])[:200] if isinstance(d, list) else '') + ' keys=' + (','.join(j.keys()) if isinstance(j, dict) else '')
      except Exception as e:
        info = 'nonjson ' + r[:300]
      out.append(f'{k} {m} {dt:.1f}s len={len(r)} {info}')
    except Exception as e:
      out.append(f'{k} {m} EXC {repr(e)[:200]}')
  time.sleep(3)
try:
  r, dt = call('getProgress', ['배라']); out.append('progress 배라: ' + r[:300])
except Exception as e: out.append('progress EXC ' + repr(e)[:200])
open('diag/qa_result.txt', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
