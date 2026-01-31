# 시나리오 2: HR/운영팀의 폼 제출 관리 자동화

**버전: v1.0
작성일: 2026-01-31**

---

## 1. 개요

### 1.1 대상 페르소나
- **역할**: HR팀, 운영팀
- **업무**: Google Form 제출 요청/관리, 미제출자 리마인드, 스프레드시트 업데이트
- **사용 툴**: Google Form, Gmail, Google Sheets, Slack, Discord

### 1.2 핵심 문제
채용, CS 문의, 행사 신청 등 다양한 폼을 관리하는데, 제출 현황을 주기적으로 확인하고 미제출자에게 리마인드를 보내는 작업이 반복적이고 시간이 많이 걸린다.

### 1.3 Shadow 솔루션
HR/운영팀이 폼 제출 관리 업무를 수행하는 패턴을 관찰하여, 언제 어떻게 리마인드를 보내는지, 스프레드시트를 어떻게 업데이트하는지 학습한다. 이후 자동으로 폼 제출 현황을 확인하고 리마인드를 발송한다.

---

## 2. Shadow 데이터 흐름

### 2.1 OBSERVE (관찰)

**수집 데이터:**
- Gmail에서 폼 제출 요청 메일 발송
- Google Sheets에서 제출 현황 확인 (제출자 이름 체크)
- Gmail에서 미제출자에게 리마인드 메일 작성
- Slack/Discord에서 특정 사용자 멘션
- Google Sheets에 제출 여부 및 특이사항 기록

**RawObservation 예시:**
```json
{
  "id": "obs_hr_001",
  "session_id": "session_hr_001",
  "timestamp": "2026-01-31T10:00:00Z",
  "before_screenshot_id": "screenshot_before_hr_001",
  "after_screenshot_id": "screenshot_after_hr_001",
  "event_id": "event_hr_click_001"
}
```

**InputEvent 예시:**
```json
{
  "id": "event_hr_click_001",
  "type": "mouse_click",
  "position": {"x": 450, "y": 200},
  "button": "left",
  "active_window": {
    "title": "채용 지원서 현황 - Google Sheets",
    "app_name": "Chrome",
    "app_bundle_id": "com.google.Chrome"
  }
}
```

### 2.2 ANALYZE (분석)

**행동 라벨링 (VLM):**
```json
{
  "id": "action_hr_001",
  "observation_id": "obs_hr_001",
  "action_type": "click",
  "target_element": "spreadsheet_cell_B3",
  "app": "Chrome",
  "semantic_label": "Google Sheets에서 제출 여부 컬럼 확인",
  "intent_guess": "누가 제출했는지 확인",
  "confidence": 0.92
}
```

**패턴 감지 (LLM):**
3회 이상 관찰 후 DetectedPattern 생성:
```json
{
  "id": "pattern_hr_001",
  "name": "폼 제출 관리 루틴",
  "core_sequence": [
    {"order": 1, "action_type": "navigate", "target_pattern": "Google Sheets", "app": "Chrome"},
    {"order": 2, "action_type": "scroll", "target_pattern": "제출 현황 컬럼", "app": "Chrome"},
    {"order": 3, "action_type": "click", "target_pattern": "미제출자 행", "app": "Chrome"},
    {"order": 4, "action_type": "navigate", "target_pattern": "Gmail", "app": "Chrome"},
    {"order": 5, "action_type": "click", "target_pattern": "새 메일 작성", "app": "Chrome"},
    {"order": 6, "action_type": "type", "target_pattern": "리마인드 메일 내용", "app": "Chrome"},
    {"order": 7, "action_type": "click", "target_pattern": "전송", "app": "Chrome"},
    {"order": 8, "action_type": "navigate", "target_pattern": "Slack", "app": "Slack"},
    {"order": 9, "action_type": "type", "target_pattern": "@사용자 리마인드", "app": "Slack"}
  ],
  "uncertainties": [
    {
      "type": "condition",
      "description": "몇 일 간격으로 리마인드를 보내는가?",
      "hypothesis": "3일마다 확인하여 미제출자에게 리마인드"
    },
    {
      "type": "quality",
      "description": "스프레드시트에 특이사항을 어떤 경우에 기록하는가?",
      "hypothesis": "제출 후 수정 요청이 있는 경우 특이사항 기록"
    }
  ]
}
```

### 2.3 CLARIFY (HITL 질문)

**생성된 질문:**

**질문 1 - 가설 검증:**
```json
{
  "id": "question_hr_001",
  "type": "hypothesis",
  "question_text": "폼 제출 현황을 3일마다 확인하시는 것 같은데, 맞나요?",
  "context": "최근 관찰된 3건의 확인 작업이 모두 3일 간격이었습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 3일마다 확인합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "아니요, 매일 확인합니다", "action": "update_condition"},
    {"id": "opt_3", "label": "마감일 기준 3일 전부터 매일 확인합니다", "action": "add_condition"}
  ]
}
```

**질문 2 - 품질 확인:**
```json
{
  "id": "question_hr_002",
  "type": "quality",
  "question_text": "마감일 1일 전부터는 리마인드 메일과 함께 Slack 멘션도 보내시는 것 같은데, 맞나요?",
  "context": "최근 관찰된 5건 중 마감 1일 전 리마인드 2건은 메일+Slack 모두 발송했고, 마감 3일 전 리마인드 3건은 메일만 발송했습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 마감 1일 전부터 Slack 멘션 추가합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "아니요, 마감 당일에만 Slack 멘션 추가합니다", "action": "update_condition"},
    {"id": "opt_3", "label": "미제출자가 5명 이상일 때만 Slack 멘션합니다", "action": "add_condition"}
  ]
}
```

**Slack으로 전송:**
Shadow Slack Bot이 HR 담당자에게 DM으로 질문 전송.

### 2.4 PROCESS (응답 처리)

**사용자 응답:**
```json
{
  "id": "answer_hr_001",
  "question_id": "question_hr_001",
  "selected_option_id": "opt_3",
  "user_id": "user_hr",
  "timestamp": "2026-01-31T14:15:00Z"
}
```

**해석:**
```json
{
  "id": "interpreted_hr_001",
  "answer_id": "answer_hr_001",
  "action": "add_condition",
  "spec_update": {
    "path": "decisions.rules",
    "operation": "add",
    "value": {
      "id": "rule_reminder_timing",
      "condition": "days_until_deadline <= 3",
      "action": "check_daily_and_remind",
      "description": "마감일 3일 전부터 매일 확인하고 리마인드 발송"
    }
  },
  "confidence": 1.0
}
```

### 2.5 NOTIFY (알림)

**Slack 알림:**
```
✅ 명세서가 업데이트되었습니다.

- 업무: 폼 제출 관리
- 변경 사항: 마감일 3일 전부터 매일 확인 규칙 추가
- 버전: v1.1.0 → v1.2.0

자세한 내용: https://shadow.app/specs/spec_hr_001
```

---

## 3. 생성되는 에이전트 명세서 (AgentSpec)

```json
{
  "meta": {
    "id": "spec_hr_001",
    "name": "폼 제출 관리 자동화",
    "description": "Google Form 제출 현황 확인 및 미제출자 리마인드 자동화",
    "version": "1.2.0",
    "status": "active"
  },

  "trigger": {
    "description": "폼 제출 마감일 기준 3일 전부터 매일 오전 9시",
    "conditions": [
      {
        "type": "time_based",
        "schedule": "daily 09:00",
        "condition": "days_until_deadline <= 3"
      }
    ],
    "operator": "AND"
  },

  "workflow": {
    "description": "제출 현황 확인 → 미제출자 리마인드 → 스프레드시트 업데이트",
    "steps": [
      {
        "order": 1,
        "id": "step_check_sheet",
        "action": "read_spreadsheet",
        "target": "Google Sheets",
        "app": "Chrome",
        "description": "스프레드시트에서 제출 현황 확인",
        "output": "submission_status"
      },
      {
        "order": 2,
        "id": "step_identify_missing",
        "action": "filter",
        "description": "미제출자 목록 추출",
        "input": "submission_status",
        "output": "missing_users"
      },
      {
        "order": 3,
        "id": "step_send_email",
        "action": "compose_and_send",
        "target": "Gmail",
        "app": "Chrome",
        "description": "미제출자에게 리마인드 메일 발송",
        "input": "missing_users",
        "is_variable": true
      },
      {
        "order": 4,
        "id": "step_send_slack",
        "action": "send_message",
        "target": "Slack",
        "app": "Slack",
        "description": "Slack에서 미제출자 멘션",
        "input": "missing_users",
        "condition": "days_until_deadline <= 1",
        "is_variable": true
      },
      {
        "order": 5,
        "id": "step_update_sheet",
        "action": "write_spreadsheet",
        "target": "Google Sheets",
        "app": "Chrome",
        "description": "스프레드시트에 리마인드 발송 기록 업데이트",
        "input": "missing_users"
      }
    ]
  },

  "decisions": {
    "description": "리마인드 발송 및 업데이트 기준",
    "rules": [
      {
        "id": "rule_check_frequency",
        "condition": "days_until_deadline > 3",
        "action": "skip",
        "else_action": "check_daily",
        "description": "마감일 3일 전부터 매일 확인",
        "source": "user_confirmed",
        "confidence": 1.0
      },
      {
        "id": "rule_email_always",
        "condition": "user in missing_users",
        "action": "send_email",
        "description": "미제출자에게 항상 이메일 발송",
        "source": "user_confirmed",
        "confidence": 1.0
      },
      {
        "id": "rule_slack_urgent",
        "condition": "days_until_deadline <= 1",
        "action": "send_slack_mention",
        "description": "마감 1일 전부터 Slack 멘션 추가",
        "source": "user_confirmed",
        "confidence": 1.0
      }
    ]
  },

  "boundaries": {
    "always_do": [
      {
        "id": "always_log",
        "description": "리마인드 발송 시 스프레드시트에 발송 일시 기록",
        "source": "user_confirmed"
      },
      {
        "id": "always_polite",
        "description": "리마인드 메일은 정중한 톤 유지",
        "source": "inferred"
      }
    ],
    "ask_first": [
      {
        "id": "ask_manual_exception",
        "condition": "user has '제출 면제' note in sheet",
        "description": "제출 면제 표시가 있는 사용자는 리마인드 제외",
        "source": "user_confirmed"
      }
    ],
    "never_do": [
      {
        "id": "never_duplicate",
        "description": "같은 날 중복 리마인드 발송 금지",
        "source": "inferred"
      },
      {
        "id": "never_after_deadline",
        "description": "마감일 이후에는 리마인드 발송하지 않음",
        "source": "inferred"
      }
    ]
  },

  "quality": {
    "description": "리마인드 및 기록 품질 기준",
    "required_fields": [
      {
        "field": "recipient_email",
        "description": "수신자 이메일",
        "format": "email"
      },
      {
        "field": "form_link",
        "description": "제출 폼 링크",
        "format": "url"
      },
      {
        "field": "deadline",
        "description": "마감일",
        "format": "YYYY-MM-DD"
      }
    ],
    "validations": [
      {
        "field": "deadline",
        "rule": "not_past",
        "description": "마감일이 과거가 아니어야 함"
      }
    ]
  },

  "exceptions": [
    {
      "id": "exc_exempted",
      "condition": "user has exemption note",
      "action": "skip_user",
      "description": "제출 면제 사용자는 리마인드 제외",
      "source": "user_confirmed"
    },
    {
      "id": "exc_already_submitted",
      "condition": "user submitted after check",
      "action": "update_status_only",
      "description": "확인 후 제출한 경우 리마인드 발송하지 않음",
      "source": "inferred"
    }
  ],

  "tools": [
    {
      "type": "service",
      "name": "Google Sheets",
      "required": true,
      "permissions": ["read", "write"]
    },
    {
      "type": "service",
      "name": "Gmail",
      "required": true,
      "permissions": ["send_email"]
    },
    {
      "type": "app",
      "name": "Slack",
      "required": false,
      "permissions": ["send_messages"]
    },
    {
      "type": "app",
      "name": "Discord",
      "required": false,
      "permissions": ["send_messages"]
    }
  ]
}
```

---

## 4. 산출물: 자동 리마인드 시스템

### 4.1 자동화 단계

**Phase 1: 현황 모니터링**
- 매일 자동으로 Google Sheets 확인
- 미제출자 목록 추출
- HR 담당자에게 요약 리포트 전송

**Phase 2: 자동 리마인드**
- 미제출자에게 자동으로 리마인드 메일 발송
- 마감일 임박 시 Slack/Discord 멘션 추가
- 스프레드시트에 발송 기록 자동 업데이트

**Phase 3: 예외 처리**
- 제출 면제 사용자 자동 필터링
- 중복 발송 방지
- 이미 제출한 사용자 실시간 반영

### 4.2 대시보드

**표시 정보:**
- 전체 대상자 수
- 제출 완료 수 / 미제출 수
- 리마인드 발송 횟수
- 제출률 추이 그래프
- 특이사항 목록 (수정 요청, 면제 사유 등)

---

## 5. 성공 지표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| 제출률 향상 | 80% → 95% | 리마인드 자동화 전후 비교 |
| HR 업무 시간 단축 | 주 5시간 → 1시간 | 현황 확인 및 리마인드 소요 시간 |
| 리마인드 발송 정확도 | 98% 이상 | 잘못된 발송/누락 비율 |
| 사용자 불편 최소화 | 중복 리마인드 0건 | 중복 발송 건수 |

---

*문서 끝*
