# 입트영 주간 암기

매주 토요일 스터디 지문을 문장별 원어민 음성으로 듣고, 써 보고, 단어·숙어를 AI에게 바로 물어보며 외우는 학습장입니다.

- **화면**: GitHub Pages (이 저장소) → `https://junkim10293847.github.io/ipteuyoung/`
- **저장·AI**: Google Apps Script (지문 공유, 닉네임별 진도, Gemini 무료 AI)
- **음성**: GitHub Actions가 15분마다 새 주차를 확인해 무료 오픈소스 음성(Kokoro)으로 자동 생성

## 처음 설정 (한 번만)

1. `apps-script/Code.gs`를 Apps Script 프로젝트에 붙여 넣고, `Seed` HTML 파일을 추가합니다.
2. 스크립트 속성에 `GEMINI_API_KEY`(Google AI Studio 무료 키)를 넣습니다.
3. `setup` 함수를 실행한 뒤 **웹 앱**으로 배포합니다. (실행: 나 / 액세스: 모든 사용자)
4. 이 저장소의 `config.js`에 웹 앱 URL(…/exec)을 붙여 넣습니다.
5. **Settings → Pages → Branch: main, / (root) → Save**를 누릅니다.

## 매주 할 일

화면에서 **+ 새 주차**를 누르고 지문을 붙여 넣으면 끝입니다. 해석·단어는 바로 정리되고, 원어민 음성은 15~20분 안에 붙습니다.
음성을 더 빨리 만들고 싶으면 **Actions → 음성 자동 생성 → Run workflow**를 누르세요.

## 참고

- 저장소에 60일 동안 변화가 없으면 GitHub가 15분 자동 확인을 멈춥니다. 그때는 Actions 탭에서 다시 켜면 됩니다.
- 지문과 진도는 이 저장소가 아니라 관리자의 구글 드라이브(`입트영 주간 암기` 폴더)에 저장됩니다.
