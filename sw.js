/* 입트영 앱 서비스워커
   화면 파일(앱 화면·아이콘 등): 휴대폰에 받아 둔 것을 바로 보여 주고, 새 버전은 뒤에서 받아 다음에 열 때 적용
   → 다른 앱에 갔다 와서 페이지가 다시 열려도 설치 앱처럼 즉시 뜸.
   자료(주차 목록·음성 목록): 늘 인터넷의 최신을 먼저 받고, 연결이 안 될 때만 받아 둔 것 사용. 음성(mp3)은 저장하지 않음 */
const C='ipt-v3';
const ROOT=new URL('./',self.registration.scope).href;
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(
  caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
const isShell=(r,u)=>r.mode==='navigate'||/\.(html|js|css|png|svg|webmanifest|woff2?)$/.test(u.pathname)||u.pathname.endsWith('/');
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;   // 서버(Apps Script) 요청은 건드리지 않음
  if(/\.mp3$/.test(u.pathname))return;                       // 음성은 브라우저에 맡김
  if(u.searchParams.has('fresh'))return;                     // 새 버전 받기 요청은 그대로 인터넷으로
  if(isShell(r,u)){
    const key=r.mode==='navigate'?ROOT:r.url.split('?')[0];
    const net=fetch(r.mode==='navigate'?ROOT:r.url,{cache:'no-cache'})
      .then(res=>{if(res.ok){const cp=res.clone();return caches.open(C).then(c=>c.put(key,cp)).then(()=>res)}return res});
    e.waitUntil(net.catch(()=>{}));
    e.respondWith(caches.match(key,{ignoreSearch:true}).then(hit=>hit||net.catch(()=>caches.match(ROOT))));
    return;
  }
  e.respondWith(fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(C).then(c=>c.put(r,cp))}return res})
    .catch(()=>caches.match(r,{ignoreSearch:true})));
});
