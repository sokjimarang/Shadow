#!/bin/bash
# 환경 변수 확인 스크립트

set -e

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

echo "🔍 Shadow 환경 변수 확인"
echo "================================"
echo ""

# .env.local 파일 존재 확인
if [ ! -f .env.local ]; then
    echo "❌ .env.local 파일이 없습니다."
    echo ""
    echo "📝 설정 방법:"
    echo "   1. .env.example을 복사하여 .env.local 생성:"
    echo "      cp .env.example .env.local"
    echo ""
    echo "   2. .env.local 파일을 열고 필요한 값을 설정:"
    echo "      - ANTHROPIC_API_KEY (필수: Claude API)"
    echo "      - SUPABASE_URL (필수: DB 연결)"
    echo "      - SUPABASE_KEY (필수: DB 인증)"
    echo "      - SLACK_BOT_TOKEN (선택: Slack 연동)"
    echo "      - SLACK_SIGNING_SECRET (선택: Slack 연동)"
    echo "      - SLACK_APP_TOKEN (선택: Slack 연동)"
    exit 1
fi

echo "✅ .env.local 파일 존재"
echo ""

# .env.local 파일 로드
export $(cat .env.local | grep -v '^#' | xargs)

# 필수 환경 변수 확인
REQUIRED_VARS=(
    "ANTHROPIC_API_KEY:Claude API 키"
    "SUPABASE_URL:Supabase URL"
    "SUPABASE_KEY:Supabase Key"
)

OPTIONAL_VARS=(
    "GEMINI_API_KEY:Gemini API 키 (선택)"
    "SLACK_BOT_TOKEN:Slack Bot Token (선택)"
    "SLACK_SIGNING_SECRET:Slack Signing Secret (선택)"
    "SLACK_APP_TOKEN:Slack App Token (선택)"
    "SLACK_DEFAULT_CHANNEL:Slack 기본 채널 ID (선택)"
)

echo "📋 필수 환경 변수:"
echo "--------------------------------"

all_required_set=true
for var_info in "${REQUIRED_VARS[@]}"; do
    var_name="${var_info%%:*}"
    var_desc="${var_info##*:}"

    if [ -z "${!var_name}" ] || [ "${!var_name}" == "your_api_key_here" ] || [ "${!var_name}" == "your_supabase_anon_key_here" ]; then
        echo "❌ $var_desc: 미설정"
        all_required_set=false
    else
        # 값의 앞 10자만 표시
        masked_value="${!var_name:0:10}..."
        echo "✅ $var_desc: $masked_value"
    fi
done

echo ""
echo "📋 선택 환경 변수:"
echo "--------------------------------"

for var_info in "${OPTIONAL_VARS[@]}"; do
    var_name="${var_info%%:*}"
    var_desc="${var_info##*:}"

    if [ -z "${!var_name}" ] || [ "${!var_name}" == "your_"* ]; then
        echo "⚠️  $var_desc: 미설정"
    else
        masked_value="${!var_name:0:10}..."
        echo "✅ $var_desc: $masked_value"
    fi
done

echo ""
echo "================================"

if [ "$all_required_set" = false ]; then
    echo "❌ 일부 필수 환경 변수가 설정되지 않았습니다."
    echo "   .env.local 파일을 확인하고 필요한 값을 설정하세요."
    exit 1
else
    echo "✅ 모든 필수 환경 변수가 설정되었습니다!"
fi
