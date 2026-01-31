# 시나리오 1: PM의 Slack 문의 답변 자동화

**버전: v1.0
작성일: 2026-01-31**

---

## 1. 개요

### 1.1 대상 페르소나
- **역할**: Product Manager (PM)
- **업무**: Slack으로 들어오는 서비스 스펙 관련 문의에 답변
- **사용 툴**: JIRA, Google Drive, Slack

### 1.2 핵심 문제
PM은 하루에 수십 건의 Slack 문의를 받지만, 대부분은 JIRA 티켓이나 Google Drive 회의록에 이미 정리된 내용이다. 하지만 매번 문서를 찾아 답변하는 데 시간이 소요된다.

### 1.3 Shadow 솔루션
PM이 Slack 문의에 답변하는 패턴을 관찰하여, 어떤 키워드로 검색하고, 어떻게 답변을 작성하는지 학습한다. 이후 유사한 문의가 오면 자동으로 답변 초안을 생성하거나, Slack 봇이 직접 답변한다.

---

## 2. Shadow 데이터 흐름

### 2.1 OBSERVE (관찰)

**수집 데이터:**
- Slack 앱에서 DM/채널 메시지 수신 이벤트
- JIRA 브라우저 탭에서 검색 키워드 입력
- Google Drive 검색 및 문서 열람
- Slack으로 돌아와 답변 작성

**RawObservation 예시:**
```json
{
  "id": "obs_001",
  "session_id": "session_pm_001",
  "timestamp": "2026-01-31T14:00:00Z",
  "before_screenshot_id": "screenshot_before_001",
  "after_screenshot_id": "screenshot_after_001",
  "event_id": "event_click_001"
}
```

**InputEvent 예시:**
```json
{
  "id": "event_click_001",
  "type": "mouse_click",
  "position": {"x": 300, "y": 150},
  "button": "left",
  "active_window": {
    "title": "#product-questions - Slack",
    "app_name": "Slack",
    "app_bundle_id": "com.tinyspeck.slackmacgap"
  }
}
```

### 2.2 ANALYZE (분석)

**행동 라벨링 (VLM):**
```json
{
  "id": "action_001",
  "observation_id": "obs_001",
  "action_type": "click",
  "target_element": "slack_message",
  "app": "Slack",
  "semantic_label": "Slack 채널에서 '결제 기능 스펙' 관련 질문 확인",
  "intent_guess": "문의 내용 파악",
  "confidence": 0.95
}
```

**패턴 감지 (LLM):**
3회 이상 관찰 후 DetectedPattern 생성:
```json
{
  "id": "pattern_pm_001",
  "name": "Slack 문의 → JIRA/Drive 검색 → 답변",
  "core_sequence": [
    {"order": 1, "action_type": "click", "target_pattern": "slack_message", "app": "Slack"},
    {"order": 2, "action_type": "navigate", "target_pattern": "JIRA 검색", "app": "Chrome"},
    {"order": 3, "action_type": "type", "target_pattern": "검색어 입력", "app": "Chrome"},
    {"order": 4, "action_type": "click", "target_pattern": "검색 결과 티켓", "app": "Chrome"},
    {"order": 5, "action_type": "navigate", "target_pattern": "Slack", "app": "Slack"},
    {"order": 6, "action_type": "type", "target_pattern": "답변 작성", "app": "Slack"}
  ],
  "uncertainties": [
    {
      "type": "condition",
      "description": "어떤 키워드로 JIRA를 검색하는가?",
      "hypothesis": "질문에서 핵심 키워드를 추출하여 검색"
    },
    {
      "type": "quality",
      "description": "답변에 항상 JIRA 링크를 포함하는가?",
      "hypothesis": "항상 티켓 링크를 포함"
    }
  ]
}
```

### 2.3 CLARIFY (HITL 질문)

**생성된 질문:**

**질문 1 - 가설 검증:**
```json
{
  "id": "question_001",
  "type": "hypothesis",
  "question_text": "Slack 문의에 답변할 때, 항상 JIRA 티켓 링크를 포함하시는 것 같은데 맞나요?",
  "context": "최근 3건의 답변에서 모두 JIRA 링크가 포함되어 있었습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 항상 포함합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "중요한 질문에만 포함합니다", "action": "add_condition"},
    {"id": "opt_3", "label": "아니요, 선택적입니다", "action": "reject"}
  ]
}
```

**질문 2 - 품질 확인:**
```json
{
  "id": "question_002",
  "type": "quality",
  "question_text": "JIRA 티켓 검색 결과가 3개 미만일 때 Google Drive 회의록을 추가로 확인하시는 것 같은데, 맞나요?",
  "context": "최근 5건의 답변 중 3건에서 JIRA 검색 결과가 적을 때(0~2개) Google Drive를 추가로 검색했습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 검색 결과 3개 미만이면 Drive도 확인합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "아니요, JIRA에서 0건일 때만 Drive 확인합니다", "action": "update_condition"},
    {"id": "opt_3", "label": "질문 내용이 중요할 때만 Drive 확인합니다", "action": "add_condition"}
  ]
}
```

**Slack으로 전송:**
Shadow Slack Bot이 PM에게 DM으로 질문 전송. PM은 버튼 클릭으로 답변.

### 2.4 PROCESS (응답 처리)

**사용자 응답:**
```json
{
  "id": "answer_001",
  "question_id": "question_001",
  "selected_option_id": "opt_1",
  "user_id": "user_pm",
  "timestamp": "2026-01-31T14:10:00Z"
}
```

**해석:**
```json
{
  "id": "interpreted_001",
  "answer_id": "answer_001",
  "action": "add_rule",
  "spec_update": {
    "path": "quality.required_fields",
    "operation": "add",
    "value": {
      "field": "jira_link",
      "description": "JIRA 티켓 링크 필수",
      "format": "url"
    }
  },
  "confidence": 1.0
}
```

### 2.5 NOTIFY (알림)

**Slack 알림:**
```
✅ 명세서가 업데이트되었습니다.

- 업무: Slack 문의 답변
- 변경 사항: 답변에 JIRA 링크 필수로 추가됨
- 버전: v1.1.0 → v1.2.0

자세한 내용: https://shadow.app/specs/spec_pm_001
```

---

## 3. 생성되는 에이전트 명세서 (AgentSpec)

```json
{
  "meta": {
    "id": "spec_pm_001",
    "name": "Slack 문의 답변 자동화",
    "description": "JIRA/Drive를 검색하여 Slack 문의에 답변",
    "version": "1.2.0",
    "status": "active"
  },

  "trigger": {
    "description": "Slack에서 특정 채널/DM에 멘션 또는 질문 수신",
    "conditions": [
      {
        "type": "app_active",
        "app": "Slack",
        "context": "message_received"
      },
      {
        "type": "content_match",
        "field": "message",
        "pattern": ".*스펙.*|.*기능.*|.*언제.*"
      }
    ],
    "operator": "AND"
  },

  "workflow": {
    "description": "Slack 문의 확인 → JIRA 검색 → 답변 작성",
    "steps": [
      {
        "order": 1,
        "id": "step_read_message",
        "action": "extract_text",
        "target": "slack_message",
        "app": "Slack",
        "description": "Slack 메시지에서 질문 내용 추출",
        "output": "question_text"
      },
      {
        "order": 2,
        "id": "step_extract_keywords",
        "action": "extract_keywords",
        "target": "question_text",
        "description": "질문에서 검색 키워드 추출",
        "output": "search_keywords"
      },
      {
        "order": 3,
        "id": "step_search_jira",
        "action": "search",
        "target": "JIRA",
        "app": "Chrome",
        "description": "JIRA에서 관련 티켓 검색",
        "input": "search_keywords",
        "output": "jira_results"
      },
      {
        "order": 4,
        "id": "step_check_results",
        "action": "check_condition",
        "description": "JIRA 검색 결과 있는지 확인",
        "output": "has_results"
      },
      {
        "order": 5,
        "id": "step_search_drive",
        "action": "search",
        "target": "Google Drive",
        "app": "Chrome",
        "description": "JIRA에 없으면 Google Drive 회의록 검색",
        "condition": "has_results == false",
        "input": "search_keywords",
        "output": "drive_results",
        "is_variable": true
      },
      {
        "order": 6,
        "id": "step_compose_answer",
        "action": "compose_text",
        "description": "검색 결과를 바탕으로 답변 작성",
        "input": "jira_results or drive_results",
        "output": "answer_text"
      },
      {
        "order": 7,
        "id": "step_send_answer",
        "action": "type",
        "target": "slack_reply",
        "app": "Slack",
        "description": "Slack에 답변 전송",
        "input": "answer_text"
      }
    ]
  },

  "decisions": {
    "description": "검색 및 답변 작성 기준",
    "rules": [
      {
        "id": "rule_search_priority",
        "condition": "always",
        "action": "search_jira_first",
        "description": "항상 JIRA를 먼저 검색",
        "source": "user_confirmed",
        "confidence": 1.0
      },
      {
        "id": "rule_fallback_drive",
        "condition": "jira_results.length == 0",
        "action": "search_drive",
        "description": "JIRA에 없으면 Google Drive 검색",
        "source": "user_confirmed",
        "confidence": 1.0
      }
    ]
  },

  "boundaries": {
    "always_do": [
      {
        "id": "always_include_link",
        "description": "답변에 항상 JIRA 티켓 링크 포함",
        "source": "user_confirmed"
      },
      {
        "id": "always_context",
        "description": "티켓 내용을 요약하여 전달 (링크만 보내지 않음)",
        "source": "user_confirmed"
      }
    ],
    "ask_first": [
      {
        "id": "ask_no_results",
        "condition": "jira_results.length == 0 && drive_results.length == 0",
        "description": "검색 결과가 없으면 PM에게 확인 요청",
        "source": "inferred"
      }
    ],
    "never_do": [
      {
        "id": "never_fabricate",
        "description": "검색 결과가 없을 때 추측으로 답변하지 않음",
        "source": "inferred"
      }
    ]
  },

  "quality": {
    "description": "답변 품질 기준",
    "required_fields": [
      {
        "field": "jira_link",
        "description": "JIRA 티켓 링크",
        "format": "url"
      },
      {
        "field": "summary",
        "description": "티켓 내용 요약",
        "format": "text"
      }
    ],
    "validations": [
      {
        "field": "jira_link",
        "rule": "valid_url",
        "description": "올바른 JIRA URL 형식"
      }
    ]
  },

  "exceptions": [
    {
      "id": "exc_urgent",
      "condition": "message contains '긴급'",
      "action": "notify_pm_immediately",
      "description": "긴급 문의는 PM에게 즉시 알림",
      "source": "inferred"
    },
    {
      "id": "exc_no_results",
      "condition": "no search results found",
      "action": "ask_pm",
      "description": "검색 결과 없으면 PM에게 질문",
      "source": "user_confirmed"
    }
  ],

  "tools": [
    {
      "type": "app",
      "name": "Slack",
      "required": true,
      "permissions": ["read_messages", "send_messages"]
    },
    {
      "type": "service",
      "name": "JIRA",
      "required": true,
      "permissions": ["search", "read_issues"]
    },
    {
      "type": "service",
      "name": "Google Drive",
      "required": true,
      "permissions": ["search", "read_files"]
    }
  ]
}
```

---

## 4. 산출물: Slack Bot

### 4.1 자동화 단계

**Phase 1: 답변 초안 생성**
- PM이 답변하기 전에 자동으로 JIRA/Drive 검색
- 검색 결과를 바탕으로 답변 초안 생성
- PM이 확인 후 전송

**Phase 2: 자동 답변**
- 명세서의 confidence_score가 0.9 이상일 때
- 간단한 문의는 Slack Bot이 직접 답변
- 복잡한 문의는 PM에게 에스컬레이션

### 4.2 대시보드

**표시 정보:**
- JIRA 프로젝트별 문의 빈도
- Google Drive 문서별 참조 횟수
- 자주 묻는 질문 Top 10
- 자동 답변 성공률

---

## 5. 성공 지표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| 답변 시간 단축 | 평균 5분 → 1분 | 문의 수신부터 답변까지 시간 |
| 자동 답변 비율 | 50% 이상 | 전체 문의 중 Bot 자동 답변 비율 |
| 답변 정확도 | 90% 이상 | PM 피드백 기반 정확도 |
| PM 만족도 | 4.5/5 이상 | 주간 설문조사 |

---

*문서 끝*
