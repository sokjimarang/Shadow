#!/bin/bash
# ngrok 터널링 시작 스크립트

set -e

# 포트 설정 (기본값: 8000)
PORT=${PORT:-8000}

echo "🌐 ngrok 터널링 시작..."
echo "   로컬 포트: $PORT"
echo ""
echo "⚠️  주의사항:"
echo "   1. FastAPI 서버가 먼저 실행되어 있어야 합니다"
echo "   2. ngrok URL을 Slack App 설정에 등록하세요"
echo ""

# ngrok으로 로컬 서버 노출
ngrok http "$PORT"
