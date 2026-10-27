# 줌 수업 복습

매일 필리핀 강사와 하는 줌 영어 수업 녹화를 올리면, 강사 목소리로 듣기·받아쓰기·말하기·표현 카드를 날짜별로 만들어 주는 복습 앱입니다.

- **화면**: GitHub Pages → `https://junkim10293847.github.io/ipteuyoung/zoom/`
- **녹화 보관·진도 저장**: 입트영 Apps Script 프로젝트 (`Code.gs` 아래쪽) (관리자 구글 드라이브 `줌 수업 복습` 폴더)
- **자동 정리**: GitHub Actions가 15분마다 새 녹화를 확인 → 강사/학습자 목소리 분리 → 영어 받아쓰기 → Gemini로 번역·끊어 읽기·표현 정리

## 처음 설정 (한 번만)

입트영 앱과 같은 Apps Script 프로젝트를 씁니다. 새 프로젝트·새 주소가 필요 없습니다.

1. 입트영 Apps Script 프로젝트를 엽니다.
2. `Code.gs` 내용을 모두 지우고 저장소의 `apps-script/Code.gs` 최신 내용을 통째로 붙여 넣은 뒤 저장합니다. (줌 기능이 맨 아래에 들어 있습니다)
3. **배포 → 배포 관리 → 연필(수정) → 버전: 새 버전 → 배포**. 주소는 그대로입니다.
4. 저장소 **Settings → Secrets and variables → Actions → New repository secret** 에 두 개를 넣습니다.
   - `ZOOM_KEY`: 입트영 관리자 비밀번호
   - `GEMINI_API_KEY`: 입트영 Apps Script에 넣어 둔 것과 같은 Gemini 키

## 매일 할 일

수업이 끝나면 앱에서 **+ 수업 올리기** → 줌 녹화(mp4 또는 m4a) 선택 → 올리기. 20~30분 뒤 목록에 그 날짜로 복습 카드가 생깁니다.
바로 시작하고 싶으면 **Actions → 줌 수업 자동 정리 → Run workflow** 를 누르세요.

## 참고

- 수업 녹화의 음성(32kbps)과 정리된 문장은 저장소(공개)에 올라갑니다. 원본 녹화는 정리가 끝나면 드라이브에서 지워집니다.
- 저장소에 60일 동안 변화가 없으면 GitHub가 15분 자동 확인을 멈춥니다. 그때는 Actions 탭에서 다시 켜면 됩니다.
- 시험 실행: `python scripts/process.py --file 녹화.mp4 --date 2026-10-27` (음성 도구가 `.sherpa` 폴더에 있어야 함)
