# Slack Bot 호출 흐름

## 주요 호출 흐름 설명

### 📥 인바운드 (Slack → Shadow)

#### 1. 이벤트 수신 (1️⃣)

- Slack이 shadow-web의 `/api/slack/events`로 Webhook 전송
- `shadow-web/app/api/slack/events/route.ts`에서 처리
- 서명 검증 → Supabase 저장 → 패턴 분석 요청

#### 2. 인터랙션 수신 (2️⃣, 7️⃣)

- 사용자 버튼 클릭 → Slack이 `/api/slack/interactions`로 Webhook 전송
- `shadow-web/app/api/slack/interactions/route.ts`에서 처리
- 서명 검증 → Supabase에 응답 저장

### 🔄 내부 처리 (shadow-web ↔ shadow-py)

#### 3. 분석 파이프라인 (3️⃣)

- shadow-web → shadow-py HTTP 호출
- `/api/shadow/*` 프록시 → `http://localhost:8000/*`
- 녹화 → 분석 → 패턴 감지 → HITL 질문 생성

### 📤 아웃바운드 (Shadow → Slack)

#### 4. 질문 생성 (4️⃣)

- shadow-py의 HITLQuestionGenerator가 질문 생성
- SlackClient가 Block Kit UI 구성

#### 5. 메시지 전송 (5️⃣)

- **두 가지 경로:**
  - `shadow-py/slack/client.py` → Slack API 직접 호출
  - `shadow-web/lib/slack/client.ts` → Slack API 호출
- Bot Token 사용
- Slack API: `chat.postMessage`, `chat.update`

#### 6. 사용자에게 표시 (6️⃣)

- Slack이 사용자에게 메시지 표시
- Block Kit UI (버튼, 메뉴 등)

### 🔁 순환 (7️⃣)

- 사용자가 버튼 클릭 → 다시 2️⃣로 돌아감

## 주요 차이점

| 항목 | shadow-web (Next.js) | shadow-py (FastAPI) |
|------|---------------------|---------------------|
| **역할** | API 게이트웨이 + 프론트엔드 | 분석 엔진 + 백엔드 |
| **Slack 이벤트** | Webhook 수신 (Vercel) | Webhook 수신 (ngrok 필요) |
| **Slack 메시지 전송** | `@slack/web-api` 사용 | `slack_sdk` 사용 |
| **데이터 저장** | Supabase (이벤트/응답) | Supabase (분석 결과) |
| **배포** | Vercel (프로덕션) | 로컬/서버 (개발 중) |

## ngrok 역할

- **개발 환경에서만 사용**: shadow-py를 직접 Slack Webhook 엔드포인트로 사용할 때
- **프로덕션**: shadow-web이 Vercel에 배포되어 있으므로 ngrok 불필요
- **현재 구조**: shadow-web이 메인 Webhook 수신기 역할