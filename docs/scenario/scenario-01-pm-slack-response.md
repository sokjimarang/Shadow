# 시나리오 1: PM의 Slack 문의 답변 자동화

**버전: v2.0**  
**작성일: 2026-02-01**

---

## 1. 페르소나

### 1.1 기본 정보

| 항목 | 내용 |
|------|------|
| **역할** | Product Manager (PM) |
| **회사 규모** | 50-200명 스타트업/중소기업 |
| **업무 경력** | 3-5년차 |
| **팀 구성** | 개발자 5-8명, 디자이너 1-2명과 협업 |

### 1.2 업무 컨텍스트

| 항목 | 내용 |
|------|------|
| **주요 업무** | 제품 기획, 스펙 정의, 이해관계자 커뮤니케이션 |
| **일일 Slack 문의** | 15-25건 |
| **문의 유형** | 스펙 확인 60%, 일정 문의 25%, 기타 15% |
| **사용 도구** | Slack, JIRA, Google Drive, Figma |

### 1.3 Pain Points

1. **반복 답변**: 문의의 60%가 이미 JIRA나 회의록에 있는 내용
2. **검색 시간**: 관련 문서를 찾는 데 평균 3-5분 소요
3. **컨텍스트 스위칭**: Slack → JIRA → Drive → Slack 왕복이 집중력을 깨뜨림
4. **암묵적 기준**: "어떤 문의에 어떤 문서를 참조하는가"가 본인 머릿속에만 있음

### 1.4 왜 AI가 필요한가

| 요소 | 설명 |
|------|------|
| **자연어 이해** | "결제 어떻게 돼요?" vs "결제 플로우 스펙" vs "PG 연동 일정" 구분 |
| **다중 소스 검색** | JIRA + Google Drive를 동시에 검색하고 우선순위 판단 |
| **맥락 기반 요약** | 10페이지 회의록에서 질문에 맞는 부분만 추출 |
| **암묵적 규칙** | "개발팀 질문은 티켓 링크 필수, 디자인팀은 Figma 링크 우선" |

---

## 2. 시나리오 흐름

### 2.1 트리거 상황

> 개발자 김철수가 #product-questions 채널에 메시지를 보냄:
> "결제 실패 시 재시도 로직 스펙이 어떻게 되나요? 3회까지인지 5회까지인지 헷갈려서요"

### 2.2 현재 PM의 행동 패턴 (Shadow가 관찰)

```
1. Slack에서 질문 확인 (10초)
2. JIRA로 이동, "결제 재시도" 검색 (30초)
3. 검색 결과 3개 중 관련 티켓 클릭 (20초)
4. 티켓 내용 확인 - 스펙 일부만 있음 (40초)
5. Google Drive로 이동, "결제 스펙" 검색 (30초)
6. "결제 모듈 상세 스펙 v2.1" 문서 열기 (20초)
7. Ctrl+F로 "재시도" 검색, 해당 섹션 찾기 (40초)
8. Slack으로 돌아와 답변 작성 (60초)
   - JIRA 티켓 링크 포함
   - Drive 문서 링크 포함
   - 핵심 내용 요약
```

**총 소요 시간: 약 4분 10초**

### 2.3 앱 전환 흐름 (3개 앱)

```
[Slack] ──질문 확인──→ [JIRA] ──검색──→ [Google Drive] ──추가 검색──→ [Slack]
   │                      │                    │                      │
   │                      │                    │                      │
   ▼                      ▼                    ▼                      ▼
 질문 읽기            티켓 검색           회의록/스펙 검색         답변 작성
 키워드 파악          관련 티켓 확인       상세 내용 확인          링크 + 요약
```

---

## 3. Shadow 데이터 흐름

### 3.1 OBSERVE (관찰)

**수집 이벤트 시퀀스:**

| 순서 | 앱 | 행동 | 캡처 데이터 |
|------|-----|------|------------|
| 1 | Slack | 메시지 클릭 | before/after 스크린샷, 클릭 좌표 |
| 2 | Chrome | JIRA 탭 클릭 | 앱 전환 이벤트 |
| 3 | JIRA | 검색창 클릭 + 타이핑 | 검색어: "결제 재시도" |
| 4 | JIRA | 검색 결과 클릭 | 티켓 ID: PAY-234 |
| 5 | Chrome | 새 탭 열기 | Google Drive 이동 |
| 6 | Drive | 검색창 클릭 + 타이핑 | 검색어: "결제 스펙" |
| 7 | Drive | 문서 클릭 | 문서명: "결제 모듈 상세 스펙 v2.1" |
| 8 | Drive | Ctrl+F + 타이핑 | 검색어: "재시도" |
| 9 | Slack | 메시지 입력창 클릭 | 앱 전환 이벤트 |
| 10 | Slack | 답변 타이핑 | 답변 내용 (링크 포함) |

**RawObservation 예시:**
```json
{
  "id": "obs_pm_001",
  "session_id": "session_pm_20260201_001",
  "timestamp": "2026-02-01T14:30:15Z",
  "before_screenshot_id": "ss_before_001",
  "after_screenshot_id": "ss_after_001",
  "event_id": "event_click_001"
}
```

### 3.2 ANALYZE (분석)

**행동 라벨링 (VLM + LLM):**

```json
{
  "id": "action_pm_001",
  "observation_id": "obs_pm_001",
  "action_type": "click",
  "target_element": "slack_message",
  "app": "Slack",
  "semantic_label": "Slack에서 '결제 재시도 스펙' 관련 질문 확인",
  "extracted_keywords": ["결제", "재시도", "스펙", "3회", "5회"],
  "intent_guess": "문의 내용 파악 및 키워드 추출"
}
```

**패턴 감지 (3회 관찰 후):**

```json
{
  "id": "pattern_pm_001",
  "name": "Slack 문의 → JIRA → Drive → Slack 답변",
  "observation_count": 3,
  "core_sequence": [
    {"order": 1, "action": "read_message", "app": "Slack", "output": "question_keywords"},
    {"order": 2, "action": "search", "app": "JIRA", "input": "question_keywords"},
    {"order": 3, "action": "read_ticket", "app": "JIRA", "output": "jira_info"},
    {"order": 4, "action": "search", "app": "Google Drive", "input": "question_keywords"},
    {"order": 5, "action": "read_document", "app": "Google Drive", "output": "drive_info"},
    {"order": 6, "action": "compose_reply", "app": "Slack", "input": ["jira_info", "drive_info"]}
  ],
  "uncertainties": [
    {
      "type": "condition",
      "step": 4,
      "description": "언제 Google Drive를 추가로 검색하는가?",
      "hypothesis": "JIRA 티켓에 상세 스펙이 없을 때"
    },
    {
      "type": "quality",
      "step": 6,
      "description": "답변에 항상 두 링크(JIRA + Drive)를 포함하는가?",
      "hypothesis": "상세 스펙 질문일 때만 Drive 링크 포함"
    },
    {
      "type": "condition",
      "step": 2,
      "description": "JIRA 검색어를 어떻게 결정하는가?",
      "hypothesis": "질문에서 핵심 명사 2-3개 추출"
    }
  ]
}
```

### 3.3 CLARIFY (HITL 질문)

**질문 1 - Drive 검색 조건:**

```json
{
  "id": "question_pm_001",
  "type": "hypothesis",
  "question_text": "JIRA 티켓에 상세 스펙이 없을 때 Google Drive를 추가로 검색하시는 것 같은데, 맞나요?",
  "context": "최근 5건의 답변 중 3건에서 JIRA 검색 후 Drive를 추가 검색했습니다. 3건 모두 '상세', '구체적', '정확한 수치' 관련 질문이었습니다.",
  "options": [
    {"id": "opt_1", "label": "네, JIRA에 상세 내용이 없으면 Drive 검색합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "스펙 관련 질문은 항상 JIRA + Drive 둘 다 검색합니다", "action": "update_rule"},
    {"id": "opt_3", "label": "질문자가 개발자일 때만 Drive까지 검색합니다", "action": "add_condition"}
  ]
}
```

**질문 2 - 답변 포맷:**

```json
{
  "id": "question_pm_002",
  "type": "quality",
  "question_text": "답변에 항상 JIRA 티켓 링크를 포함하시는 것 같은데, 맞나요?",
  "context": "최근 8건의 답변에서 모두 JIRA 링크가 포함되어 있었습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 항상 JIRA 링크를 포함합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "개발팀 질문에만 JIRA 링크를 포함합니다", "action": "add_condition"},
    {"id": "opt_3", "label": "관련 티켓이 있을 때만 포함합니다", "action": "add_condition"}
  ]
}
```

**질문 3 - 검색어 추출:**

```json
{
  "id": "question_pm_003",
  "type": "hypothesis",
  "question_text": "질문에서 기능명과 상태(실패, 성공 등)를 조합해서 JIRA를 검색하시는 것 같은데, 맞나요?",
  "context": "'결제 실패 시 재시도' 질문에서 '결제 재시도'로 검색하셨습니다. 다른 2건에서도 유사한 패턴이 관찰되었습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 기능명 + 상태/동작을 조합합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "질문의 핵심 명사만 추출합니다", "action": "update_rule"},
    {"id": "opt_3", "label": "상황에 따라 다릅니다", "action": "reject"}
  ]
}
```

### 3.4 PROCESS (응답 처리)

**사용자 응답 예시:**

질문 1에 opt_2 선택: "스펙 관련 질문은 항상 JIRA + Drive 둘 다 검색합니다"

```json
{
  "id": "answer_pm_001",
  "question_id": "question_pm_001",
  "selected_option_id": "opt_2",
  "timestamp": "2026-02-01T15:00:00Z"
}
```

**명세서 업데이트:**

```json
{
  "spec_update": {
    "path": "decisions.rules",
    "operation": "add",
    "value": {
      "id": "rule_search_scope",
      "condition": "question_type == 'spec'",
      "action": "search_both_jira_and_drive",
      "description": "스펙 관련 질문은 JIRA와 Google Drive 모두 검색",
      "source": "user_confirmed"
    }
  }
}
```

### 3.5 NOTIFY (알림)

```
✅ 명세서가 업데이트되었습니다.

- 업무: Slack 문의 답변
- 변경 사항: 스펙 질문 시 JIRA + Drive 동시 검색 규칙 추가
- 버전: v1.0.0 → v1.1.0

[명세서 보기]
```

---

## 4. 생성되는 에이전트 명세서

```json
{
  "meta": {
    "id": "spec_pm_001",
    "name": "Slack 문의 답변 자동화",
    "description": "JIRA와 Google Drive를 검색하여 Slack 문의에 답변",
    "version": "1.2.0",
    "status": "active"
  },

  "trigger": {
    "description": "Slack #product-questions 채널에 질문이 올라올 때",
    "conditions": [
      {"type": "app_event", "app": "Slack", "event": "message_received"},
      {"type": "content_match", "pattern": ".*스펙.*|.*어떻게.*|.*언제.*|.*확인.*"}
    ],
    "operator": "AND"
  },

  "workflow": {
    "description": "질문 분석 → JIRA 검색 → Drive 검색 → 답변 작성",
    "steps": [
      {
        "order": 1,
        "id": "step_analyze_question",
        "action": "extract_keywords",
        "app": "Slack",
        "description": "질문에서 검색 키워드 추출",
        "output": "search_keywords"
      },
      {
        "order": 2,
        "id": "step_search_jira",
        "action": "search",
        "app": "JIRA",
        "description": "JIRA에서 관련 티켓 검색",
        "input": "search_keywords",
        "output": "jira_results"
      },
      {
        "order": 3,
        "id": "step_read_jira",
        "action": "read_content",
        "app": "JIRA",
        "description": "검색된 티켓 내용 확인",
        "input": "jira_results",
        "output": "jira_info"
      },
      {
        "order": 4,
        "id": "step_search_drive",
        "action": "search",
        "app": "Google Drive",
        "description": "Google Drive에서 관련 문서 검색",
        "input": "search_keywords",
        "output": "drive_results",
        "condition": "question_type == 'spec'"
      },
      {
        "order": 5,
        "id": "step_read_drive",
        "action": "read_content",
        "app": "Google Drive",
        "description": "검색된 문서에서 관련 내용 추출",
        "input": "drive_results",
        "output": "drive_info",
        "condition": "drive_results.length > 0"
      },
      {
        "order": 6,
        "id": "step_compose_reply",
        "action": "compose_text",
        "app": "Slack",
        "description": "검색 결과를 바탕으로 답변 작성",
        "input": ["jira_info", "drive_info"],
        "output": "reply_text"
      },
      {
        "order": 7,
        "id": "step_send_reply",
        "action": "send_message",
        "app": "Slack",
        "description": "답변 전송",
        "input": "reply_text"
      }
    ]
  },

  "decisions": {
    "description": "검색 범위 및 답변 포맷 기준",
    "rules": [
      {
        "id": "rule_search_scope",
        "condition": "question_type == 'spec'",
        "action": "search_both_jira_and_drive",
        "description": "스펙 관련 질문은 JIRA와 Drive 모두 검색",
        "source": "user_confirmed"
      },
      {
        "id": "rule_jira_link",
        "condition": "jira_results.length > 0",
        "action": "include_jira_link",
        "description": "관련 티켓이 있으면 JIRA 링크 포함",
        "source": "user_confirmed"
      },
      {
        "id": "rule_drive_link",
        "condition": "question_type == 'spec' && drive_results.length > 0",
        "action": "include_drive_link",
        "description": "스펙 질문이고 문서가 있으면 Drive 링크 포함",
        "source": "user_confirmed"
      },
      {
        "id": "rule_keyword_extraction",
        "condition": "always",
        "action": "extract_feature_and_action",
        "description": "기능명 + 상태/동작 조합으로 검색어 생성",
        "source": "user_confirmed"
      }
    ]
  },

  "boundaries": {
    "always_do": [
      {
        "id": "always_summarize",
        "description": "링크만 보내지 않고 핵심 내용 요약 포함",
        "source": "user_confirmed"
      },
      {
        "id": "always_jira_link",
        "description": "관련 JIRA 티켓 링크 포함",
        "source": "user_confirmed"
      }
    ],
    "ask_first": [
      {
        "id": "ask_no_results",
        "condition": "jira_results.length == 0 && drive_results.length == 0",
        "description": "검색 결과가 없으면 PM에게 확인",
        "source": "user_confirmed"
      },
      {
        "id": "ask_multiple_matches",
        "condition": "jira_results.length > 3",
        "description": "관련 티켓이 3개 초과면 어떤 것이 맞는지 확인",
        "source": "inferred"
      }
    ],
    "never_do": [
      {
        "id": "never_guess",
        "description": "검색 결과 없이 추측으로 답변하지 않음",
        "source": "user_confirmed"
      },
      {
        "id": "never_outdated",
        "description": "6개월 이상 된 문서는 최신 여부 확인 없이 인용하지 않음",
        "source": "inferred"
      }
    ]
  },

  "quality": {
    "description": "답변 품질 기준",
    "required_fields": [
      {"field": "summary", "description": "핵심 내용 요약 (2-3문장)"},
      {"field": "jira_link", "description": "JIRA 티켓 링크"},
      {"field": "drive_link", "description": "Drive 문서 링크 (스펙 질문 시)", "conditional": true}
    ],
    "format": {
      "tone": "professional_friendly",
      "max_length": "300자",
      "structure": ["요약", "상세 링크", "추가 질문 유도"]
    }
  },

  "exceptions": [
    {
      "id": "exc_urgent",
      "condition": "message contains '긴급' or '장애'",
      "action": "notify_pm_immediately",
      "description": "긴급/장애 문의는 자동 답변 없이 PM에게 즉시 알림",
      "source": "inferred"
    },
    {
      "id": "exc_confidential",
      "condition": "document marked as 'confidential'",
      "action": "ask_pm_before_sharing",
      "description": "기밀 문서는 공유 전 PM 확인",
      "source": "inferred"
    }
  ],

  "tools": [
    {"type": "app", "name": "Slack", "required": true, "permissions": ["read_messages", "send_messages"]},
    {"type": "service", "name": "JIRA", "required": true, "permissions": ["search", "read_issues"]},
    {"type": "service", "name": "Google Drive", "required": true, "permissions": ["search", "read_files"]}
  ]
}
```

---

## 5. 성공 지표

### 5.1 구조적 완성도 (자동 측정)

| 지표 | 측정 방법 | 목표 |
|------|----------|------|
| 필수 필드 완성도 | meta, trigger, workflow, decisions, boundaries 존재 | 100% |
| 규칙 구체성 | 모호한 표현("적절히", "상황에 따라") 개수 | 0개 |
| 예외 커버리지 | exceptions 항목 수 | 2개 이상 |
| 앱 커버리지 | 관찰된 앱이 tools에 모두 포함 | 100% |

### 5.2 사용자 평가 (주관)

| 지표 | 질문 | 목표 |
|------|------|------|
| 정확도 | "이게 내 업무 방식 맞아?" | 4/5 이상 |
| 완성도 | "빠진 규칙이 있어?" | "없음" 응답 |
| 실행 가능성 | "다른 PM이 이걸 보고 따라할 수 있어?" | 4/5 이상 |

---

*문서 끝*