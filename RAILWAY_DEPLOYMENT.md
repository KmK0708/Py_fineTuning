# 🚂 Railway.app 배포 가이드

Railway.app은 매우 간단하고 빠른 클라우드 서비스입니다.

## 📋 사전 준비사항

### 1. GitHub 계정
- GitHub에 가입되어 있어야 합니다

### 2. Railway.app 계정
- [railway.app](https://railway.app)에서 무료 계정 생성
- GitHub 계정으로 로그인

### 3. OpenAI API 키
- OpenAI API 키가 필요합니다

## 🚀 배포 단계

### 1단계: GitHub에 프로젝트 업로드

```bash
# 1. GitHub에서 새 저장소 생성
# 2. 로컬에서 Git 초기화
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/your-repo-name.git
git push -u origin main
```

### 2단계: Railway.app에서 프로젝트 생성

1. **Railway.app 로그인**
   - [railway.app](https://railway.app) 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "Start a New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - GitHub 저장소 선택

3. **서비스 설정**
   - 자동으로 Dockerfile 감지
   - 환경 변수 설정 필요

4. **환경 변수 설정**
   - "Variables" 탭 클릭
   - "New Variable" 클릭
   - `OPENAI_API_KEY` = `your_openai_api_key_here`

5. **배포 시작**
   - 자동으로 배포가 시작됩니다 (2-5분 소요)

### 3단계: 도메인 확인

배포 완료 후:
- **자동 도메인**: `https://your-app-name.railway.app`
- **커스텀 도메인**: 원하는 도메인 연결 가능

## 🌐 접속 방법

### 웹 브라우저
- **URL**: `https://your-app-name.railway.app`
- **예시**: `https://emotion-diary-app.railway.app`

### Flutter 앱 설정
```dart
// lib/config/api_config.dart
class ApiConfig {
  // Railway.app 서버 주소
  static const String baseUrl = "https://your-app-name.railway.app";
}
```

## 🆓 무료 플랜 제한사항

### Railway.app 무료 플랜:
- ✅ **월 $5 크레딧** (충분함)
- ✅ **24/7 서비스** (슬립 모드 없음)
- ✅ **빠른 응답** (첫 요청 지연 없음)
- ✅ **SSL 무료**: HTTPS 자동 제공
- ✅ **도메인 무료**: `.railway.app` 도메인

### 장점:
- 🚀 **슬립 모드 없음**: 항상 활성 상태
- 🚀 **빠른 응답**: 첫 요청도 즉시 응답
- 🚀 **고성능**: 빠른 서버

## 🔄 업데이트 방법

### 자동 배포 (권장)
1. GitHub에 코드 푸시
2. Railway.app이 자동으로 새로 배포
3. 2-5분 후 업데이트 완료

## 📊 모니터링

### Railway.app 대시보드에서 확인 가능:
- ✅ 서비스 상태
- ✅ 로그 확인
- ✅ 트래픽 사용량
- ✅ 에러 알림

## 🛠️ 문제 해결

### 1. 배포 실패
```bash
# 로그 확인
# Railway.app 대시보드 → Deployments → Logs

# 일반적인 문제:
# - OPENAI_API_KEY 설정 안됨
# - Docker 빌드 실패
```

### 2. 서비스 접속 안됨
```bash
# 헬스체크 확인
curl https://your-app-name.railway.app/api/status
```

## 💡 Railway.app vs Render.com 비교

| 기능 | Railway.app | Render.com |
|------|-------------|------------|
| 무료 크레딧 | $5/월 | 750시간/월 |
| 슬립 모드 | ❌ 없음 | ✅ 있음 |
| 첫 요청 지연 | ❌ 없음 | ⚠️ 30초 |
| 배포 속도 | 빠름 (2-5분) | 보통 (5-10분) |
| 사용 편의성 | 매우 간단 | 간단 |

## 🎉 완료!

Railway.app으로 배포하면:
- ✅ **무료로 24/7 서비스**
- ✅ **슬립 모드 없음** (항상 활성)
- ✅ **빠른 응답** (첫 요청 지연 없음)
- ✅ **어디서든 웹 접속 가능**
- ✅ **Flutter 앱에서도 사용 가능**
- ✅ **자동 SSL 보안**

Railway.app이 **슬립 모드가 없어서 더 안정적**입니다! 🚂 