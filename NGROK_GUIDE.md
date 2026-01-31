# Shadow ngrok 실행 가이드

이 가이드는 Shadow FastAPI 서버를 ngrok으로 외부에 노출시켜 Slack 이벤트를 수신하는 방법을 안내합니다.

## 📋 사전 요구사항

### 1. ngrok 설치

```bash
# Homebrew로 설치 (macOS)
brew install ngrok

# 또는 공식 사이트에서 다운로드
# https://ngrok.com/download
```

### 2. tmux 설치 (개발 환경 모드 사용 시)

```bash
brew install tmux
```

## ⚙️ 환경 설정

### 1. 환경 변수 파일 생성

```bash
# .env.example을 복사하여 .env.local 생성
cp .env.example .env.local
```

### 2. .env.local 파일 편집

```env
# 필수: Claude API 키
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 필수: Supabase 설정
SUPABASE_URL=https://ddntzfdetgcobzohimvm.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# 선택: Gemini API 키 (대안 백엔드)
GEMINI_API_KEY=your_gemini_api_key

# 선택: Slack Bot 설정 (Slack 연동 시)
SLACK_BOT_TOKEN=xoxb-xxxxx
SLACK_SIGNING_SECRET=xxxxx
SLACK_APP_TOKEN=xapp-xxxxx
SLACK_DEFAULT_CHANNEL=C07UZ1234AB  # 기본 전송 채널 ID
```

### 3. 환경 변수 확인

```bash
make check-env
```

출력 예시:
```
✅ .env.local 파일 존재

📋 필수 환경 변수:
--------------------------------
✅ Claude API 키: sk-ant-api...
✅ Supabase URL: https://dd...
✅ Supabase Key: eyJhbGciO...

📋 선택 환경 변수:
--------------------------------
⚠️  Gemini API 키 (선택): 미설정
✅ Slack Bot Token (선택): xoxb-12345...
✅ Slack Signing Secret (선택): ab12cd34ef...
✅ Slack App Token (선택): xapp-1-AAA...

================================
✅ 모든 필수 환경 변수가 설정되었습니다!
```

## 🚀 실행 방법

### 방법 1: 개발 환경 모드 (권장)

서버와 ngrok을 동시에 실행합니다 (tmux 사용).

```bash
make dev
```

**tmux 사용법:**
- `Ctrl+b, 0`: FastAPI 서버 화면으로 전환
- `Ctrl+b, 1`: ngrok 화면으로 전환
- `Ctrl+b, d`: 세션에서 나가기 (백그라운드 실행)
- `tmux attach -t shadow-dev`: 세션에 다시 접속
- `tmux kill-session -t shadow-dev`: 세션 종료

### 방법 2: 별도 터미널에서 실행

**터미널 1 - FastAPI 서버:**
```bash
make server
```

**터미널 2 - ngrok:**
```bash
make ngrok
```

### 방법 3: 수동 실행

```bash
# FastAPI 서버
./scripts/run_server.sh

# ngrok (별도 터미널)
./scripts/start_ngrok.sh
```

## 🌐 ngrok URL 확인

ngrok이 시작되면 다음과 같은 화면이 표시됩니다:

```
Session Status                online
Account                       your_account (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-1234-5678.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**중요:** `Forwarding` 항목의 HTTPS URL이 외부에서 접근 가능한 주소입니다.

예: `https://abcd-1234-5678.ngrok-free.app`

### ngrok 웹 인터페이스

로컬에서 `http://127.0.0.1:4040`에 접속하면 요청 로그를 실시간으로 확인할 수 있습니다.

## 📡 Slack App 설정

### 1. Slack App Event Subscriptions 설정

1. [Slack API](https://api.slack.com/apps)에서 앱 선택
2. **Event Subscriptions** 메뉴로 이동
3. **Enable Events** 활성화
4. **Request URL** 입력:
   ```
   https://your-ngrok-url.ngrok-free.app/api/slack/events
   ```
   (ngrok URL은 매번 변경되므로 서버 재시작 시마다 업데이트 필요)

5. **Subscribe to bot events** 섹션에서 필요한 이벤트 추가:
   - `message.channels`
   - `message.groups`
   - `message.im`
   - `message.mpim`

6. **Save Changes** 클릭

### 2. Interactivity 설정 (버튼/모달 사용 시)

1. **Interactivity & Shortcuts** 메뉴로 이동
2. **Interactivity** 활성화
3. **Request URL** 입력:
   ```
   https://your-ngrok-url.ngrok-free.app/api/slack/interactions
   ```

## 🔍 API 엔드포인트 확인

### FastAPI Swagger UI

브라우저에서 다음 URL로 접속:

```
# 로컬
http://localhost:8000/docs

# ngrok
https://your-ngrok-url.ngrok-free.app/docs
```

### 주요 엔드포인트

- `GET /status`: 서버 상태 확인
- `POST /recording/start`: 녹화 시작
- `POST /recording/stop`: 녹화 중지
- `GET /recording/status`: 녹화 상태 조회
- `POST /analyze`: 녹화 데이터 분석
- `GET /patterns`: 패턴 감지 결과

### 테스트 예시

```bash
# 서버 상태 확인
curl https://your-ngrok-url.ngrok-free.app/status

# 녹화 시작
curl -X POST https://your-ngrok-url.ngrok-free.app/recording/start \
  -H "Content-Type: application/json" \
  -d '{"duration": 10, "fps": 10}'

# 녹화 상태 확인
curl https://your-ngrok-url.ngrok-free.app/recording/status
```

## ⚠️ 주의사항

### ngrok 무료 플랜 제약사항

- **URL 변경**: ngrok을 재시작할 때마다 URL이 변경됩니다
  - 해결: ngrok 유료 플랜에서 고정 도메인 사용
  - 또는: Slack App 설정을 매번 업데이트

- **세션 제한**: 무료 플랜은 동시 연결 제한이 있습니다
  - 제한: 40 connections/min

- **배너**: 무료 플랜에서는 첫 방문 시 ngrok 경고 페이지가 표시됩니다
  - 해결: 유료 플랜 사용 또는 "Visit Site" 클릭

### 보안

- `.env.local` 파일은 절대 git에 커밋하지 마세요 (`.gitignore`에 이미 추가됨)
- ngrok URL은 외부에 노출되므로 인증/인가 로직 추가를 권장합니다
- 프로덕션 환경에서는 ngrok 대신 정식 도메인과 SSL 인증서를 사용하세요

## 🐛 트러블슈팅

### 서버가 시작되지 않는 경우

```bash
# 환경 변수 확인
make check-env

# 포트 충돌 확인
lsof -i :8000

# 다른 포트로 실행
PORT=8001 make server
PORT=8001 make ngrok
```

### ngrok 연결 오류

```bash
# ngrok 로그인 확인
ngrok authtoken YOUR_AUTH_TOKEN

# ngrok 설정 확인
ngrok config check
```

### Slack 이벤트가 수신되지 않는 경우

1. ngrok URL이 Slack App에 올바르게 설정되었는지 확인
2. ngrok 웹 인터페이스(`http://127.0.0.1:4040`)에서 요청 로그 확인
3. Slack App의 Event Subscriptions 페이지에서 URL 검증 상태 확인

## 📚 추가 리소스

- [ngrok 공식 문서](https://ngrok.com/docs)
- [Slack Events API 가이드](https://api.slack.com/apis/connections/events-api)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
