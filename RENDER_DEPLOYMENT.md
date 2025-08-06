# 🚀 Render.com 배포 가이드 (가장 간단!)

Render.com은 무료로 사용할 수 있고 매우 간단한 클라우드 서비스입니다.

## 📋 사전 준비사항

### 1. GitHub 계정
- GitHub에 가입되어 있어야 합니다
- 프로젝트를 GitHub에 업로드해야 합니다

### 2. Render.com 계정
- [render.com](https://render.com)에서 무료 계정 생성
- GitHub 계정으로 로그인 가능

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

### 2단계: Render.com에서 서비스 생성

1. **Render.com 로그인**
   - [render.com](https://render.com) 접속
   - GitHub 계정으로 로그인

2. **새 Web Service 생성**
   - "New +" 버튼 클릭
   - "Web Service" 선택
   - GitHub 저장소 연결

3. **서비스 설정**
   ```
   Name: emotion-diary-app
   Environment: Docker
   Region: Oregon (US West)
   Branch: main
   Root Directory: (비워두기)
   ```

4. **환경 변수 설정**
   - "Environment" 탭 클릭
   - "Add Environment Variable" 클릭
   - `OPENAI_API_KEY` = `your_openai_api_key_here`

5. **배포 시작**
   - "Create Web Service" 클릭
   - 자동으로 배포가 시작됩니다 (5-10분 소요)

### 3단계: 도메인 확인

배포 완료 후:
- **자동 도메인**: `https://your-app-name.onrender.com`
- **커스텀 도메인**: 원하는 도메인 연결 가능

## 🔧 설정 파일 설명

### render.yaml
```yaml
services:
  - type: web
    name: emotion-diary-app    # 서비스 이름
    env: docker               # Docker 환경 사용
    plan: free               # 무료 플랜
    region: oregon           # 서버 지역
    healthCheckPath: /api/status  # 헬스체크 경로
    envVars:
      - key: OPENAI_API_KEY  # 환경 변수
        sync: false          # GitHub에 동기화 안함
```

## 🌐 접속 방법

### 웹 브라우저
- **URL**: `https://your-app-name.onrender.com`
- **예시**: `https://emotion-diary-app.onrender.com`

### Flutter 앱 설정
```dart
// lib/config/api_config.dart
class ApiConfig {
  // Render.com 서버 주소
  static const String baseUrl = "https://your-app-name.onrender.com";
}
```

## 🔄 업데이트 방법

### 자동 배포 (권장)
1. GitHub에 코드 푸시
2. Render.com이 자동으로 새로 배포
3. 5-10분 후 업데이트 완료

### 수동 배포
1. Render.com 대시보드 접속
2. 서비스 선택
3. "Manual Deploy" 클릭

## 📊 모니터링

### Render.com 대시보드에서 확인 가능:
- ✅ 서비스 상태
- ✅ 로그 확인
- ✅ 트래픽 사용량
- ✅ 에러 알림

### 헬스체크
```bash
# API 상태 확인
curl https://your-app-name.onrender.com/api/status

# 웹 페이지 확인
curl -I https://your-app-name.onrender.com
```

## 🆓 무료 플랜 제한사항

### Render.com 무료 플랜:
- ✅ **월 750시간** (거의 24/7 사용 가능)
- ✅ **자동 슬립**: 15분 비활성 시 슬립 모드
- ✅ **첫 요청 시 깨움**: 약 30초 소요
- ✅ **SSL 무료**: HTTPS 자동 제공
- ✅ **도메인 무료**: `.onrender.com` 도메인

### 주의사항:
- ⚠️ **슬립 모드**: 15분 비활성 시 서버가 잠들어요
- ⚠️ **첫 요청 지연**: 깨우는데 30초 정도 걸려요
- ⚠️ **트래픽 제한**: 월 750시간 (충분함)

## 🛠️ 문제 해결

### 1. 배포 실패
```bash
# 로그 확인
# Render.com 대시보드 → Logs 탭

# 일반적인 문제:
# - OPENAI_API_KEY 설정 안됨
# - Docker 빌드 실패
# - 포트 설정 오류
```

### 2. 서비스 접속 안됨
```bash
# 헬스체크 확인
curl https://your-app-name.onrender.com/api/status

# 대기 시간: 첫 요청은 30초 정도 걸릴 수 있음
```

### 3. 환경 변수 설정
```bash
# Render.com 대시보드 → Environment 탭
# OPENAI_API_KEY = your_actual_api_key
```

## 💡 팁

### 1. 커스텀 도메인 설정
1. 도메인 구매 (예: GoDaddy, Namecheap)
2. Render.com에서 "Custom Domains" 설정
3. DNS 설정 변경

### 2. 성능 최적화
- 첫 요청 지연을 줄이려면 정기적으로 핑
- 무료 플랜에서는 슬립 모드가 있으니 참고

### 3. 비용 관리
- 무료 플랜으로 충분히 사용 가능
- 필요시 유료 플랜으로 업그레이드

## 🎉 완료!

이제 Render.com으로 배포하면:
- ✅ **무료로 24/7 서비스**
- ✅ **어디서든 웹 접속 가능**
- ✅ **Flutter 앱에서도 사용 가능**
- ✅ **자동 SSL 보안**
- ✅ **GitHub 연동으로 쉬운 업데이트**

Render.com이 가장 간단하고 무료로 사용하기 좋은 옵션입니다! 🚀 