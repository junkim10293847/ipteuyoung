import json, re, time, urllib.request
cfg = open('config.js').read(); url = re.search(r'https://script\.google\.com/[^"\']+', cfg).group(0)
out = []
def call(fn, *args):
  t = time.time()
  try:
    req = urllib.request.Request(url, data=json.dumps({'fn': fn, 'args': list(args)}).encode(), headers={'Content-Type': 'text/plain', 'User-Agent': 'diag'})
    r = urllib.request.urlopen(req, timeout=90).read().decode()
    out.append(f'{fn} {time.time()-t:.1f}s len={len(r)} {r[:220]}')
  except Exception as e:
    out.append(f'{fn} {time.time()-t:.1f}s EXC {repr(e)[:300]}')
call('features'); call('getWeeks'); call('members', 'wrong-pw'); call('checkAdmin', 'change-me-7528')
open('diag/qa_result.txt', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
