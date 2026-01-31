# Shadow - 데이터 스키마

**버전: v1.1
작성일: 2026-01-31**

---

## 1. 개요

이 문서는 Shadow 시스템에서 사용하는 모든 데이터 엔티티와 그 관계를 정의한다.

---

## 2. 엔티티 관계도

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              데이터 흐름                                     │
└─────────────────────────────────────────────────────────────────────────────┘

[Raw Data Layer]
    │
    ├── Screenshot ─────┐
    │                   │
    └── InputEvent ─────┼──→ RawObservation
                        │
                        ▼
[Analysis Layer]
    │
    └── LabeledAction ──┬──→ SessionSequence
                        │
                        ▼
[Pattern Layer]
    │
    └── DetectedPattern ─┬──→ Uncertainty
                         │
                         ▼
[HITL Layer]
    │
    ├── HITLQuestion ───┬──→ HITLAnswer ──→ InterpretedAnswer
    │                   │
    │                   ▼
[Spec Layer]
    │
    └── AgentSpec ──────┬──→ SpecVersion
                        │
                        └──→ SpecHistory

```

---

## 3. 엔티티 정의

### 3.1 Raw Data Layer

### Screenshot

화면 캡처 데이터

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| timestamp | datetime | ✓ | 캡처 시각 |
| type | enum | ✓ | "before" | "after" |
| data | base64 | ✓ | 원본 이미지 (분석 후 삭제) |
| thumbnail | base64 | ✓ | 썸네일 이미지 (보관) |
| resolution | object | ✓ | { width, height } |
| trigger_event_id | string | ✓ | 트리거된 이벤트 ID |
| session_id | string | ✓ | 세션 ID |

### InputEvent

입력 이벤트 데이터

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| timestamp | datetime | ✓ | 이벤트 발생 시각 |
| type | enum | ✓ | "mouse_click" | "mouse_move" | "key_press" | "key_release" | "scroll" |
| position | object |  | { x, y } - 마우스 이벤트 |
| button | enum |  | "left" | "right" | "middle" |
| click_type | enum |  | "single" | "double" |
| key | string |  | 입력된 키 |
| modifiers | array |  | ["ctrl", "alt", "shift", "cmd"] |
| active_window | object | ✓ | { title, app_name, app_bundle_id } |
| session_id | string | ✓ | 세션 ID |

### RawObservation

원시 관찰 데이터 (Screenshot + InputEvent 묶음)

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| session_id | string | ✓ | 세션 ID |
| timestamp | datetime | ✓ | 관찰 시각 |
| before_screenshot_id | string | ✓ | Before 스크린샷 ID |
| after_screenshot_id | string | ✓ | After 스크린샷 ID |
| event_id | string | ✓ | 입력 이벤트 ID |

---

### 3.2 Analysis Layer

### LabeledAction

라벨링된 행동

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| observation_id | string | ✓ | 원시 관찰 데이터 ID |
| timestamp | datetime | ✓ | 행동 시각 |
| action_type | enum | ✓ | "click" | "type" | "copy" | "paste" | "scroll" | "navigate" | "select" |
| target_element | string | ✓ | 대상 요소 (예: "search_bar") |
| app | string | ✓ | 앱 이름 |
| app_context | string |  | 앱 내 컨텍스트 (예: "inbox") |
| semantic_label | string | ✓ | 자연어 설명 |
| intent_guess | string |  | 추측 의도 |
| confidence | float | ✓ | 0.0 - 1.0 |
| session_id | string | ✓ | 세션 ID |

### SessionSequence

세션 내 행동 시퀀스

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| session_id | string | ✓ | 세션 ID |
| start_time | datetime | ✓ | 시작 시각 |
| end_time | datetime |  | 종료 시각 |
| action_ids | array | ✓ | LabeledAction ID 배열 (순서대로) |
| apps_used | array | ✓ | 사용된 앱 목록 |
| action_count | int | ✓ | 행동 수 |
| status | enum | ✓ | "recording" | "completed" | "analyzed" |

---

### 3.3 Pattern Layer

### DetectedPattern

감지된 패턴

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| name | string | ✓ | 패턴 이름 (자동 생성) |
| description | string |  | 패턴 설명 |
| core_sequence | array | ✓ | ActionTemplate 배열 |
| apps_involved | array | ✓ | 관련 앱 목록 |
| occurrences | int | ✓ | 발생 횟수 |
| first_seen | datetime | ✓ | 최초 발견 시각 |
| last_seen | datetime | ✓ | 최근 발견 시각 |
| session_ids | array | ✓ | 관련 세션 ID 목록 |
| variations | array |  | Variation 배열 |
| uncertainties | array |  | Uncertainty 배열 |
| status | enum | ✓ | "detected" | "confirming" | "confirmed" | "rejected" |
| confidence | float | ✓ | 0.0 - 1.0 |
| spec_id | string |  | 연결된 명세서 ID |

### ActionTemplate

패턴 내 행동 템플릿

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| order | int | ✓ | 순서 |
| action_type | string | ✓ | 행동 타입 |
| target_pattern | string | ✓ | 대상 패턴 (정규식 또는 설명) |
| app | string | ✓ | 앱 이름 |
| is_variable | boolean | ✓ | 가변 요소 여부 |
| description | string |  | 설명 |

### Variation

패턴 변형

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | ✓ | 고유 식별자 |
| description | string | ✓ | 변형 설명 |
| occurrence_rate | float | ✓ | 발생 비율 (0.0 - 1.0) |
| example_session_id | string | ✓ | 예시 세션 ID |
| differs_at | array |  | 다른 부분 인덱스 |

### Uncertainty

불확실 지점

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | ✓ | 고유 식별자 |
| type | enum | ✓ | "condition" | "exception" | "quality" | "alternative" |
| description | string | ✓ | 불확실 지점 설명 |
| hypothesis | string |  | AI 가설 |
| related_action_indices | array |  | 관련 행동 인덱스 |
| resolved | boolean | ✓ | 해결 여부 |
| resolution | string |  | 해결 내용 |

---

### 3.4 HITL Layer

### HITLQuestion

HITL 질문

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| pattern_id | string | ✓ | 관련 패턴 ID |
| uncertainty_id | string | ✓ | 관련 Uncertainty ID |
| type | enum | ✓ | "anomaly" | "alternative" | "hypothesis" | "quality" |
| question_text | string | ✓ | 질문 내용 |
| context | string |  | 배경 설명 |
| options | array | ✓ | QuestionOption 배열 |
| allows_freetext | boolean | ✓ | 자유 텍스트 허용 여부 |
| priority | int | ✓ | 우선순위 (1-5) |
| status | enum | ✓ | "pending" | "sent" | "answered" | "expired" |
| created_at | datetime | ✓ | 생성 시각 |
| sent_at | datetime |  | 전송 시각 |
| answered_at | datetime |  | 응답 시각 |
| slack_message_ts | string |  | Slack 메시지 타임스탬프 |

### QuestionOption

질문 옵션

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | ✓ | 옵션 ID |
| label | string | ✓ | 표시 텍스트 |
| action | string | ✓ | 시스템 취할 행동 |
| is_default | boolean |  | 기본값 여부 |

### HITLAnswer

HITL 응답

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| question_id | string | ✓ | 질문 ID |
| response_type | enum | ✓ | "button" | "freetext" |
| selected_option_id | string |  | 선택된 옵션 ID |
| freetext | string |  | 자유 텍스트 응답 |
| user_id | string | ✓ | 응답자 ID |
| timestamp | datetime | ✓ | 응답 시각 |

### InterpretedAnswer

해석된 응답

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| answer_id | string | ✓ | 원본 응답 ID |
| action | enum | ✓ | "add_rule" | "add_exception" | "set_quality" | "reject" | "needs_clarification" |
| spec_update | object |  | { path, operation, value } |
| confidence | float | ✓ | 해석 확신도 |
| applied | boolean | ✓ | 명세서 반영 여부 |
| applied_at | datetime |  | 반영 시각 |

---

### 3.5 Spec Layer

### AgentSpec

에이전트 명세서 (상세 스키마는 별도 문서)

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| pattern_id | string | ✓ | 원본 패턴 ID |
| version | string | ✓ | 버전 (semver) |
| created_at | datetime | ✓ | 최초 생성 시각 |
| updated_at | datetime | ✓ | 최종 수정 시각 |
| status | enum | ✓ | "draft" | "active" | "archived" |
| content | object | ✓ | 명세서 내용 (별도 스키마) |

### SpecHistory

명세서 변경 이력

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| spec_id | string | ✓ | 명세서 ID |
| version | string | ✓ | 변경된 버전 |
| previous_version | string |  | 이전 버전 |
| change_type | enum | ✓ | "create" | "update" | "delete" |
| change_summary | string | ✓ | 변경 요약 |
| changes | array | ✓ | 상세 변경 내역 |
| source | enum | ✓ | "pattern_detection" | "hitl_answer" | "manual" |
| source_id | string |  | 소스 ID (answer_id 등) |
| timestamp | datetime | ✓ | 변경 시각 |

---

### 3.6 System Layer

### Session

관찰 세션

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| user_id | string | ✓ | 사용자 ID |
| start_time | datetime | ✓ | 시작 시각 |
| end_time | datetime |  | 종료 시각 |
| status | enum | ✓ | "active" | "paused" | "completed" |
| event_count | int | ✓ | 이벤트 수 |
| observation_count | int | ✓ | 관찰 수 |

### User

사용자

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string (UUID) | ✓ | 고유 식별자 |
| slack_user_id | string | ✓ | Slack 사용자 ID |
| slack_channel_id | string | ✓ | DM 채널 ID |
| created_at | datetime | ✓ | 가입 시각 |
| settings | object |  | 사용자 설정 |

### Config

시스템 설정

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| user_id | string | ✓ | 사용자 ID |
| excluded_apps | array |  | 제외 앱 목록 |
| capture_interval_ms | int |  | 캡처 간격 |
| min_pattern_occurrences | int |  | 패턴 최소 횟수 (기본: 3) |
| hitl_max_questions | int |  | 한 번에 최대 질문 수 |

---

## 4. 데이터 흐름

### 4.1 수집 → 분석 흐름

```
1. InputEvent 발생
   ↓
2. Screenshot (Before/After) 캡처
   ↓
3. RawObservation 생성
   ↓
4. VLM 분석
   ↓
5. LabeledAction 생성
   ↓
6. SessionSequence에 추가

```

### 4.2 패턴 감지 흐름

```
1. SessionSequence 여러 개 수집
   ↓
2. LLM 패턴 분석
   ↓
3. DetectedPattern 생성/업데이트
   ↓
4. Uncertainty 식별
   ↓
5. 3회 이상이면 HITL 진입

```

### 4.3 HITL 흐름

```
1. Uncertainty에서 HITLQuestion 생성
   ↓
2. Slack으로 전송
   ↓
3. HITLAnswer 수신
   ↓
4. InterpretedAnswer 생성
   ↓
5. AgentSpec 업데이트
   ↓
6. SpecHistory 기록

```

---

## 5. 저장소 구조

### 5.1 파일 시스템 (로컬)

```
~/.shadow/
├── config.json              # 사용자 설정
├── sessions/
│   └── {session_id}/
│       ├── events.jsonl     # InputEvent 스트림
│       ├── screenshots/     # 썸네일만 보관
│       └── observations.jsonl
├── patterns/
│   └── {pattern_id}.json
├── specs/
│   ├── index.json           # 명세서 목록
│   └── {spec_id}/
│       ├── spec.json        # 현재 버전
│       └── history.jsonl    # 변경 이력
├── hitl/
│   ├── questions.jsonl
│   └── answers.jsonl
└── logs/
    └── shadow.log

```

### 5.2 데이터 보존 정책

| 데이터 | 보존 기간 | 비고 |
| --- | --- | --- |
| 원본 스크린샷 | 즉시 삭제 | 분석 완료 후 |
| 썸네일 | 7일 | 디버깅용 |
| InputEvent | 30일 | 압축 보관 |
| LabeledAction | 90일 |  |
| SessionSequence | 90일 |  |
| DetectedPattern | 영구 |  |
| AgentSpec | 영구 |  |
| SpecHistory | 영구 |  |

---

*문서 끝*