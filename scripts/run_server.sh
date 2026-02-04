#!/bin/bash
# FastAPI 서버 실행 스크립트

set -e

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# .env.local 파일 확인
if [ ! -f .env.local ]; then
    echo "❌ .env.local 파일이 없습니다."
    echo "📝 .env.example을 복사하여 .env.local을 생성하고 필요한 값을 설정하세요:"
    echo "   cp .env.example .env.local"
    exit 1
fi

# 포트 설정 (기본값: 8000)
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "🚀 Shadow FastAPI 서버 시작..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo ""

# uvicorn으로 FastAPI 서버 실행
uv run uvicorn main:app --host "$HOST" --port "$PORT" --reload
