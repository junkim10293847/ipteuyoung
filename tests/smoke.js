/* 배포 전 자동 점검 (스모크 테스트)
   - 실제 서버 대신 가짜 응답(data/weeks.json + 정해진 AI 답)을 써서, 휴대폰 크기 화면으로 주요 기능을 눌러 봄
   - 하나라도 실패하면 종료 코드 1 → 사이트(main)에 올리지 않음
   실행: node tests/smoke.js [포트]   (저장소 폴더에서 정적 서버를 띄운 상태) */
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const ROOT=path.join(__dirname,'..');const PORT=process.argv[2]||8765;
const weeks=JSON.parse(fs.readFileSync(path.join(ROOT,'data/weeks.json'),'utf8'));
const results=[];let failed=0;
const ok=(name,cond,info='')=>{results.push(`${cond?'✅':'❌'} ${name}${info?' — '+info:''}`);if(!cond)failed++};

(async()=>{
  const b=await chromium.launch();
  const ctx=await b.newContext({viewport:{width:412,height:860},hasTouch:true,isMobile:true});
  const pg=await ctx.newPage();
  const errs=[];pg.on('pageerror',e=>errs.push(e.message));
  let aiCalls=0;
  await pg.route(/fonts\.(googleapis|gstatic)\.com/,r=>r.fulfill({status:200,body:''}));
  await pg.route(/\.mp3(\?|$)/,r=>r.fulfill({status:404,body:''}));
  await pg.route(/script\.google/,async r=>{let body={};try{body=JSON.parse(r.request().postData()||'{}')}catch(_){}
    const fn=body.fn,p=String((body.args||[])[0]||'');let res=true;
    if(fn==='getWeeks')res=weeks;else if(fn==='features')res={ai:true,tts:true};else if(fn==='getProgress')res={exists:false};
    else if(fn==='aiText'){aiCalls++;res='첫 줄 핵심 답입니다.\nI decided to go. (나는 가기로 했다.)\nShe started running. (그녀는 달리기 시작했다.)\n확인 퀴즈: \'나는 쉬기로 했어요\'를 영어로 말해 보세요.'}
    else if(fn==='aiJson'){aiCalls++;
      if(/"ok"/.test(p)&&/학습자/.test(p))res={ok:true,fixed:'Checked sentence.',better:'',tip:'좋아요'};
      else if(/난이도별로 3개/.test(p))res={};   /* 일부러 실패: AI가 실패해도 화면이 무한 반복에 빠지지 않는지 확인 */
      else res={items:[]}}
    r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({res})})});

  await pg.goto(`http://localhost:${PORT}/index.html`);await pg.waitForTimeout(2500);
  if(await pg.isVisible('#gate')){await pg.fill('#gate input','홍길동');await pg.press('#gate input','Enter');await pg.waitForTimeout(1500)}
  const ev=(f,a)=>pg.evaluate(f,a);

  // 1. 첫 화면
  const n=await ev(()=>{const w=weeks.find(w=>w.sentences.length>5&&w.prog!=='gtv');curId=w.id;view='all';full();return document.querySelectorAll('li.card').length});
  ok('첫 화면에 문장 카드가 나옴',n>3,`${n}장`);
  ok('1번 카드 제목과 첫 문장이 한 칸',await ev(()=>{const t=document.querySelector('li.card .ttl');return !t||!!t.closest('.enw')}));

  // 2. 써보기 → 채점: 결과가 나오고 쓰기 칸이 제자리
  await ev(()=>document.querySelector('#c3 .write').click());await pg.waitForTimeout(200);
  await ev(()=>{const e=$('wr-3');scrollTo(0,e.getBoundingClientRect().top+scrollY-300)});
  const tap=async sel=>{const r=await pg.$eval(sel,e=>{const b=e.getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2}});await pg.touchscreen.tap(r.x,r.y)};
  await tap('#wr-3');await pg.setViewportSize({width:412,height:520});await pg.waitForTimeout(500);
  await pg.keyboard.type('I am a test.');
  const y0=await ev(()=>Math.round($('wr-3').getBoundingClientRect().top));
  await tap('#c3 .wr-check');await pg.waitForTimeout(150);await pg.setViewportSize({width:412,height:860});await pg.waitForTimeout(1400);
  const y1=await ev(()=>Math.round($('wr-3').getBoundingClientRect().top));
  ok('채점 결과가 나옴',!!await pg.$('#c3 .wr-res'));
  ok('채점해도 쓰기 칸이 제자리',Math.abs(y1-y0)<=3,`${y0}→${y1}`);

  // 3. 숙어 자세히 + 확인 퀴즈 첨삭 (입력칸이 계속 다시 그려지지 않아야 함)
  const loc=await ev(()=>{for(let i=0;i<weeks.find(x=>x.id===curId).sentences.length;i++){const s=weeks.find(x=>x.id===curId).sentences[i];if(s.isTitle||!document.getElementById('c'+i))continue;for(let j=0;j<(s.vocab||[]).length;j++){const v=s.vocab[j];if(v.detail&&v.detail.core){if(!v.detail.quiz){v.detail.quiz="'시험'을 영어로 말해 보세요.";v.detail.quizAns='Test.'}openVoc.add(i);openDet.add(i+'-'+j);renderCard(i);return i}}}return -1});
  if(loc>=0){await pg.waitForTimeout(800);
    const sel=`#c${loc} .d-quiz`;await ev(s=>{const e=document.querySelector(s);if(e)e.scrollIntoView({block:'center'})},sel);
    let filled=true;try{await pg.fill(sel+' .qz-in','I test it.',{timeout:5000})}catch(e){filled=false}
    ok('확인 퀴즈 입력칸이 안정적(계속 다시 그려지지 않음)',filled);
    if(filled){await tap(sel+' .dq-go');await pg.waitForTimeout(1500);ok('확인 퀴즈 첨삭 결과가 나옴',await ev(s=>/맞았어요|고쳐 보세요/.test(document.querySelector(s).innerText),sel))}
  }else ok('설명이 있는 숙어 찾기',false,'data/weeks.json에 설명 없음');

  // 4. 질문하기
  const qk=await ev(()=>{const f=document.querySelector('.qa-form');return f?f.dataset.k:null});
  if(qk){await ev(k=>{const i=document.getElementById('qaIn-'+k);i.value='decide 다음 to?';i.dispatchEvent(new Event('input',{bubbles:true}))},qk);
    await ev(k=>{const f=document.querySelector(`.qa-form[data-k="${k}"]`);f.requestSubmit?f.requestSubmit():f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))},qk);
    await pg.waitForTimeout(1500);ok('질문하면 답이 나옴',await ev(()=>/첫 줄 핵심 답/.test(document.body.innerText)))}

  // 5. 연습 도구 열고 닫기
  for(const id of ['psBox','dqaBox','gsBox','mockBox','weakBox']){const has=await pg.$('#'+id);if(!has)continue;
    await ev(id=>{const d=$(id);d.open=true},id);await pg.waitForTimeout(250);await ev(id=>{const d=$(id);d.open=false},id)}
  ok('연습 도구 열고 닫기 중 오류 없음',!errs.length,errs.slice(0,2).join(' / '));

  // 6. 귀트영 전환
  const g=await ev(()=>{const b=document.querySelector('#progSw [data-prog="gtv"]');if(!b)return 'none';b.click();return curProg});
  await pg.waitForTimeout(400);ok('귀트영으로 전환',g==='gtv'||g==='none',g);
  await ev(()=>{const b=document.querySelector('#progSw [data-prog="ipt"]');if(b)b.click()});await pg.waitForTimeout(400);

  // 7. 가만히 둘 때 AI 요청이 끝없이 나가지 않음
  const a0=aiCalls;await pg.waitForTimeout(12000);const da=aiCalls-a0;
  ok('가만히 있을 때 AI 요청이 반복되지 않음',da<=12,`12초 동안 ${da}번`);
  ok('화면 오류(자바스크립트) 없음',!errs.length,errs.slice(0,3).join(' / '));

  await b.close();
  const out=results.join('\n');console.log(out);
  fs.mkdirSync(path.join(ROOT,'diag'),{recursive:true});
  fs.writeFileSync(path.join(ROOT,'diag','smoke_result.txt'),`${new Date().toISOString()}\n${failed?'실패 '+failed+'개':'모두 통과'}\n${out}\n`);
  process.exit(failed?1:0);
})().catch(e=>{console.error('점검 중단:',e.message);process.exit(1)});
