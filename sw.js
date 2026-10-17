/* 입트영 앱 서비스워커: 설치형 앱으로 쓰기 위한 최소 구성.
   항상 인터넷의 최신 화면을 먼저 쓰고, 연결이 안 될 때만 마지막으로 받아 둔 화면을 보여 줌 (예전 화면이 남는 문제 방지) */
const C='ipt-v1';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin)return;   // 서버(Apps Script) 요청은 건드리지 않음
  e.respondWith(fetch(r).then(res=>{if(res.ok&&!/\.mp3$/.test(u.pathname)){const cp=res.clone();caches.open(C).then(c=>c.put(r,cp))}return res})
    .catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match('./'))));
});
