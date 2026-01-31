# 시나리오 2: CS 담당자의 고객 문의 처리 자동화

**버전: v2.0**  
**작성일: 2026-02-01**

---

## 1. 페르소나

### 1.1 기본 정보

| 항목 | 내용 |
|------|------|
| **역할** | CS (Customer Success) 담당자 |
| **회사 규모** | 50-200명 스타트업/중소기업 |
| **업무 경력** | 1-3년차 |
| **팀 구성** | CS팀 3-5명, 개발팀/운영팀과 협업 |

### 1.2 업무 컨텍스트

| 항목 | 내용 |
|------|------|
| **주요 업무** | 고객 문의 분류, 답변, 에스컬레이션 판단 |
| **일일 처리량** | 30-50건의 티켓 |
| **문의 유형** | 사용법 40%, 환불/결제 25%, 버그 신고 20%, 기타 15% |
| **사용 도구** | Zendesk, Notion (헬프센터), Slack |

### 1.3 Pain Points

1. **반복 답변**: 문의의 50%가 FAQ나 헬프센터에 이미 있는 내용
2. **에스컬레이션 기준 모호**: "이건 내가 처리해도 되나?" 매번 고민
3. **개발팀 문의 지연**: Slack으로 물어봐야 하는데 답변이 늦음
4. **톤 조절 어려움**: 화난 고객 vs 일반 문의 대응 기준이 암묵적

### 1.4 왜 AI가 필요한가

| 요소 | 설명 |
|------|------|
| **자연어 이해** | "환불해주세요" vs "이거 왜 안돼요" vs "사기 아니에요?" 구분 |
| **감정 분석** | 고객의 감정 상태 파악 → 톤 조절 |
| **다중 소스 통합** | Zendesk 티켓 + Notion 문서 + Slack 팀 답변 종합 |
| **암묵적 규칙** | "제품 불량 환불은 금액 상관없이 팀장 보고" 같은 룰 |

---

## 2. 시나리오 흐름

### 2.1 트리거 상황

> Zendesk에 새 티켓이 들어옴:
> 
> **제목**: 결제했는데 구독이 안 돼요!!!
> **내용**: "어제 연간 구독 결제했는데 아직도 무료 버전이에요. 돈만 빠져나가고 사기 아닌가요?? 빨리 해결해주세요"
> **고객 정보**: 3회 문의 이력, VIP 아님

### 2.2 현재 CS 담당자의 행동 패턴 (Shadow가 관찰)

```
1. Zendesk에서 새 티켓 열기 (5초)
2. 티켓 내용 읽기 - 감정 상태 파악 (15초)
   → "화난 고객이네, 사과로 시작해야겠다"
3. Notion 헬프센터로 이동, "구독 결제" 검색 (20초)
4. "결제 후 구독 미반영" 문서 찾아서 확인 (30초)
   → "보통 24시간 내 반영인데, 수동 처리가 필요할 수도"
5. Slack #cs-dev 채널로 이동 (10초)
6. 개발팀에 확인 요청 메시지 작성 (40초)
   → "티켓 #4521 고객, 어제 결제했는데 구독 미반영. 수동 처리 필요한가요?"
7. (개발팀 응답 대기 - 10분)
8. 응답 확인: "DB 확인해보니 결제는 됐는데 구독 플래그가 안 바뀌었네요. 수동으로 바꿔드렸습니다"
9. Zendesk로 돌아와 답변 작성 (60초)
   → 사과 문구 + 해결 완료 + 보상 제안
10. 티켓 카테고리/태그 지정 (10초)
```

**총 소요 시간: 약 13분 (대기 시간 포함)**

### 2.3 앱 전환 흐름 (3개 앱)

```
[Zendesk] ──티켓 확인──→ [Notion] ──문서 검색──→ [Slack] ──팀 문의──→ [Zendesk]
    │                       │                      │                    │
    │                       │                      │                    │
    ▼                       ▼                      ▼                    ▼
 티켓 읽기              헬프센터 검색           개발팀 확인           답변 작성
 감정 파악              해결 방법 찾기          기술적 확인           톤 조절
 분류 판단              정책 확인               상태 확인             태그 지정
```

---

## 3. Shadow 데이터 흐름

### 3.1 OBSERVE (관찰)

**수집 이벤트 시퀀스:**

| 순서 | 앱 | 행동 | 캡처 데이터 |
|------|-----|------|------------|
| 1 | Zendesk | 티켓 클릭 | 티켓 내용, 고객 정보 |
| 2 | Zendesk | 스크롤 (내용 읽기) | 체류 시간: 15초 |
| 3 | Chrome | Notion 탭 클릭 | 앱 전환 |
| 4 | Notion | 검색창 클릭 + 타이핑 | 검색어: "구독 결제" |
| 5 | Notion | 문서 클릭 | 문서명: "결제 후 구독 미반영 대응 가이드" |
| 6 | Notion | 스크롤 + 텍스트 선택 | 선택 영역: "수동 처리 요청 방법" |
| 7 | Slack | #cs-dev 채널 클릭 | 앱 전환 |
| 8 | Slack | 메시지 입력 | 내용: 티켓 번호 + 증상 + 질문 |
| 9 | Slack | 메시지 읽기 | 개발팀 응답 확인 |
| 10 | Zendesk | 답변 입력창 클릭 | 앱 전환 |
| 11 | Zendesk | 답변 타이핑 | 사과 + 해결 + 보상 |
| 12 | Zendesk | 카테고리 선택 | "결제/구독" |
| 13 | Zendesk | 전송 버튼 클릭 | 답변 완료 |

### 3.2 ANALYZE (분석)

**행동 라벨링 (VLM + LLM):**

```json
{
  "id": "action_cs_001",
  "observation_id": "obs_cs_001",
  "action_type": "read",
  "target_element": "ticket_content",
  "app": "Zendesk",
  "semantic_label": "티켓 내용 확인 - 결제 완료 but 구독 미반영 문의",
  "extracted_info": {
    "issue_type": "payment_subscription_mismatch",
    "customer_sentiment": "angry",
    "urgency": "high",
    "keywords": ["결제", "구독", "미반영", "사기"]
  }
}
```

**패턴 감지 (3회 관찰 후):**

```json
{
  "id": "pattern_cs_001",
  "name": "고객 문의 처리: Zendesk → Notion → Slack → Zendesk",
  "observation_count": 3,
  "core_sequence": [
    {"order": 1, "action": "read_ticket", "app": "Zendesk", "output": "ticket_info"},
    {"order": 2, "action": "analyze_sentiment", "app": "Zendesk", "output": "customer_sentiment"},
    {"order": 3, "action": "search", "app": "Notion", "input": "issue_keywords"},
    {"order": 4, "action": "read_document", "app": "Notion", "output": "solution_info"},
    {"order": 5, "action": "send_message", "app": "Slack", "condition": "needs_dev_confirmation"},
    {"order": 6, "action": "read_response", "app": "Slack", "output": "dev_response"},
    {"order": 7, "action": "compose_reply", "app": "Zendesk", "input": ["solution_info", "dev_response"]},
    {"order": 8, "action": "categorize", "app": "Zendesk"}
  ],
  "uncertainties": [
    {
      "type": "condition",
      "step": 5,
      "description": "언제 Slack으로 개발팀에 문의하는가?",
      "hypothesis": "기술적 확인이 필요하거나 수동 처리가 필요할 때"
    },
    {
      "type": "quality",
      "step": 7,
      "description": "화난 고객에게 어떻게 답변하는가?",
      "hypothesis": "사과 문구로 시작하고 보상 제안"
    },
    {
      "type": "condition",
      "description": "에스컬레이션 기준은?",
      "hypothesis": "환불 금액 10만원 이상 또는 법적 언급 시"
    }
  ]
}
```

### 3.3 CLARIFY (HITL 질문)

**질문 1 - Slack 문의 조건:**

```json
{
  "id": "question_cs_001",
  "type": "hypothesis",
  "question_text": "기술적 확인이 필요하거나 수동 처리가 필요할 때 Slack으로 개발팀에 문의하시는 것 같은데, 맞나요?",
  "context": "최근 10건의 티켓 중 4건에서 Slack으로 개발팀에 문의했습니다. 4건 모두 '시스템 오류', '수동 처리', 'DB 확인' 관련이었습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 기술적 확인이나 수동 처리가 필요할 때 문의합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "Notion에서 해결 방법을 못 찾았을 때 문의합니다", "action": "update_rule"},
    {"id": "opt_3", "label": "결제/구독 관련 문의는 항상 개발팀에 확인합니다", "action": "add_condition"}
  ]
}
```

**질문 2 - 감정 대응:**

```json
{
  "id": "question_cs_002",
  "type": "quality",
  "question_text": "고객이 화났을 때(욕설, 느낌표 다수, '사기' 등 표현) 답변을 사과 문구로 시작하시는 것 같은데, 맞나요?",
  "context": "최근 화난 고객 티켓 5건 중 5건 모두 '불편을 드려 죄송합니다'로 시작했습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 화난 고객에게는 항상 사과로 시작합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "회사 잘못이 명확할 때만 사과합니다", "action": "add_condition"},
    {"id": "opt_3", "label": "사과보다는 공감 표현('불편하셨겠네요')으로 시작합니다", "action": "update_rule"}
  ]
}
```

**질문 3 - 에스컬레이션:**

```json
{
  "id": "question_cs_003",
  "type": "hypothesis",
  "question_text": "환불 요청 중 '제품 불량'이 사유인 경우 금액과 상관없이 팀장님께 보고하시는 것 같은데, 맞나요?",
  "context": "최근 환불 요청 7건 중, 제품 불량 2건은 금액(3만원, 8만원)과 상관없이 팀장님께 공유했고, 단순 변심 5건 중 10만원 이상 1건만 공유했습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 제품 불량은 금액 상관없이 보고합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "제품 불량 + 금액 5만원 이상일 때 보고합니다", "action": "add_condition"},
    {"id": "opt_3", "label": "제품 불량이면 보고하고, 그 외에는 10만원 이상일 때 보고합니다", "action": "add_rule"}
  ]
}
```

### 3.4 PROCESS (응답 처리)

**사용자 응답:**

질문 1에 opt_1 선택, 질문 3에 opt_3 선택

```json
{
  "id": "answer_cs_003",
  "question_id": "question_cs_003",
  "selected_option_id": "opt_3",
  "timestamp": "2026-02-01T16:00:00Z"
}
```

**명세서 업데이트:**

```json
{
  "spec_update": {
    "path": "decisions.rules",
    "operation": "add",
    "value": {
      "id": "rule_escalation",
      "conditions": [
        {"if": "refund_reason == 'product_defect'", "then": "escalate"},
        {"if": "refund_reason != 'product_defect' && amount >= 100000", "then": "escalate"},
        {"else": "handle_directly"}
      ],
      "description": "제품 불량은 항상 에스컬레이션, 그 외에는 10만원 이상만",
      "source": "user_confirmed"
    }
  }
}
```

---

## 4. 생성되는 에이전트 명세서

```json
{
  "meta": {
    "id": "spec_cs_001",
    "name": "고객 문의 처리 자동화",
    "description": "Zendesk 티켓 분류, Notion 검색, Slack 팀 문의, 답변 생성",
    "version": "1.2.0",
    "status": "active"
  },

  "trigger": {
    "description": "Zendesk에 새 티켓이 할당되었을 때",
    "conditions": [
      {"type": "app_event", "app": "Zendesk", "event": "ticket_assigned"}
    ]
  },

  "workflow": {
    "description": "티켓 분석 → Notion 검색 → Slack 문의 → 답변 작성",
    "steps": [
      {
        "order": 1,
        "id": "step_read_ticket",
        "action": "read_content",
        "app": "Zendesk",
        "description": "티켓 내용 및 고객 정보 확인",
        "output": "ticket_info"
      },
      {
        "order": 2,
        "id": "step_analyze",
        "action": "analyze",
        "description": "문의 유형, 고객 감정, 긴급도 분석",
        "input": "ticket_info",
        "output": "analysis_result"
      },
      {
        "order": 3,
        "id": "step_check_escalation",
        "action": "evaluate_rules",
        "description": "에스컬레이션 필요 여부 판단",
        "input": "analysis_result",
        "output": "escalation_decision"
      },
      {
        "order": 4,
        "id": "step_search_notion",
        "action": "search",
        "app": "Notion",
        "description": "헬프센터에서 관련 문서 검색",
        "input": "analysis_result.keywords",
        "output": "notion_results"
      },
      {
        "order": 5,
        "id": "step_read_notion",
        "action": "read_content",
        "app": "Notion",
        "description": "검색된 문서에서 해결 방법 추출",
        "input": "notion_results",
        "output": "solution_info"
      },
      {
        "order": 6,
        "id": "step_ask_slack",
        "action": "send_message",
        "app": "Slack",
        "channel": "#cs-dev",
        "description": "개발팀에 기술적 확인 요청",
        "input": "ticket_info",
        "output": "dev_response",
        "condition": "needs_technical_confirmation || needs_manual_action",
        "is_variable": true
      },
      {
        "order": 7,
        "id": "step_compose_reply",
        "action": "compose_text",
        "app": "Zendesk",
        "description": "답변 초안 작성",
        "input": ["ticket_info", "solution_info", "dev_response", "analysis_result.sentiment"],
        "output": "reply_draft"
      },
      {
        "order": 8,
        "id": "step_categorize",
        "action": "set_field",
        "app": "Zendesk",
        "description": "티켓 카테고리 및 태그 지정",
        "input": "analysis_result.category"
      },
      {
        "order": 9,
        "id": "step_escalate",
        "action": "escalate",
        "app": "Zendesk",
        "description": "팀장에게 에스컬레이션",
        "condition": "escalation_decision == true",
        "is_variable": true
      }
    ]
  },

  "decisions": {
    "description": "분류, 에스컬레이션, 톤 조절 기준",
    "rules": [
      {
        "id": "rule_slack_inquiry",
        "condition": "needs_technical_confirmation || needs_manual_action",
        "action": "ask_dev_team_via_slack",
        "description": "기술적 확인이나 수동 처리 필요 시 Slack으로 개발팀 문의",
        "source": "user_confirmed"
      },
      {
        "id": "rule_tone_angry",
        "condition": "customer_sentiment == 'angry'",
        "action": "start_with_apology",
        "description": "화난 고객에게는 사과 문구로 시작",
        "source": "user_confirmed"
      },
      {
        "id": "rule_escalation",
        "conditions": [
          {"if": "refund_reason == 'product_defect'", "then": "escalate"},
          {"if": "refund_reason != 'product_defect' && amount >= 100000", "then": "escalate"}
        ],
        "description": "제품 불량은 항상 에스컬레이션, 그 외에는 10만원 이상만",
        "source": "user_confirmed"
      },
      {
        "id": "rule_vip",
        "condition": "customer_type == 'vip'",
        "action": "prioritize_and_personalize",
        "description": "VIP 고객은 우선 처리 + 개인화된 톤",
        "source": "inferred"
      }
    ]
  },

  "boundaries": {
    "always_do": [
      {
        "id": "always_acknowledge",
        "description": "문의 내용을 먼저 확인했음을 언급",
        "source": "user_confirmed"
      },
      {
        "id": "always_next_step",
        "description": "답변 끝에 추가 문의 안내 포함",
        "source": "inferred"
      },
      {
        "id": "always_tag",
        "description": "티켓에 적절한 카테고리/태그 지정",
        "source": "user_confirmed"
      }
    ],
    "ask_first": [
      {
        "id": "ask_policy_exception",
        "condition": "customer_requests_exception_to_policy",
        "description": "정책 예외 요청은 팀장 확인 필요",
        "source": "user_confirmed"
      },
      {
        "id": "ask_compensation",
        "condition": "compensation_value > 10000",
        "description": "1만원 초과 보상은 승인 필요",
        "source": "user_confirmed"
      }
    ],
    "never_do": [
      {
        "id": "never_promise_timeline",
        "description": "확인되지 않은 처리 일정 약속 금지",
        "source": "user_confirmed"
      },
      {
        "id": "never_blame_customer",
        "description": "고객 탓하는 표현 금지",
        "source": "inferred"
      },
      {
        "id": "never_share_internal",
        "description": "내부 시스템/정책 상세 공유 금지",
        "source": "inferred"
      }
    ]
  },

  "quality": {
    "description": "답변 품질 기준",
    "required_fields": [
      {"field": "greeting", "description": "인사말"},
      {"field": "acknowledgment", "description": "문의 내용 확인"},
      {"field": "solution", "description": "해결 방법 또는 현재 상태"},
      {"field": "next_step", "description": "다음 단계 안내"}
    ],
    "tone_rules": [
      {
        "condition": "customer_sentiment == 'angry'",
        "tone": "empathetic_apologetic",
        "example_start": "먼저 불편을 드려 진심으로 죄송합니다."
      },
      {
        "condition": "customer_sentiment == 'neutral'",
        "tone": "friendly_professional",
        "example_start": "안녕하세요, 문의 주셔서 감사합니다."
      },
      {
        "condition": "customer_type == 'vip'",
        "tone": "premium_personalized",
        "example_start": "[고객명]님, 항상 이용해 주셔서 감사합니다."
      }
    ]
  },

  "exceptions": [
    {
      "id": "exc_legal_threat",
      "condition": "message contains '소송' or '신고' or '법적'",
      "action": "escalate_immediately",
      "notify": "team_lead",
      "description": "법적 위협은 즉시 에스컬레이션",
      "source": "inferred"
    },
    {
      "id": "exc_repeat_customer",
      "condition": "customer_ticket_count >= 3 && within_7_days",
      "action": "flag_and_notify",
      "description": "7일 내 3회 이상 문의 고객은 팀장에게 공유",
      "source": "user_confirmed"
    },
    {
      "id": "exc_system_error",
      "condition": "issue_type == 'system_error' && affects_multiple_users",
      "action": "escalate_to_dev_lead",
      "description": "다수 사용자 영향 시스템 오류는 개발 리드에게 에스컬레이션",
      "source": "inferred"
    }
  ],

  "tools": [
    {"type": "service", "name": "Zendesk", "required": true, "permissions": ["read_tickets", "update_tickets", "send_replies"]},
    {"type": "service", "name": "Notion", "required": true, "permissions": ["search", "read"]},
    {"type": "app", "name": "Slack", "required": true, "permissions": ["send_messages", "read_messages"]}
  ]
}
```

---

## 5. PM 시나리오 vs CS 시나리오 비교

| 항목 | PM (Slack 문의) | CS (고객 문의) |
|------|----------------|----------------|
| **입력 복잡도** | 중 (내부 동료 질문) | 고 (외부 고객, 감정 포함) |
| **판단 포인트** | 검색 범위, 답변 포맷 | 감정 대응, 에스컬레이션, Slack 문의 여부 |
| **앱 조합** | Slack → JIRA → Drive → Slack | Zendesk → Notion → Slack → Zendesk |
| **HITL 질문 수** | 3개 | 3-4개 |
| **암묵적 규칙 예시** | "스펙 질문은 Drive까지 검색" | "제품 불량 환불은 무조건 에스컬레이션" |

---

## 6. 성공 지표

### 6.1 구조적 완성도 (자동 측정)

| 지표 | 측정 방법 | 목표 |
|------|----------|------|
| 필수 필드 완성도 | 모든 섹션 존재 여부 | 100% |
| 규칙 구체성 | 조건문에 구체적 수치/키워드 포함 | 모든 규칙 |
| 예외 커버리지 | exceptions 항목 수 | 3개 이상 |
| 톤 규칙 | quality.tone_rules 정의 여부 | 3개 이상 |

### 6.2 사용자 평가 (주관)

| 지표 | 질문 | 목표 |
|------|------|------|
| 정확도 | "에스컬레이션 기준이 맞아?" | 5/5 |
| 톤 적절성 | "화난 고객 대응 방식이 맞아?" | 4/5 이상 |
| 실행 가능성 | "신입 CS가 이걸 보고 따라할 수 있어?" | 4/5 이상 |

---

*문서 끝*
