# 📔 감성 일기 생성기 (KakaoTalk 기반)

> 카카오톡 대화를 업로드하면 AI가 요약·감정분석을 수행하고 감성 일기를 자동으로 생성합니다.  
> 웹과 모바일(Flutter) 환경에서 모두 사용 가능합니다.  

[![Demo](https://img.shields.io/badge/Demo-online-green?style=flat&logo=fastapi)](https://py-finetuning.onrender.com)  
[![Docs](https://img.shields.io/badge/API%20Docs-FastAPI-blue?logo=fastapi)](https://py-finetuning.onrender.com/docs)  

---

## 🚀 데모
- **웹 UI** → `/`  
- **API 문서** → `/docs`  
- **헬스체크** → `/api/status`  

---

## ✨ 주요 기능
- 대화 요약 → 감정 분석 → 감성 일기(JSON 5섹션) 생성  
- 날짜별 분석 (특정 날짜만 추출/분석)  
- 일관성 테스트 (n회 반복 → 유사도/점수 산출)  
- 웹 UI: 파일 업로드, 시각화, 다운로드  
- Flutter 연동: 파일 업로드·결과 확인·로컬 저장  
- 간단한 회원가입/로그인/세션 유지  

---

## 🏗 아키텍처
- **Backend**: FastAPI + OpenAI API (gpt-4o / gpt-4o-mini)  
- **Frontend**: Jinja2 + Bootstrap 5 + Chart.js  
- **Infra**: Docker + Render.com  

```bash
📂 project-root
 ├─ main.py               # FastAPI 엔드포인트 및 핵심 로직
 ├─ templates/            # 웹 UI (Jinja2)
 ├─ static/               # 정적 리소스
 ├─ Dockerfile            # 컨테이너 빌드
 ├─ render.yaml           # Render 배포 설정
 └─ requirements.txt      # 의존성
