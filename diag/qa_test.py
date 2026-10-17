import json, re, urllib.request
cfg = open('config.js').read(); url = re.search(r'https://script\.google\.com/[^"\']+', cfg).group(0)
r = urllib.request.urlopen(urllib.request.Request(url + '?fn=getWeeks', headers={'User-Agent': 'diag'}), timeout=60).read().decode()
d = json.loads(r)['res']; out = []
for k in sorted(d):
  w = d[k]; s = [x for x in w.get('sentences', []) if not x.get('isTitle')]
  out.append(f"{k} | {w.get('title')} | {len(s)} sents | updated {w.get('updated')} | by {w.get('addedByName')} | first: {(s[0].get('en') if s else '')[:70]}")
open('diag/qa_result.txt', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
