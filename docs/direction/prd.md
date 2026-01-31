<aside>

### PRD 버전 관리

v2.0

[PRD v2.0](https://www.notion.so/PRD-v2-0-2f9630957afa8033ab11d246f8f1790e?pvs=21)

</aside>

# Shadow - PRD (Product Requirements Document)

**버전: v3.0**

**마지막 업데이트: 2026-01-31**

---

## 1. 개요

### 1.1 문제-솔루션 요약

**문제**: AI 에이전트에게 업무를 위임하려면 판단 기준과 품질 기준을 설명해야 하는데, 대부분의 사람들은 자신의 업무 방식을 언어화하지 못한다.

**솔루션**: Shadow는 사용자의 화면을 관찰하여 반복 업무 패턴을 발견하고, HITL(Human-in-the-Loop) 질문을 통해 불확실한 부분을 확인하여, AI 에이전트가 사용할 수 있는 **에이전트 명세서**를 자동 생성한다.

**핵심 전환**: "어떻게 일하세요?" (열린 질문) → "이렇게 하신 것 맞나요?" (닫힌 질문)

### 1.2 제약사항

| 항목 | 내용 |
| --- | --- |
| **총 개발 시간** | 18시간 |
| **팀 구성** | 2인 |
| **현재 시점** | Hour 3 (3시간 경과) |
| **남은 시간** | 15시간 |
| **타겟 사용자** | 반복적인 컴퓨터 업무를 수행하는 지식 노동자 |

---

## 2. 시스템 아키텍처

> v3.0 신규 섹션: 병렬 개발 과정에서 Slack 관련 기능을 TypeScript로 구현하여 2개 서비스로 분리됨.
> 

### 2.1 서비스 구성

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Shadow System                              │
├──────────────────────────────┬──────────────────────────────────────┤
│       shadow-py (Python)     │     shadow-web (TypeScript)          │
│       localhost:8000         │     localhost:3000                   │
├──────────────────────────────┼──────────────────────────────────────┤
│ • 화면 캡처 (mss)            │ • Slack Events 수신                  │
│ • 마우스 이벤트 (pynput)     │ • Slack 메시지 송신                  │
│ • VLM 행동 라벨링            │ • HITL 응답 저장 (Supabase)          │
│ • LLM 패턴 감지              │                                      │
│ • HITL 질문 생성             │                                      │
│ • 명세서 생성                │                                      │
│ • CLI                        │                                      │
└──────────────────────────────┴──────────────────────────────────────┘

```

### 2.2 서비스 간 통신

**HITL 질문 전송** (shadow-py → shadow-web → Slack)

```
shadow-py                          shadow-web                         Slack
    │  POST /api/internal/hitl/send    │                                │
    │─────────────────────────────────→│  chat.postMessage              │
    │                                  │───────────────────────────────→│
    │  {ok: true, message_ts}          │                                │
    │←─────────────────────────────────│                                │

```

**HITL 응답 수신** (Slack → shadow-web → shadow-py)

```
Slack                              shadow-web                      shadow-py
    │  POST /api/slack/events          │                                │
    │─────────────────────────────────→│  POST /api/hitl/response       │
    │                                  │───────────────────────────────→│
    │                                  │  {ok: true}                    │
    │                                  │←───────────────────────────────│

```

---

## 3. 목표

### 3.1 핵심 데모 목표

> "3회 관찰 후, 사용자가 2개 질문에 답하면 spec이 생성되고, 다음 회차부터는 같은 판단을 질문 없이 재현한다 (동일 판단 기준을 다시 묻지 않음)."
> 

### 3.2 성공 기준 (Pass/Fail)

데모 성공 여부는 아래 테스트케이스의 Pass/Fail로 판단한다.

| ID | 테스트 항목 | Pass 조건 | 우선순위 | 담당 |
| --- | --- | --- | --- | --- |
| TC-01 | 화면 캡처 | 클릭 이벤트 발생 시 Before/After 스크린샷이 저장됨 | P0 | shadow-py |
| TC-02 | 행동 라벨링 | 스크린샷+이벤트를 VLM에 입력하면 semantic_label이 생성됨 | P0 | shadow-py |
| TC-03 | 패턴 감지 | 3회 유사 시퀀스 입력 시 패턴 후보가 1개 이상 생성됨 | P0 | shadow-py |
| TC-04 | 질문 생성 | 패턴의 불확실 지점에서 HITL 질문이 2개 이상 생성됨 | P0 | shadow-py |
| TC-05 | Slack 전송 | 생성된 질문이 Slack DM으로 전송됨 | P0 | **shadow-web** |
| TC-06 | Slack 응답 | 버튼 클릭 응답이 시스템에 전달됨 | P0 | **shadow-web** |
| TC-07 | 명세서 생성 | 응답 반영 후 spec.json 파일이 생성되고, 판단 기준이 포함됨 | P0 | shadow-py |
| TC-08 | E2E 플로우 | 관찰→분석→질문→응답→명세서의 전체 사이클이 1회 완료됨 | P0 | **both** |
| TC-09 | 재질문 방지 | 이미 확인된 판단 기준에 대해 동일 질문이 발생하지 않음 | P1 | shadow-py |

### 3.3 비목표 (Non-Goals)

이번 MVP에서 **의도적으로 제외**하는 것:

- 자동화 스크립트 실행 (명세서 생성까지만)
- 키보드 이벤트 분석 (마우스 클릭만으로 데모 가능)
- HITL 질문 중 "이상 탐지", "대안 제시" 유형 (코칭 성격)
- 웹 UI (Streamlit 대시보드)
- 명세서 버전 관리, 변경 이력
- Slack 자연어 명령 처리
- 다중 모니터, 멀티 앱 복잡 시나리오

---

## 4. 기능 명세

### 4.1 P0 기능 (E2E 데모 필수)

총 **10개**. 이것만 있으면 데모가 동작한다.

| ID | 기능 | 설명 | Pass 조건 | 담당 |
| --- | --- | --- | --- | --- |
| F-01 | 화면 캡처 | 클릭 이벤트 발생 시 Before/After 스크린샷 캡처 | 이미지 파일 2개 저장됨 | shadow-py |
| F-02 | 마우스 이벤트 캡처 | 클릭 위치, 버튼 타입, 타임스탬프 기록 | 이벤트 JSON 저장됨 | shadow-py |
| F-03 | 활성 윈도우 정보 | 현재 앱 이름, 창 제목 수집 | app_name 필드 존재 | shadow-py |
| F-04 | 행동 라벨링 (VLM) | Before/After + 이벤트 → semantic_label 생성 | "Gmail 검색창 클릭" 같은 자연어 라벨 | shadow-py |
| F-05 | 패턴 감지 (LLM) | 3개 이상 세션 비교 → 반복 패턴 식별 | 패턴 후보 1개 이상, uncertainties 포함 | shadow-py |
| F-06 | HITL 질문 생성 | 패턴의 불확실 지점에서 가설검증/품질확인 질문 생성 | question_text, options 포함된 질문 객체 | shadow-py |
| F-07 | Slack 메시지 송신 | 질문을 Slack DM으로 전송 (버튼 UI) | 메시지 ts 반환 | **shadow-web** |
| F-08 | Slack 응답 수신 | 버튼 클릭 이벤트 수신 | selected_option_id 획득 | **shadow-web** |
| F-09 | 명세서 생성 | 패턴 + 응답 → spec.json 파일 저장 | 파일 존재, decisions.rules에 확인된 규칙 포함 | shadow-py |
| F-10 | CLI 시작/중지 | `shadow start`, `shadow stop` 명령 | 프로세스 시작/종료 | shadow-py |

### 4.2 P1 기능 (있으면 좋음)

| ID | 기능 | 설명 | 담당 |
| --- | --- | --- | --- |
| F-11 | 키보드 이벤트 캡처 | 키 입력, 단축키 기록 | shadow-py |
| F-12 | CLI status 명령 | 현재 상태 출력 | shadow-py |
| F-13 | 재질문 방지 로직 | 이미 확인된 규칙은 다시 묻지 않음 | shadow-py |
| F-14 | HITL 이상탐지 질문 | "평소와 다르게 하셨는데, 이유가 있나요?" | shadow-py |
| F-15 | 웹 UI 명세서 조회 | Streamlit으로 spec.json 내용 표시 | shadow-py |

### 4.3 P2 기능 (MVP 이후)

| ID | 기능 | 설명 | 담당 |
| --- | --- | --- | --- |
| F-16 | HITL 대안제시 질문 | "더 효율적인 방법이 있는데, 이유가 있나요?" | shadow-py |
| F-17 | 명세서 버전 관리 | 변경 이력 추적 | shadow-py |
| F-18 | Slack 자연어 명령 | "녹화 중지", "패턴 보여줘" 등 | shadow-web |

### 4.4 HITL 질문 유형

MVP에서는 **P0 유형만** 구현한다.

| 유형 | 트리거 | 질문 예시 | 목적 | 우선순위 |
| --- | --- | --- | --- | --- |
| **가설 검증** | 패턴에서 규칙 추론 | "금액 100만원 넘으면 상사 확인 받으시는 것 같은데, 맞나요?" | 판단 기준 확정 | **P0** |
| **품질 확인** | 최종 산출물 분석 | "결과물에 항상 날짜를 넣으시는데, 필수인가요?" | 품질 기준 확정 | **P0** |
| 이상 탐지 | 평소 패턴과 다른 행동 | "보통은 A→B→C인데, 이번엔 A→D→C 하셨네요." | 예외 조건 학습 | P1 |
| 대안 제시 | 더 효율적인 방법 존재 | "Ctrl+C 대신 우클릭 복사 쓰시는 이유가 있나요?" | 숨은 제약조건 | P2 |

### 4.5 데이터 흐름 요약

```
[관찰]                    [분석]                     [확인]                    [생성]
클릭 이벤트          →    VLM 행동 라벨링      →    HITL 질문 생성      →    명세서 저장
Before/After 캡처         LLM 패턴 감지              Slack 송신/수신           spec.json
마우스 이벤트             uncertainties 식별         응답 해석
윈도우 정보
     │                         │                          │                      │
     └─────────────────────────┴──────────────────────────┴──────────────────────┘
                          shadow-py                   shadow-web              shadow-py

```

---

## 5. API 명세 요약

> 상세 스키마는 별도 문서 참조: shadow-py-api-spec.md, shadow-web-api-spec.md
> 

### 5.1 shadow-py API

**Base URL**: `http://localhost:8000`

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | `/api/session/start` | 관찰 세션 시작 |
| POST | `/api/session/stop` | 관찰 세션 중지 |
| GET | `/api/session/status` | 세션 상태 조회 |
| GET | `/api/patterns` | 감지된 패턴 목록 |
| POST | `/api/hitl/response` | HITL 응답 수신 (shadow-web이 호출) |
| POST | `/api/spec/generate` | 명세서 생성 |
| GET | `/api/health` | 헬스체크 |

### 5.2 shadow-web API

**Base URL**: `http://localhost:3000`

| Method | Endpoint | 설명 |
| --- | --- | --- |
| POST | `/api/slack/events` | Slack Events API 수신 |
| POST | `/api/internal/hitl/send` | HITL 질문 Slack 전송 (shadow-py가 호출) |

---

## 6. 구현 계획

### 6.1 구현 원칙

**스켈레톤 먼저, 점진적 교체**

1. 먼저 모킹 데이터로 **E2E 파이프라인을 연결**한다 (Hour 6까지)
2. 이후 각 모듈을 **실제 구현으로 교체**한다
3. 항상 E2E가 동작하는 상태를 유지한다

### 6.2 타임라인

| 버전 | 시간 | 목표 | 산출물 | 완료 기준 |
| --- | --- | --- | --- | --- |
| **v0.1** | Hour 3-6 | 스켈레톤 E2E | 전체 플로우 모킹 연결 | 가짜 데이터가 CLI→분석→Slack→파일까지 흐름 |
| **v0.2** | Hour 6-9 | 데이터 수집 | 화면 캡처, 마우스 이벤트, VLM 연동 | TC-01, TC-02 Pass |
| **v0.3** | Hour 9-12 | 패턴 분석 | LLM 패턴 감지, 질문 생성 | TC-03, TC-04 Pass |
| **v0.4** | Hour 12-15 | Slack 통합 | 실제 Slack 송수신, 명세서 저장 | TC-05, TC-06, TC-07 Pass |
| **v0.5** | Hour 15-18 | 데모 준비 | 통합 테스트, 데모 연습, 발표 자료 | TC-08 Pass, 데모 성공 |

### 6.3 Hour별 상세

| Hour | 작업 | 산출물 | 담당 | 리스크 |
| --- | --- | --- | --- | --- |
| 3-4 | 프로젝트 셋업, 디렉토리 구조, 모듈 스켈레톤 | 빈 모듈 + main.py | both | 낮음 |
| 4-5 | 모킹 데이터로 E2E 파이프라인 연결 | 가짜 데이터 흐름 | both | 중간 |
| 5-6 | Slack Bot 기본 셋업 (토큰, 이벤트) | 메시지 송수신 테스트 | shadow-web | 중간 |
| 6-7 | mss로 화면 캡처 구현 | 실제 스크린샷 저장 | shadow-py | 낮음 |
| 7-8 | pynput으로 마우스 이벤트 캡처 | 클릭 이벤트 로깅 | shadow-py | 낮음 |
| 8-9 | Claude API로 행동 라벨링 | VLM 분석 결과 | shadow-py | 높음 |
| 9-10 | 세션 시퀀스 구성 | 행동들이 세션으로 그룹화 | shadow-py | 낮음 |
| 10-11 | LLM 패턴 감지 | 패턴 후보 생성 | shadow-py | 높음 |
| 11-12 | HITL 질문 생성 | 질문 객체 | shadow-py | 중간 |
| 12-13 | Slack 질문 전송 (블록 UI) | 실제 Slack 메시지 | shadow-web | 중간 |
| 13-14 | Slack 응답 수신 + shadow-py 전달 | 응답 처리 | shadow-web | 중간 |
| 14-15 | 명세서 생성 + 저장 | spec.json 파일 | shadow-py | 낮음 |
| 15-16 | 통합 테스트, 버그 수정 | E2E Pass | both | 높음 |
| 16-17 | 데모 시나리오 실행 연습 | 데모 스크립트 | both | 낮음 |
| 17-18 | 발표 자료, 최종 점검 | 발표 준비 완료 | both | 낮음 |

### 6.4 리스크 완화

| 리스크 | 확률 | 영향 | 완화 방안 |
| --- | --- | --- | --- |
| VLM 프롬프트 튜닝 지연 | 높음 | 높음 | 사전 정의된 템플릿 사용, 튜닝 시간 1시간 제한 |
| 서비스 간 통신 문제 | 중간 | 높음 | Hour 4-5에 조기 검증 |
| Slack API 연동 문제 | 중간 | 높음 | Hour 5-6에 조기 검증, 실패 시 CLI fallback |
| 패턴 감지 품질 부족 | 높음 | 중간 | 데모 시나리오를 단순화하여 확실히 동작하게 |
| 시간 부족 | 중간 | 높음 | P1 기능 과감히 스킵, P0만 집중 |

---

## 7. 기술 스택

| 구분 | 기술 | 용도 | 담당 |
| --- | --- | --- | --- |
| 화면 캡처 | mss | Before/After 스크린샷 | shadow-py |
| 입력 로깅 | pynput | 마우스 클릭 이벤트 | shadow-py |
| VLM | Claude Opus 4.5 | 행동 라벨링 | shadow-py |
| LLM | Claude Opus 4.5 | 패턴 감지, 질문 생성 | shadow-py |
| Slack | @slack/web-api | HITL 대화 | shadow-web |
| 저장 | 로컬 파일 시스템 | spec.json, 이벤트 로그 | shadow-py |
| DB | Supabase (PostgreSQL) | Slack 이벤트, HITL 응답 | shadow-web |
| Framework | FastAPI | REST API 서버 | shadow-py |
| Framework | Next.js 14 | API Routes | shadow-web |

---

## 8. 환경변수

### 8.1 shadow-py

```bash
# 필수
ANTHROPIC_API_KEY=sk-ant-...          # Claude API Key
SHADOW_WEB_URL=http://localhost:3000  # shadow-web URL

# 선택
API_HOST=0.0.0.0
API_PORT=8000
CAPTURE_OUTPUT_DIR=./output
AFTER_CAPTURE_DELAY_MS=300

```

### 8.2 shadow-web

```bash
# 필수
SLACK_BOT_TOKEN=xoxb-...              # Bot User OAuth Token
SLACK_SIGNING_SECRET=...              # Signing Secret
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

# 선택
SHADOW_PY_API_URL=http://localhost:8000

```

---

## 9. 산출물: 에이전트 명세서

Shadow가 생성하는 **spec.json**의 핵심 구조:

```
spec.json
├── meta: 이름, 버전, 생성일
├── trigger: 언제 이 업무가 시작되는가
├── workflow: 어떤 단계로 진행되는가
├── decisions: 판단 기준 (HITL로 확인된 규칙)
├── boundaries: always_do / ask_first / never_do
├── quality: 결과물 필수 요소
└── exceptions: 예외 처리

```

**MVP에서 필수 생성 필드:**

- meta.name, meta.version
- workflow.steps (기본 시퀀스)
- decisions.rules (HITL 응답으로 확인된 규칙)

상세 스키마는 별도 문서(shadow-spec-schema.md) 참조.

---

## Changelog

| 버전 | 날짜 | 변경 내용 |
| --- | --- | --- |
| 1.0 | 2026-01-31 | 초안 (템플릿 기반) |
| 2.0 | 2026-01-31 | 해커톤용 재구성: 페르소나/Epic 삭제, 기능명세 통합, Pass/Fail 기준 명확화, AI 전달 최적화 |
| **3.0** | **2026-01-31** | **아키텍처 분리 반영: shadow-py (Python) + shadow-web (TypeScript) 2개 서비스 구성, F-07/F-08 담당을 shadow-web으로 이관, 서비스 간 통신 API 추가, 환경변수 분리** |