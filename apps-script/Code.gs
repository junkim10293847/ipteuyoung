/**
 * 입트영 주간 암기 — Apps Script 서버 (GitHub Pages 화면용 API)
 *
 * 하는 일: 주차 지문 저장·공유, 닉네임별 진도 저장, Gemini 무료 AI(해석 정리·자세히·바로 질문)
 * 음성은 GitHub Actions가 무료로 만들어 GitHub 저장소에 올립니다.
 *
 * 처음 한 번: 위쪽 함수 목록에서 'setup' 선택 → 실행 → 권한 허용
 * 그다음: 배포 → 새 배포 → 유형 '웹 앱' / 실행 사용자: 나 / 액세스 권한: 모든 사용자 → 배포
 *         → 나온 웹 앱 URL(…/exec)을 GitHub 저장소 config.js에 붙여 넣기
 *
 * 스크립트 속성(프로젝트 설정 → 스크립트 속성)
 *   GEMINI_API_KEY   (필수, 무료) Google AI Studio 키 → 해석 자동 정리·자세히·바로 질문
 *   ADMIN_PASSWORD   관리자 비밀번호 (setup이 자동으로 만들고 실행 로그에 보여 줌)
 *   GITHUB_TOKEN     (선택) 넣으면 새 주차 저장 즉시 음성 생성 시작 (없으면 15분 안에 자동 시작)
 *   GITHUB_REPO      (선택) GITHUB_TOKEN과 함께: 아이디/저장소 (예: hong/ipteuyoung)
 *   GEMINI_MODEL     (선택) 먼저 쓸 모델 (예: gemini-2.5-flash). 혼잡하면 자동으로 다른 무료 모델로 넘어감
 *   AI_DAILY_LIMIT   (선택) 하루 AI 호출 상한, 기본 300
 */

const PROPS = PropertiesService.getScriptProperties();
const ROOT_NAME = '입트영 주간 암기';
const API_FNS = ['getWeeks', 'saveWeek', 'deleteWeek', 'checkAdmin', 'getProgress', 'saveProgress', 'aiText', 'aiJson', 'aiEnabled', 'features', 'members'];

/* ---------- API ---------- */
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function call_(fn, args) {
  if (API_FNS.indexOf(fn) < 0) return { err: 'unknown_fn' };
  try { return { res: this[fn].apply(null, args || []) }; }
  catch (e) { return { err: String(e && e.message || e) }; }
}
/* 브라우저: POST {fn, args} (Content-Type text/plain) */
function doPost(e) {
  let b = {};
  try { b = JSON.parse(e.postData.contents || '{}'); } catch (x) { return json_({ err: 'bad_request' }); }
  if (/^zoom_/.test(String(b.fn))) return json_(zoomCall_(b.fn, b.args));   // 줌 수업 복습 앱 (Zoom.gs)
  return json_(call_(b.fn, b.args));
}
/* GitHub Actions·확인용: GET …/exec?fn=getWeeks */
function doGet(e) {
  const fn = e && e.parameter && e.parameter.fn;
  if (fn === 'getWeeks' || fn === 'features') return json_(call_(fn, []));
  return json_({ ok: true, app: '입트영 주간 암기 API', ai: aiEnabled() });
}

/* ---------- 최초 설정 ---------- */
function setup() {
  let root;
  const rid = PROPS.getProperty('ROOT_ID');
  if (rid) { try { root = DriveApp.getFolderById(rid); } catch (e) { root = null; } }
  if (!root) { const it = DriveApp.getFoldersByName(ROOT_NAME); root = it.hasNext() ? it.next() : DriveApp.createFolder(ROOT_NAME); }
  const data = sub_(root, 'data'), prog = sub_(data, 'progress');
  PROPS.setProperties({ ROOT_ID: root.getId(), DATA_ID: data.getId(), PROG_ID: prog.getId() });
  if (!PROPS.getProperty('ADMIN_PASSWORD')) PROPS.setProperty('ADMIN_PASSWORD', 'change-me-' + Math.floor(Math.random() * 9000 + 1000));

  // 처음 데이터 넣기 (Seed.html): 기존 주차·진도
  let seed = {};
  try { seed = JSON.parse(HtmlService.createHtmlOutputFromFile('Seed').getContent()); } catch (e) { Logger.log('Seed 없음(괜찮음): ' + e); }
  // 새 Seed(버전이 다름)면 Seed 내용으로 덮어쓰고, 같은 Seed를 다시 실행하면 없는 것만 채움
  const fresh = seed.v && PROPS.getProperty('SEED_V') !== seed.v;
  const cur = readJson_(data, 'weeks.json') || {};
  let nw = 0, np = 0;
  Object.keys(seed.weeks || {}).forEach(id => { if (fresh || !cur[id]) { cur[id] = seed.weeks[id]; nw++; } });
  writeJson_(data, 'weeks.json', cur);
  Object.keys(seed.progress || {}).forEach(k => { if (fresh || !readJson_(prog, safe_(k) + '.json')) { writeJson_(prog, safe_(k) + '.json', seed.progress[k]); np++; } });
  if (seed.v) PROPS.setProperty('SEED_V', seed.v);

  // 예전 버전이 만든 시간 트리거 정리
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === 'audioJob') ScriptApp.deleteTrigger(t); });

  Logger.log('설정 완료. 주차 %s개, 진도 %s개 추가. 폴더: %s', nw, np, root.getUrl());
  Logger.log('관리자 비밀번호: %s  (프로젝트 설정 → 스크립트 속성에서 바꿀 수 있습니다)', PROPS.getProperty('ADMIN_PASSWORD'));
  Logger.log(PROPS.getProperty('GEMINI_API_KEY') ? 'Gemini 키 확인됨: AI 기능 켜짐' : '아직 GEMINI_API_KEY가 없습니다. 스크립트 속성에 넣어 주세요.');
}

/* Gemini 키가 잘 되는지 확인: 함수 목록에서 testAI 선택 → 실행 → 로그 확인 */
function testAI() { Logger.log(aiText('Say hello in one short English sentence.')); }

/* ---------- 화면이 부르는 함수 ---------- */
function getWeeks() { return readWeeks_(folder_('DATA_ID')); }

/* 주차 파일 읽기: 드라이브가 잠깐 응답을 못 해도 '빈 목록'으로 착각하지 않도록 다시 시도하고, 그래도 안 되면 최근 백업을 씀 */
function readWeeks_(f) {
  for (let t = 0; t < 3; t++) {
    try {
      const it = f.getFilesByName('weeks.json');
      if (it.hasNext()) { const s = it.next().getBlob().getDataAsString('UTF-8'); if (s && s.trim()) return JSON.parse(s); }
    } catch (e) {}
    Utilities.sleep(400 * (t + 1));
  }
  const b = latestBackup_(f); if (b) return b;
  throw new Error('read_failed');
}
function latestBackup_(f) {
  const list = [], it = f.getFiles();
  while (it.hasNext()) { const x = it.next(); if (/^weeks-bak-/.test(x.getName())) list.push(x); }
  list.sort((a, b) => b.getName() < a.getName() ? -1 : 1);
  for (const x of list) { try { return JSON.parse(x.getBlob().getDataAsString('UTF-8')); } catch (e) {} }
  return null;
}
/* 저장할 때마다 바로 전 상태를 백업으로 남김 (최근 15개 보관) */
function writeWeeks_(f, all) {
  try {
    const it = f.getFilesByName('weeks.json');
    if (it.hasNext()) {
      const prev = it.next().getBlob().getDataAsString('UTF-8');
      if (prev && prev.length > 2) f.createFile('weeks-bak-' + Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyyMMdd-HHmmss') + '.json', prev, 'application/json');
    }
    const list = [], it2 = f.getFiles();
    while (it2.hasNext()) { const x = it2.next(); if (/^weeks-bak-/.test(x.getName())) list.push(x); }
    list.sort((a, b) => b.getName() < a.getName() ? -1 : 1).slice(15).forEach(x => x.setTrashed(true));
  } catch (e) {}
  writeJson_(f, 'weeks.json', all);
}

function saveWeek(id, data, merge) {
  id = String(id || '').replace(/[^0-9-]/g, '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(id)) throw new Error('bad_id');
  if (!data || typeof data !== 'object') throw new Error('bad_data');
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    const f = folder_('DATA_ID'), all = readWeeks_(f);
    if (merge && !all[id]) throw new Error('not_found');
    all[id] = merge ? Object.assign({}, all[id], data) : data;
    writeWeeks_(f, all);
  } finally { lock.releaseLock(); }
  if (!merge || data.sentences) kickAudio_();
  return true;
}

function deleteWeek(id, pw) {
  if (!checkAdmin(pw)) throw new Error('not_admin');
  const lock = LockService.getScriptLock(); lock.waitLock(20000);
  try { const f = folder_('DATA_ID'), all = readWeeks_(f); delete all[id]; writeWeeks_(f, all); return true; }
  finally { lock.releaseLock(); }
}

function checkAdmin(pw) { const p = PROPS.getProperty('ADMIN_PASSWORD'); return !!p && pw === p; }

/* 관리자용: 닉네임별 진도 파일 목록 (이름·마지막 활동·외운 문장 수) */
function members(pw) {
  if (!checkAdmin(pw)) throw new Error('not_admin');
  const out = [], it = folder_('PROG_ID').getFiles();
  while (it.hasNext()) {
    const f = it.next(); if (!/\.json$/.test(f.getName())) continue;
    let d = {}; try { d = JSON.parse(f.getBlob().getDataAsString('UTF-8')); } catch (e) {}
    const done = {}; Object.keys(d.done || {}).forEach(w => { done[w] = Object.keys(d.done[w] || {}).filter(k => d.done[w][k]).length; });
    let writes = 0; Object.keys(d.weak || {}).forEach(w => Object.keys(d.weak[w] || {}).forEach(i => { writes += (d.weak[w][i] || {}).n || 0; }));
    out.push({ nick: d.nick || '', updated: d.updated || f.getLastUpdated().getTime(), done: done, writes: writes, tests: Object.keys(d.tests || {}).reduce((a, w) => a + (d.tests[w] || []).length, 0) });
  }
  return out.sort((a, b) => b.updated - a.updated);
}

function getProgress(key) { const d = readJson_(folder_('PROG_ID'), safe_(key) + '.json'); return d ? { exists: true, data: d } : { exists: false }; }
function saveProgress(key, data) {
  if (!data || typeof data !== 'object') throw new Error('bad_data');
  const s = JSON.stringify(data); if (s.length > 400000) throw new Error('too_large');
  writeJson_(folder_('PROG_ID'), safe_(key) + '.json', data); return true;
}

/* (선택) 새 주차 저장 즉시 GitHub Actions 음성 생성 시작 */
function kickAudio_() {
  const tok = PROPS.getProperty('GITHUB_TOKEN'), repo = PROPS.getProperty('GITHUB_REPO');
  if (!tok || !repo) return;
  try {
    UrlFetchApp.fetch('https://api.github.com/repos/' + repo + '/dispatches', {
      method: 'post', contentType: 'application/json', muteHttpExceptions: true,
      headers: { Authorization: 'Bearer ' + tok, Accept: 'application/vnd.github+json' },
      payload: JSON.stringify({ event_type: 'audio' })
    });
  } catch (e) { Logger.log('GitHub 호출 실패: ' + e); }
}

/* ---------- AI: Gemini 무료(GEMINI_API_KEY) 우선, 없으면 Claude(ANTHROPIC_API_KEY) ---------- */
function aiText(prompt) { return callAI_(prompt, false); }
function aiJson(prompt) {
  const t = callAI_(prompt + '\n\n반드시 JSON만 출력하세요. 설명 문장이나 코드펜스 없이.', true);
  try { return JSON.parse(t); } catch (e) {}
  const m = t.match(/```(?:json)?\s*([\s\S]*?)```/); if (m) { try { return JSON.parse(m[1]); } catch (e) {} }
  const a = t.search(/[\[{]/), b = Math.max(t.lastIndexOf('}'), t.lastIndexOf(']'));
  if (a >= 0 && b > a) { try { return JSON.parse(t.slice(a, b + 1)); } catch (e) {} }
  throw new Error('invalid_json');
}
function aiEnabled() { return !!(PROPS.getProperty('GEMINI_API_KEY') || PROPS.getProperty('ANTHROPIC_API_KEY')); }
function features() { return { ai: aiEnabled(), tts: true }; }

function callAI_(prompt, json) {
  const cache = CacheService.getScriptCache(), dk = 'ai:' + Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyyMMdd');
  const used = +(cache.get(dk) || 0), limit = +(PROPS.getProperty('AI_DAILY_LIMIT') || 300);
  if (used >= limit) throw new Error('rate_limited');
  cache.put(dk, String(used + 1), 21600 * 4);
  prompt = String(prompt).slice(0, 60000);
  if (PROPS.getProperty('GEMINI_API_KEY')) return gemini_(prompt, json);
  if (PROPS.getProperty('ANTHROPIC_API_KEY')) return claude_(prompt);
  throw new Error('not_granted');
}

/* Gemini 무료: GEMINI_MODEL(쉼표로 여러 개 가능)을 먼저 쓰고, 그 모델이 혼잡·한도 초과·이름 오류면 다음 후보로 자동 전환 */
const GEMINI_CANDIDATES = ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-3.6-flash', 'gemini-3.8-flash', 'gemini-2.5-flash-lite', 'gemini-flash-lite-latest', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite'];
function thinkCfg_(model) {
  if (/pro/i.test(model)) return null;                       // pro 모델은 생각 단계를 끌 수 없음
  if (/^gemini-2\.5/.test(model)) return { thinkingBudget: 0 };
  if (/^gemini-[3-9]/.test(model)) return { thinkingLevel: 'low' };
  return null;
}
function gemini_(prompt, json) {
  const key = PROPS.getProperty('GEMINI_API_KEY');
  const fixed = String(PROPS.getProperty('GEMINI_MODEL') || '').split(',').map(x => x.trim()).filter(Boolean);
  const known = PROPS.getProperty('GEMINI_OK_MODEL');
  const list = fixed.concat([known], GEMINI_CANDIDATES).filter((x, i, a) => x && a.indexOf(x) === i);
  let lastErr = 'upstream_error';
  for (const model of list) {
    let res, code, body, msg;
    /* 빠르게: 답하기 전 '오래 생각하기' 단계를 끄거나 줄임 (설명 40~70초 → 10~20초). 모델이 이 설정을 모르면 설정 없이 다시 요청 */
    for (const think of [thinkCfg_(model), null]) {
      const gc = json ? { responseMimeType: 'application/json' } : {};
      if (think) gc.thinkingConfig = think;
      try {
        res = UrlFetchApp.fetch('https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent?key=' + encodeURIComponent(key), {
          method: 'post', contentType: 'application/json', muteHttpExceptions: true,
          payload: JSON.stringify({ contents: [{ role: 'user', parts: [{ text: prompt }] }], generationConfig: gc })
        });
      } catch (e) { res = null; lastErr = 'upstream_error: ' + e; break; }
      code = res.getResponseCode();
      body = {}; try { body = JSON.parse(res.getContentText() || '{}'); } catch (e) {}
      msg = JSON.stringify(body.error || '');
      if (!(think && code === 400 && /think/i.test(msg))) break;
    }
    if (!res) continue;
    if (code === 404 || (code === 400 && /model/i.test(msg))) { lastErr = 'model_not_found ' + model; continue; }
    if (code === 429) { lastErr = 'rate_limited'; continue; }                         // 이 모델 한도 초과 → 다른 모델
    if (code >= 500 || /high demand|overloaded|UNAVAILABLE/i.test(msg)) { lastErr = 'upstream_error: busy'; continue; } // 혼잡 → 다른 모델
    if (code >= 400) throw new Error('upstream_error: ' + ((body.error && body.error.message) || code));
    const c = (body.candidates || [])[0];
    const text = c && c.content && (c.content.parts || []).map(p => p.text || '').join('');
    if (!text) { lastErr = 'upstream_error: empty'; continue; }
    if (!fixed.length && model !== known) PROPS.setProperty('GEMINI_OK_MODEL', model);
    return text;
  }
  throw new Error(lastErr);
}

function claude_(prompt) {
  const res = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { 'x-api-key': PROPS.getProperty('ANTHROPIC_API_KEY'), 'anthropic-version': '2023-06-01' },
    payload: JSON.stringify({ model: PROPS.getProperty('AI_MODEL') || 'claude-sonnet-5-5', max_tokens: 4096, messages: [{ role: 'user', content: prompt }] })
  });
  const code = res.getResponseCode(), body = JSON.parse(res.getContentText() || '{}');
  if (code === 429) throw new Error('rate_limited');
  if (code >= 400) throw new Error('upstream_error: ' + ((body.error && body.error.message) || code));
  return (body.content || []).filter(c => c.type === 'text').map(c => c.text).join('');
}

/* ---------- 내부 도우미 ---------- */
function folder_(k) { const id = PROPS.getProperty(k); if (!id) throw new Error('setup_needed'); return DriveApp.getFolderById(id); }
function sub_(parent, name) { const it = parent.getFoldersByName(name); return it.hasNext() ? it.next() : parent.createFolder(name); }
function safe_(k) { return String(k || 'x').replace(/[^A-Za-z0-9_\-]/g, '_').slice(0, 80); }
function readJson_(folder, name) { const it = folder.getFilesByName(name); if (!it.hasNext()) return null; try { return JSON.parse(it.next().getBlob().getDataAsString('UTF-8')); } catch (e) { return null; } }
function writeJson_(folder, name, obj) {
  const s = JSON.stringify(obj), it = folder.getFilesByName(name);
  if (it.hasNext()) it.next().setContent(s); else folder.createFile(name, s, 'application/json');
}
