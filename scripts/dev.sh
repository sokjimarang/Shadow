#!/bin/bash
# 개발 환경 시작 스크립트 (tmux 사용)
# 서버와 ngrok을 동시에 실행합니다

set -e

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# tmux가 설치되어 있는지 확인
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux가 설치되어 있지 않습니다."
    echo "📝 설치 방법:"
    echo "   brew install tmux"
    exit 1
fi

# .env.local 파일 확인
if [ ! -f .env.local ]; then
    echo "❌ .env.local 파일이 없습니다."
    echo "📝 .env.example을 복사하여 .env.local을 생성하고 필요한 값을 설정하세요:"
    echo "   cp .env.example .env.local"
    exit 1
fi

# 포트 설정
PORT=${PORT:-8000}
SESSION_NAME="shadow-dev"

# 기존 세션이 있으면 종료
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

echo "🚀 Shadow 개발 환경 시작..."
echo ""
echo "   세션 이름: $SESSION_NAME"
echo "   포트: $PORT"
echo ""
echo "📝 tmux 사용법:"
echo "   - Ctrl+b, 0: FastAPI 서버 화면으로 전환"
echo "   - Ctrl+b, 1: ngrok 화면으로 전환"
echo "   - Ctrl+b, d: 세션에서 나가기 (백그라운드 실행)"
echo "   - tmux attach -t $SESSION_NAME: 세션에 다시 접속"
echo "   - tmux kill-session -t $SESSION_NAME: 세션 종료"
echo ""

sleep 2

# tmux 세션 생성 및 창 분할
tmux new-session -d -s "$SESSION_NAME" -n "shadow"

# 첫 번째 창: FastAPI 서버
tmux send-keys -t "$SESSION_NAME:0" "PORT=$PORT ./scripts/run_server.sh" C-m

# 두 번째 창: ngrok (5초 후 시작 - 서버가 먼저 실행되도록)
tmux new-window -t "$SESSION_NAME:1" -n "ngrok"
tmux send-keys -t "$SESSION_NAME:1" "echo '⏳ 서버 시작 대기 중 (5초)...'" C-m
tmux send-keys -t "$SESSION_NAME:1" "sleep 5" C-m
tmux send-keys -t "$SESSION_NAME:1" "PORT=$PORT ./scripts/start_ngrok.sh" C-m

# 첫 번째 창으로 이동
tmux select-window -t "$SESSION_NAME:0"

# 세션에 접속
tmux attach-session -t "$SESSION_NAME"
