/**
 * 줌 수업 복습 (/zoom 앱) — 입트영 Apps Script 프로젝트에 '파일 추가'로 넣는 파일
 *
 * 하는 일: 앱에서 올린 줌 녹화를 구글 드라이브 '줌 수업 복습' 폴더에 잠시 보관 → GitHub Actions가 가져가 정리
 *          복습 진도 저장 (휴대폰·PC 어디서 열어도 같은 진도)
 * 비밀번호: 입트영 관리자 비밀번호(ADMIN_PASSWORD)를 그대로 씀. 따로 쓰고 싶으면 스크립트 속성에 ZOOM_KEY를 넣으세요.
 * Code.gs의 doPost가 'zoom_'으로 시작하는 요청을 이 파일로 넘겨 줍니다. 별도 설정·배포 주소 없음.
 */
const ZOOM_FNS = ['zoom_check', 'zoom_uploadPart', 'zoom_finishUpload', 'zoom_jobs', 'zoom_pendingJobs', 'zoom_getPart',
  'zoom_setJob', 'zoom_deleteJob', 'zoom_getProgress', 'zoom_saveProgress'];

function zoomCall_(fn, args) {
  if (ZOOM_FNS.indexOf(fn) < 0) return { err: 'unknown_fn' };
  args = args || [];
  const key = PROPS.getProperty('ZOOM_KEY') || PROPS.getProperty('ADMIN_PASSWORD');
  if (!key || String(args[0] || '') !== String(key)) return { err: 'wrong_key' };
  try { return { res: this[fn].apply(null, args.slice(1)) }; }
  catch (e) { return { err: String(e && e.message || e) }; }
}

function zoom_check() { return true; }

/* 녹화를 4MB씩 나눠 받음 (한 번에 받을 수 있는 크기 제한 때문) */
function zoom_uploadPart(id, i, b64) {
  const f = sub_(zf_('uploads'), safe_(id)), name = zpart_(i);
  const it = f.getFilesByName(name); while (it.hasNext()) it.next().setTrashed(true);
  f.createFile(name, b64, 'text/plain');
  return i;
}
function zoom_finishUpload(id, date, name, parts, size) {
  zlock_(() => {
    const J = zjobs_();
    J[id] = { id: id, date: date, name: name, parts: parts, size: size, status: 'waiting', created: new Date().toISOString() };
    zsave_('jobs.json', J);
  });
  zkick_();
  return true;
}
function zoom_jobs() {
  const J = zjobs_();
  return Object.keys(J).map(k => J[k]).sort((a, b) => b.created.localeCompare(a.created)).slice(0, 10);
}
function zoom_deleteJob(id) { zlock_(() => { const J = zjobs_(); delete J[id]; zsave_('jobs.json', J); }); zclear_(id); return true; }

/* GitHub Actions가 부르는 함수 */
function zoom_pendingJobs() {
  const J = zjobs_(), now = Date.now();
  return Object.keys(J).map(k => J[k]).filter(j =>
    j.status === 'waiting' || (j.status === 'processing' && now - new Date(j.started || j.created).getTime() > 2 * 3600 * 1000)
  ).sort((a, b) => a.created.localeCompare(b.created));
}
function zoom_getPart(id, i) {
  const it = sub_(zf_('uploads'), safe_(id)).getFilesByName(zpart_(i));
  if (!it.hasNext()) throw new Error('part_missing ' + i);
  return it.next().getBlob().getDataAsString();
}
function zoom_setJob(id, patch) {
  zlock_(() => {
    const J = zjobs_(); if (!J[id]) return;
    Object.keys(patch || {}).forEach(k => J[id][k] = patch[k]);
    if (patch.status === 'processing') J[id].started = new Date().toISOString();
    if (patch.status === 'done') J[id].finished = new Date().toISOString();
    zsave_('jobs.json', J);
  });
  if (patch && patch.status === 'done') zclear_(id);
  return true;
}

/* 진도: { '2026-10-23:Lt1': 'ok', ... } */
function zoom_getProgress() { return readJson_(zf_(), 'progress.json') || {}; }
function zoom_saveProgress(p) {
  zlock_(() => {
    const cur = readJson_(zf_(), 'progress.json') || {};
    Object.keys(p || {}).forEach(k => { if (p[k] === null) delete cur[k]; else cur[k] = p[k]; });
    zsave_('progress.json', cur);
  });
  return true;
}

/* ---------- 내부 도우미 (Code.gs의 sub_·safe_·readJson_·writeJson_ 함께 사용) ---------- */
function zf_(child) {
  let root = null; const id = PROPS.getProperty('ZOOM_ROOT_ID');
  if (id) { try { root = DriveApp.getFolderById(id); } catch (e) { root = null; } }
  if (!root) {
    const it = DriveApp.getFoldersByName('줌 수업 복습');
    root = it.hasNext() ? it.next() : DriveApp.createFolder('줌 수업 복습');
    PROPS.setProperty('ZOOM_ROOT_ID', root.getId());
  }
  return child ? sub_(root, child) : root;
}
function zpart_(i) { return 'part-' + ('000' + i).slice(-4) + '.txt'; }
function zjobs_() { return readJson_(zf_(), 'jobs.json') || {}; }
function zsave_(name, obj) { writeJson_(zf_(), name, obj); }
function zclear_(id) { const it = zf_('uploads').getFoldersByName(safe_(id)); while (it.hasNext()) it.next().setTrashed(true); }
function zlock_(fn) { const l = LockService.getScriptLock(); l.waitLock(20000); try { fn(); } finally { l.releaseLock(); } }
function zkick_() {
  const tok = PROPS.getProperty('GITHUB_TOKEN'), repo = PROPS.getProperty('GITHUB_REPO');
  if (!tok || !repo) return;
  try {
    UrlFetchApp.fetch('https://api.github.com/repos/' + repo + '/dispatches', {
      method: 'post', contentType: 'application/json', muteHttpExceptions: true,
      headers: { Authorization: 'Bearer ' + tok, Accept: 'application/vnd.github+json' },
      payload: JSON.stringify({ event_type: 'zoom' })
    });
  } catch (e) {}
}
