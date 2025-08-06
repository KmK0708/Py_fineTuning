#!/bin/bash

# 감성 일기 생성기 클라우드 배포 스크립트

set -e

echo "🚀 감성 일기 생성기 클라우드 배포를 시작합니다..."

# 1. 환경 변수 확인
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다."
    echo "export OPENAI_API_KEY=your_api_key_here 를 실행하세요."
    exit 1
fi

# 2. Docker 설치 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    echo "Docker를 먼저 설치해주세요: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    echo "Docker Compose를 설치해주세요."
    exit 1
fi

# 3. SSL 인증서 생성 (개발용)
echo "🔐 SSL 인증서를 생성합니다..."
mkdir -p ssl
if [ ! -f ssl/nginx-selfsigned.crt ] || [ ! -f ssl/nginx-selfsigned.key ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/nginx-selfsigned.key \
        -out ssl/nginx-selfsigned.crt \
        -subj "/C=KR/ST=Seoul/L=Seoul/O=EmotionDiary/CN=localhost"
    echo "✅ SSL 인증서가 생성되었습니다."
else
    echo "✅ 기존 SSL 인증서를 사용합니다."
fi

# 4. 로그 디렉토리 생성
mkdir -p logs

# 5. 기존 컨테이너 정리
echo "🧹 기존 컨테이너를 정리합니다..."
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# 6. 이미지 빌드
echo "🔨 Docker 이미지를 빌드합니다..."
docker-compose -f docker-compose.prod.yml build

# 7. 서비스 시작
echo "🚀 서비스를 시작합니다..."
docker-compose -f docker-compose.prod.yml up -d

# 8. 서비스 상태 확인
echo "⏳ 서비스가 시작될 때까지 기다립니다..."
sleep 10

# 9. 헬스체크
echo "🔍 서비스 상태를 확인합니다..."
if curl -f http://localhost/api/status > /dev/null 2>&1; then
    echo "✅ 서비스가 정상적으로 시작되었습니다!"
    echo ""
    echo "🌐 웹 접속 주소:"
    echo "   HTTP:  http://$(curl -s ifconfig.me)"
    echo "   HTTPS: https://$(curl -s ifconfig.me)"
    echo ""
    echo "📱 Flutter 앱에서 사용할 API 주소:"
    echo "   https://$(curl -s ifconfig.me)"
    echo ""
    echo "📊 서비스 모니터링:"
    echo "   docker-compose -f docker-compose.prod.yml logs -f"
    echo ""
    echo "🛑 서비스 중지:"
    echo "   docker-compose -f docker-compose.prod.yml down"
else
    echo "❌ 서비스 시작에 실패했습니다."
    echo "로그를 확인해주세요:"
    echo "docker-compose -f docker-compose.prod.yml logs"
    exit 1
fi 