# 🌐 클라우드 서버 배포 가이드

감성 일기 생성기를 클라우드 서버에 배포하여 웹과 모바일 앱에서 접근할 수 있도록 설정하는 방법입니다.

## 📋 사전 준비사항

### 1. 클라우드 서버 준비
- **AWS EC2**, **Google Cloud Compute Engine**, **Azure VM** 등
- **Ubuntu 20.04 LTS** 이상 권장
- **최소 사양**: 1GB RAM, 1 vCPU, 20GB 저장공간

### 2. 도메인 준비 (선택사항)
- 웹 접속을 위한 도메인
- SSL 인증서 발급용

## 🚀 배포 방법

### 방법 1: 자동 배포 스크립트 사용 (권장)

```bash
# 1. 서버에 접속
ssh username@your-server-ip

# 2. 프로젝트 클론 또는 업로드
git clone your-repository-url
cd Py_fineTuning

# 3. 환경 변수 설정
export OPENAI_API_KEY=your_openai_api_key_here

# 4. 배포 스크립트 실행 권한 부여
chmod +x deploy.sh

# 5. 배포 실행
./deploy.sh
```

### 방법 2: 수동 배포

```bash
# 1. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. 환경 변수 설정
export OPENAI_API_KEY=your_openai_api_key_here

# 4. 서비스 시작
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 설정 파일

### 1. 환경 변수 설정
```bash
# .env 파일 생성
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
EOF
```

### 2. 방화벽 설정
```bash
# Ubuntu UFW 방화벽 설정
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## 🌐 접속 방법

### 웹 브라우저
- **HTTP**: `http://your-server-ip`
- **HTTPS**: `https://your-server-ip`

### Flutter 앱 설정
Flutter 앱의 API 설정을 다음과 같이 변경:

```dart
// 기존 (로컬)
String baseUrl = "http://localhost:8000";

// 변경 (클라우드)
String baseUrl = "https://your-server-ip";
```

## 🔒 보안 설정

### 1. SSL 인증서 설정 (프로덕션용)

#### Let's Encrypt 사용
```bash
# Certbot 설치
sudo apt update
sudo apt install certbot

# 인증서 발급
sudo certbot certonly --standalone -d your-domain.com

# Nginx 설정 업데이트
# nginx.conf 파일에서 SSL 인증서 경로 수정
```

### 2. 방화벽 추가 설정
```bash
# 특정 IP만 허용 (선택사항)
sudo ufw allow from your-ip-address to any port 22
sudo ufw deny 22  # SSH 기본 포트 차단
```

## 📊 모니터링

### 1. 서비스 상태 확인
```bash
# 컨테이너 상태 확인
docker-compose -f docker-compose.prod.yml ps

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 리소스 사용량 확인
docker stats
```

### 2. 헬스체크
```bash
# API 상태 확인
curl https://your-server-ip/api/status

# 웹 페이지 접속 확인
curl -I https://your-server-ip
```

## 🔄 업데이트 방법

### 1. 코드 업데이트
```bash
# 새 코드로 업데이트
git pull origin main

# 서비스 재시작
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### 2. 환경 변수 업데이트
```bash
# 환경 변수 변경 후
export OPENAI_API_KEY=new_api_key

# 서비스 재시작
docker-compose -f docker-compose.prod.yml restart emotion-diary-app
```

## 🛠️ 문제 해결

### 1. 서비스 시작 실패
```bash
# 로그 확인
docker-compose -f docker-compose.prod.yml logs

# 컨테이너 재시작
docker-compose -f docker-compose.prod.yml restart
```

### 2. 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# 충돌하는 서비스 중지
sudo systemctl stop apache2  # 예시
```

### 3. 메모리 부족
```bash
# 메모리 사용량 확인
free -h

# 스왑 메모리 추가 (필요시)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 📱 Flutter 앱 설정

### 1. API 주소 변경
```dart
// lib/config/api_config.dart
class ApiConfig {
  // 로컬 개발용
  // static const String baseUrl = "http://localhost:8000";
  
  // 클라우드 서버용
  static const String baseUrl = "https://your-server-ip";
}
```

### 2. HTTPS 인증서 처리
```dart
// Android: android/app/src/main/AndroidManifest.xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

```dart
// iOS: ios/Runner/Info.plist
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

## 🔍 성능 최적화

### 1. Nginx 캐싱 설정
```nginx
# nginx.conf에 추가
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 2. Docker 리소스 제한
```yaml
# docker-compose.prod.yml에 추가
services:
  emotion-diary-app:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:
1. 서버 로그: `docker-compose -f docker-compose.prod.yml logs`
2. 네트워크 연결: `ping your-server-ip`
3. 포트 상태: `netstat -tlnp`

추가 지원이 필요하면 이슈를 등록해주세요. 