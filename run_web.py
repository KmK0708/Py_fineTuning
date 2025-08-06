#!/usr/bin/env python3
"""
감성 일기 생성기 웹 서버 실행 스크립트
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 감성 일기 생성기 웹 서버를 시작합니다...")
    print("📱 웹 브라우저에서 http://localhost:8000 으로 접속하세요")
    print("🔧 API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 