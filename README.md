
# 감성 일기 생성기

카카오톡 대화 로그를 분석하여 감정 분석과 요약을 포함한 "감성 일기"를 자동으로 생성하는 FastAPI 기반의 웹 애플리케이션입니다. 사용자는 카카오톡 대화 텍스트를 업로드하거나 붙여넣기하고, 필요하면 사용자 프롬프트를 함께 제공하여 더 맞춤화된 일기를 생성할 수 있습니다.


## 주요 기능
- 카카오톡 대화 텍스트 파싱 및 날짜별 분류
- 대화 요약 및 감정 분석 기반의 "감성 일기" 생성
- 사용자 프롬프트와 실제 대화 내용 간 충돌 감지 및 가이드 제공
- 간단한 회원가입/로그인/세션 처리(인메모리)
- 템플릿 기반의 웹 UI 및 정적 리소스 제공
- API 상태 확인 및 테스트용 엔드포인트 제공


## 기술 스택
- 백엔드: FastAPI, Uvicorn, Pydantic, ORJSON
- 템플릿/정적: Jinja2 (`templates/`), Vanilla JS/CSS (`static/`)
- AI: OpenAI API (환경 변수 `OPENAI_API_KEY` 필요)
- 기타: python-dotenv, python-multipart, aiofiles


## 폴더 구조
```
Py_fineTuning/
├─ main.py                 # FastAPI 앱(핵심 로직, 라우팅, 실행 진입점)
├─ run_web.py              # 개발 편의용 실행 스크립트 (reload)
├─ emotion_diary_app_test.py
├─ requirements.txt
├─ templates/              # Jinja2 템플릿 (index, diary, login, register, profile 등)
├─ static/                 # 정적 리소스 (script.js, style.css)
├─ finetune_dataset/       # (데이터셋 관련 폴더, 사용 시 참고)
├─ .env                    # 환경 변수 파일(루트 경로, 예: OPENAI_API_KEY)
├─ Dockerfile, docker-compose*.yml, nginx.conf
├─ RENDER_DEPLOYMENT.md, RAILWAY_DEPLOYMENT.md, CLOUD_DEPLOYMENT.md, README_WEB.md
└─ ... (개발용/가상환경/설정 폴더 등)
```
> 문서화에서는 `venv/`, `test_venv/`, `.git/` 등 개발/환경 폴더는 보통 제외합니다.


## 빠른 시작
1) 의존성 설치
```powershell
python -m venv .venv
. .venv/Scripts/Activate.ps1   # PowerShell
pip install -r requirements.txt
```

2) 환경 변수 설정 (`.env` 파일, 프로젝트 루트)
```env
OPENAI_API_KEY=sk-...
```

3) 로컬 실행 (개발 모드)
```bash
python run_web.py
```
- 웹: http://localhost:8000
- 문서: http://localhost:8000/docs

4) (대안) 직접 실행
```bash
python main.py
```
- 환경 변수 `PORT`가 지정되어 있으면 해당 포트로 실행됩니다.(기본 8000)


## 환경 변수
- `OPENAI_API_KEY`: OpenAI API 키 (필수). `main.py` 에서 `load_dotenv()`로 루트의 `.env` 를 로드합니다.


## 사용 방법 (웹 UI)
1) 브라우저에서 `http://localhost:8000` 접속
2) 카카오톡 대화 텍스트를 업로드/붙여넣기
3) 선택적으로 사용자 프롬프트 입력, "프롬프트 사용" 여부 설정
4) 생성 버튼 클릭 → 감정 분석과 요약이 포함된 일기 출력
5) 로그인/회원가입을 통해 세션 기반 기능(간단) 사용 가능


## 주요 엔드포인트 (요약)
- `GET /` 홈 페이지 (`templates/index.html`)
- `POST /generate-diary` 감성 일기 생성
- `POST /auto-diary` 프롬프트 처리 로직 포함 자동 일기 생성
- `GET /api/status` 서버 상태 확인 (웹)
- `GET /api/flutter/status` Flutter 용 상태 확인
- `GET /login`, `POST /login` 로그인 / `GET /logout` 로그아웃
- `GET /register`, `POST /register` 회원가입
- `GET /profile` 마이페이지

자세한 요청/응답 스키마는 `main.py` 의 Pydantic 모델과 FastAPI 라우트 핸들러를 참고하세요.

- 요청 모델 예시 (`DiaryRequest`):
  - `kakao_text: str`
  - `search_log: str | None = "없음"`
  - `user_prompt: str | None = None`
  - `use_prompt: bool = True`


## 내부 동작 개요
- 카카오톡 파싱/분석
  - `extract_today_chat(text, _)`: 유효한 대화만 필터링
  - `extract_chat_by_date(text, target_date=None)`: 월/일 기준으로 대화 묶기
  - `get_chat_for_date(chat_by_date, target_date)`: 특정 날짜 대화 문자열 반환
  - `analyze_events_by_date(chat_by_date)`: 날짜별 이벤트/패턴 분석
- 일기 생성 로직
  - `generate_diary_with_prompt_handling(data)`: 프롬프트 사용 여부와 사용자 프롬프트를 반영하여 감성 일기 생성
  - `detect_prompt_conflict(user_prompt, kakao_text)`: 프롬프트와 실제 대화 내용 충돌 감지 및 제안 제공
- 사용자/세션 (간단 구현)
  - `User` 모델, 인메모리 `users_db`, `sessions_db`
  - `hash_password()`, `create_session()`, `get_user_from_session()`, `get_current_user()`


## 주의사항 및 한계
- 현재 사용자/세션은 인메모리 구현입니다. 프로덕션에서는 데이터베이스 연동이 필요합니다.
- OpenAI API 키는 절대 코드에 하드코딩하지 말고 `.env` 를 사용하세요.
- 로그/모니터링/테스트 코드는 필요에 따라 보강이 필요할 수 있습니다.
