/* 입트영 앱 서비스워커
   화면 파일(앱 화면·코드·아이콘·사진): 휴대폰에 받아 둔 것을 바로 보여 주고, 새 버전은 뒤에서 받아 다음에 열 때 적용
   자료(주차 목록·음성 목록): 늘 인터넷의 최신을 먼저 받고, 연결이 안 될 때만 받아 둔 것 사용. 음성(mp3)은 저장하지 않음
   v4: 자료를 '주소?t=시각'마다 따로 쌓던 문제를 고침 → 같은 파일은 한 칸에만 저장 (쌓인 칸이 수천 개라 열 때 5초씩 걸렸음) */
const C='ipt-v4';
const ROOT=new URL('./',self.registration.scope).href;
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(
  caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
const isShell=(r,u)=>r.mode==='navigate'||/\.(html|js|css|png|jpe?g|webp|gif|svg|webmanifest|woff2?)$/.test(u.pathname)||u.pathname.endsWith('/');
/* 코드(app.js?v=번호)는 번호까지 한 칸 — 새 버전이면 새로 받음. 같은 파일의 예전 번호 칸은 지움 */
const keyOf=(r,u)=>r.mode==='navigate'?ROOT:(/\.js$/.test(u.pathname)&&u.searchParams.has('v')?u.origin+u.pathname+'?v='+u.searchParams.get('v'):u.origin+u.pathname);
async function put(key,res){const c=await caches.open(C);await c.put(key,res);
  if(key.includes('?v=')){const base=key.split('?')[0];for(const k of await c.keys())if(k.url!==key&&k.url.split('?')[0]===base)c.delete(k)}}
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;   // 서버(Apps Script) 요청은 건드리지 않음
  if(/\.(mp3|mp4)$/.test(u.pathname))return;                 // 음성·영상은 브라우저에 맡김
  if(u.searchParams.has('fresh'))return;                     // 새 버전 받기 요청은 그대로 인터넷으로
  const key=keyOf(r,u);
  if(isShell(r,u)){
    const hit=caches.match(key);
    e.respondWith(hit.then(h=>h||fetch(r.mode==='navigate'?ROOT:r.url).then(res=>{if(res.ok)put(key,res.clone());return res}).catch(()=>caches.match(ROOT))));
    /* 저장된 게 있으면 뒤에서 조용히 새로 받아 둠 (번호 붙은 코드·사진은 한 번 받으면 그대로) */
    if(!key.includes('?v=')&&!/\.(png|jpe?g|webp|gif|woff2?)$/.test(u.pathname))e.waitUntil(hit.then(h=>h&&fetch(ROOT===key?ROOT:r.url,{cache:'no-cache'}).then(res=>res.ok&&put(key,res))).catch(()=>{}));
    return;
  }
  e.respondWith(fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(C).then(c=>c.put(key,cp))}return res})
    .catch(()=>caches.match(key)));
});
