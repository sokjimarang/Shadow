# Shadow - 에이전트 명세서 스키마

**버전: v1.1
작성일: 2026-01-31**

---

## 1. 개요

이 문서는 Shadow가 생성하는 **에이전트 명세서(Agent Spec)**의 상세 구조를 정의한다.

에이전트 명세서는 AI 에이전트가 특정 업무를 수행하기 위해 필요한 모든 정보를 담고 있으며, 다음 원칙을 따른다:

- **Progressive Disclosure**: 필요한 정보만 단계적으로 로드
- **Human Readable**: 사람이 읽고 이해할 수 있는 구조
- **Machine Executable**: AI 에이전트가 파싱하고 실행할 수 있는 형식
- **Version Controlled**: 모든 변경 이력 추적 가능

---

## 2. 파일 구조

```
~/.shadow/specs/{spec_id}/
├── spec.json              # 메인 명세서
├── history.jsonl          # 변경 이력
└── examples/              # 실제 관찰 예시
    ├── example_001.json
    └── example_002.json

```

---

## 3. 메인 스키마 (spec.json)

### 3.1 전체 구조

```json
{
  "meta": { ... },
  "trigger": { ... },
  "workflow": { ... },
  "decisions": { ... },
  "boundaries": { ... },
  "quality": { ... },
  "exceptions": [ ... ],
  "tools": [ ... ]
}

```

### 3.2 상세 스키마

### meta (메타데이터)

명세서의 기본 정보

```json
{
  "meta": {
    "id": "spec_uuid_here",
    "pattern_id": "pattern_uuid_here",
    "name": "이메일 → 스프레드시트 복사",
    "description": "Gmail에서 주문 정보를 추출하여 Google Sheets에 정리하는 업무",
    "version": "1.2.0",
    "created_at": "2025-01-31T10:00:00Z",
    "updated_at": "2025-01-31T14:30:00Z",
    "observation_count": 5,
    "confidence_score": 0.85,
    "status": "active"
  }
}

```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | ✓ | 명세서 고유 ID |
| pattern_id | string | ✓ | 원본 패턴 ID |
| name | string | ✓ | 명세서 이름 |
| description | string | ✓ | 업무 설명 |
| version | string | ✓ | 버전 (semver) |
| created_at | datetime | ✓ | 생성 시각 |
| updated_at | datetime | ✓ | 수정 시각 |
| observation_count | int | ✓ | 관찰 횟수 |
| confidence_score | float | ✓ | 전체 확신도 (0.0-1.0) |
| status | enum | ✓ | "draft" | "active" | "archived" |

---

### trigger (트리거)

업무가 시작되는 조건

```json
{
  "trigger": {
    "description": "Gmail에서 @supplier.com 발신자의 이메일을 열 때",
    "conditions": [
      {
        "type": "app_active",
        "app": "Gmail",
        "context": "email_view"
      },
      {
        "type": "content_match",
        "field": "sender",
        "pattern": "*@supplier.com"
      }
    ],
    "operator": "AND"
  }
}

```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| description | string | ✓ | 자연어 설명 |
| conditions | array | ✓ | 조건 목록 |
| operator | enum | ✓ | "AND" | "OR" |

**Condition 타입:**

| type | 설명 | 필요 필드 |
| --- | --- | --- |
| app_active | 특정 앱 활성화 | app, context (optional) |
| content_match | 콘텐츠 매칭 | field, pattern |
| time_based | 시간 기반 | schedule |
| manual | 수동 트리거 | - |

---

### workflow (워크플로우)

업무의 단계별 절차

```json
{
  "workflow": {
    "description": "이메일에서 정보 추출 후 스프레드시트에 입력",
    "steps": [
      {
        "order": 1,
        "id": "step_extract",
        "action": "extract_text",
        "target": "email_body",
        "app": "Gmail",
        "description": "이메일 본문에서 주문 정보 추출",
        "output": "order_info",
        "is_variable": false
      },
      {
        "order": 2,
        "id": "step_switch",
        "action": "switch_app",
        "target": "Google Sheets",
        "app": null,
        "description": "스프레드시트로 이동",
        "output": null,
        "is_variable": false
      },
      {
        "order": 3,
        "id": "step_find_row",
        "action": "find_empty_row",
        "target": "column_A",
        "app": "Google Sheets",
        "description": "비어있는 행 찾기",
        "output": "target_row",
        "is_variable": false
      },
      {
        "order": 4,
        "id": "step_input",
        "action": "input_data",
        "target": "{target_row}",
        "app": "Google Sheets",
        "description": "추출한 정보 입력",
        "input": "order_info",
        "output": null,
        "is_variable": true
      }
    ]
  }
}

```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| description | string | ✓ | 워크플로우 설명 |
| steps | array | ✓ | Step 배열 |

**Step 구조:**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| order | int | ✓ | 순서 |
| id | string | ✓ | 단계 ID |
| action | string | ✓ | 행동 타입 |
| target | string | ✓ | 대상 |
| app | string |  | 앱 이름 |
| description | string | ✓ | 설명 |
| input | string |  | 입력 변수명 |
| output | string |  | 출력 변수명 |
| is_variable | boolean | ✓ | 가변 요소 여부 |

**Action 타입:**

| action | 설명 |
| --- | --- |
| extract_text | 텍스트 추출 |
| switch_app | 앱 전환 |
| click | 클릭 |
| type | 텍스트 입력 |
| copy | 복사 |
| paste | 붙여넣기 |
| find_empty_row | 빈 행 찾기 |
| input_data | 데이터 입력 |
| scroll | 스크롤 |
| wait | 대기 |

---

### decisions (판단 기준)

선택이 필요한 순간의 기준

```json
{
  "decisions": {
    "description": "데이터 처리 시 적용되는 판단 기준",
    "rules": [
      {
        "id": "rule_highlight",
        "condition": "order_info.amount > 500000",
        "action": "highlight_yellow",
        "description": "금액 50만원 초과 시 노란색 하이라이트",
        "source": "user_confirmed",
        "confirmed_at": "2025-01-31T14:00:00Z",
        "confidence": 1.0
      },
      {
        "id": "rule_urgent",
        "condition": "order_info.amount > 1000000",
        "action": "mark_urgent",
        "description": "금액 100만원 초과 시 긴급 표시",
        "source": "user_confirmed",
        "confirmed_at": "2025-01-31T14:05:00Z",
        "confidence": 1.0
      },
      {
        "id": "rule_column",
        "condition": "order_info.type == 'domestic'",
        "action": "use_column_C",
        "else_action": "use_column_D",
        "description": "국내 주문은 C열, 해외 주문은 D열",
        "source": "inferred",
        "confidence": 0.7
      }
    ]
  }
}

```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| description | string | ✓ | 판단 기준 설명 |
| rules | array | ✓ | Rule 배열 |

**Rule 구조:**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | ✓ | 규칙 ID |
| condition | string | ✓ | 조건 (표현식) |
| action | string | ✓ | 참일 때 행동 |
| else_action | string |  | 거짓일 때 행동 |
| description | string | ✓ | 설명 |
| source | enum | ✓ | "user_confirmed" | "inferred" |
| confirmed_at | datetime |  | 확인 시각 |
| confidence | float | ✓ | 확신도 |

---

### boundaries (경계 조건)

해야 할 것 / 하지 말아야 할 것

```json
{
  "boundaries": {
    "always_do": [
      {
        "id": "always_1",
        "description": "새 행에 입력 (기존 데이터 덮어쓰기 금지)",
        "source": "inferred"
      },
      {
        "id": "always_2",
        "description": "날짜 형식은 YYYY-MM-DD 유지",
        "source": "user_confirmed"
      }
    ],
    "ask_first": [
      {
        "id": "ask_1",
        "condition": "order_info.amount > 1000000",
        "description": "100만원 초과 주문은 처리 전 확인",
        "source": "user_confirmed"
      },
      {
        "id": "ask_2",
        "condition": "sender not in known_senders",
        "description": "새로운 발신자의 이메일은 확인 필요",
        "source": "user_confirmed"
      }
    ],
    "never_do": [
      {
        "id": "never_1",
        "description": "기존 데이터 삭제 금지",
        "source": "inferred"
      },
      {
        "id": "never_2",
        "description": "다른 시트 접근 금지",
        "source": "inferred"
      }
    ]
  }
}

```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| always_do | array | ✓ | 항상 해야 할 것 |
| ask_first | array | ✓ | 확인이 필요한 것 |
| never_do | array | ✓ | 절대 하면 안 되는 것 |

**Boundary Item 구조:**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | ✓ | 항목 ID |
| condition | string |  | 조건 (ask_first만) |
| description | string | ✓ | 설명 |
| source | enum | ✓ | "user_confirmed" | "inferred" |

---

### quality (품질 기준)

결과물이 갖춰야 할 조건

```json
{
  "quality": {
    "description": "완료된 작업의 품질 기준",
    "required_fields": [
      {
        "field": "date",
        "description": "날짜 필수",
        "format": "YYYY-MM-DD"
      },
      {
        "field": "order_number",
        "description": "주문번호 필수",
        "format": null
      },
      {
        "field": "amount",
        "description": "금액 필수",
        "format": "number"
      }
    ],
    "validations": [
      {
        "field": "amount",
        "rule": "positive_number",
        "description": "금액은 양수여야 함"
      },
      {
        "field": "date",
        "rule": "not_future",
        "description": "미래 날짜 불가"
      }
    ],
    "completeness_check": {
      "min_fields": 3,
      "required_fields": ["date", "order_number", "amount"]
    }
  }
}

```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| description | string | ✓ | 품질 기준 설명 |
| required_fields | array | ✓ | 필수 필드 목록 |
| validations | array |  | 검증 규칙 |
| completeness_check | object |  | 완료 조건 |

---

### exceptions (예외 처리)

예상과 다른 상황의 처리 방법

```json
{
  "exceptions": [
    {
      "id": "exc_1",
      "condition": "email has attachment only (no body text)",
      "action": "skip",
      "description": "첨부파일만 있는 이메일은 건너뛰기",
      "source": "user_confirmed"
    },
    {
      "id": "exc_2",
      "condition": "spreadsheet is read-only",
      "action": "notify_user",
      "description": "스프레드시트가 읽기 전용이면 사용자에게 알림",
      "source": "inferred"
    },
    {
      "id": "exc_3",
      "condition": "amount is negative",
      "action": "flag_for_review",
      "description": "음수 금액은 검토 표시",
      "source": "user_confirmed"
    }
  ]
}

```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | ✓ | 예외 ID |
| condition | string | ✓ | 조건 |
| action | string | ✓ | 처리 방법 |
| description | string | ✓ | 설명 |
| source | enum | ✓ | "user_confirmed" | "inferred" | "observed" |

**Action 타입:**

| action | 설명 |
| --- | --- |
| skip | 건너뛰기 |
| notify_user | 사용자에게 알림 |
| flag_for_review | 검토 표시 |
| retry | 재시도 |
| fallback | 대체 행동 실행 |

---

### tools (필요 도구)

업무 수행에 필요한 앱/API

```json
{
  "tools": [
    {
      "type": "app",
      "name": "Gmail",
      "required": true,
      "permissions": ["read_email"]
    },
    {
      "type": "app",
      "name": "Google Sheets",
      "required": true,
      "permissions": ["read_write"]
    }
  ]
}

```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| type | enum | ✓ | "app" | "api" | "service" |
| name | string | ✓ | 도구 이름 |
| required | boolean | ✓ | 필수 여부 |
| permissions | array |  | 필요 권한 |

---

## 4. 전체 예시

```json
{
  "meta": {
    "id": "spec_001",
    "pattern_id": "pattern_001",
    "name": "이메일 → 스프레드시트 복사",
    "description": "Gmail에서 주문 정보를 추출하여 Google Sheets에 정리하는 업무",
    "version": "1.2.0",
    "created_at": "2025-01-31T10:00:00Z",
    "updated_at": "2025-01-31T14:30:00Z",
    "observation_count": 5,
    "confidence_score": 0.85,
    "status": "active"
  },

  "trigger": {
    "description": "Gmail에서 @supplier.com 발신자의 이메일을 열 때",
    "conditions": [
      { "type": "app_active", "app": "Gmail", "context": "email_view" },
      { "type": "content_match", "field": "sender", "pattern": "*@supplier.com" }
    ],
    "operator": "AND"
  },

  "workflow": {
    "description": "이메일에서 정보 추출 후 스프레드시트에 입력",
    "steps": [
      { "order": 1, "id": "step_1", "action": "extract_text", "target": "email_body", "app": "Gmail", "description": "주문 정보 추출", "output": "order_info", "is_variable": false },
      { "order": 2, "id": "step_2", "action": "switch_app", "target": "Google Sheets", "app": null, "description": "스프레드시트로 이동", "output": null, "is_variable": false },
      { "order": 3, "id": "step_3", "action": "find_empty_row", "target": "column_A", "app": "Google Sheets", "description": "빈 행 찾기", "output": "target_row", "is_variable": false },
      { "order": 4, "id": "step_4", "action": "input_data", "target": "{target_row}", "app": "Google Sheets", "description": "정보 입력", "input": "order_info", "output": null, "is_variable": true }
    ]
  },

  "decisions": {
    "description": "금액 기반 처리 규칙",
    "rules": [
      { "id": "rule_1", "condition": "order_info.amount > 500000", "action": "highlight_yellow", "description": "50만원 초과 시 노란색", "source": "user_confirmed", "confidence": 1.0 },
      { "id": "rule_2", "condition": "order_info.amount > 1000000", "action": "mark_urgent", "description": "100만원 초과 시 긴급", "source": "user_confirmed", "confidence": 1.0 }
    ]
  },

  "boundaries": {
    "always_do": [
      { "id": "always_1", "description": "새 행에 입력", "source": "inferred" },
      { "id": "always_2", "description": "날짜 형식 YYYY-MM-DD", "source": "user_confirmed" }
    ],
    "ask_first": [
      { "id": "ask_1", "condition": "order_info.amount > 1000000", "description": "100만원 초과 시 확인", "source": "user_confirmed" }
    ],
    "never_do": [
      { "id": "never_1", "description": "기존 데이터 삭제 금지", "source": "inferred" }
    ]
  },

  "quality": {
    "description": "필수 필드 및 검증",
    "required_fields": [
      { "field": "date", "description": "날짜", "format": "YYYY-MM-DD" },
      { "field": "order_number", "description": "주문번호", "format": null },
      { "field": "amount", "description": "금액", "format": "number" }
    ],
    "validations": [
      { "field": "amount", "rule": "positive_number", "description": "양수" }
    ],
    "completeness_check": { "min_fields": 3, "required_fields": ["date", "order_number", "amount"] }
  },

  "exceptions": [
    { "id": "exc_1", "condition": "attachment_only", "action": "skip", "description": "첨부만 있으면 스킵", "source": "user_confirmed" }
  ],

  "tools": [
    { "type": "app", "name": "Gmail", "required": true, "permissions": ["read_email"] },
    { "type": "app", "name": "Google Sheets", "required": true, "permissions": ["read_write"] }
  ]
}

```

---

## 5. 변경 이력 스키마 (history.jsonl)

각 줄이 하나의 변경 기록 (JSON Lines 형식)

```json
{"id":"hist_001","version":"1.0.0","previous_version":null,"change_type":"create","summary":"최초 생성","changes":[],"source":"pattern_detection","source_id":"pattern_001","timestamp":"2025-01-31T10:00:00Z"}
{"id":"hist_002","version":"1.1.0","previous_version":"1.0.0","change_type":"update","summary":"판단 기준 추가: 50만원 초과 시 노란색","changes":[{"path":"decisions.rules","operation":"add","value":{"id":"rule_1","condition":"amount > 500000"}}],"source":"hitl_answer","source_id":"answer_001","timestamp":"2025-01-31T12:00:00Z"}
{"id":"hist_003","version":"1.2.0","previous_version":"1.1.0","change_type":"update","summary":"예외 조건 추가: 첨부만 있으면 스킵","changes":[{"path":"exceptions","operation":"add","value":{"id":"exc_1","condition":"attachment_only"}}],"source":"hitl_answer","source_id":"answer_002","timestamp":"2025-01-31T14:30:00Z"}

```

---

## 6. 예시 데이터 스키마 (examples/)

실제 관찰된 예시 저장

```json
{
  "id": "example_001",
  "spec_id": "spec_001",
  "session_id": "session_001",
  "timestamp": "2025-01-31T11:00:00Z",
  "actions": [
    {
      "step_id": "step_1",
      "actual_action": "Gmail에서 'ORD-2025-001' 주문 이메일 열기",
      "screenshot_thumbnail": "base64...",
      "extracted_data": { "order_number": "ORD-2025-001", "amount": 750000 }
    }
  ],
  "outcome": "success",
  "notes": "50만원 초과로 노란색 하이라이트 적용됨"
}

```

---

*문서 끝*