# 시나리오 3: 마케터의 광고 집행 자동화

**버전: v1.0
작성일: 2026-01-31**

---

## 1. 개요

### 1.1 대상 페르소나
- **역할**: 마케터 (Performance Marketer)
- **업무**: Google Form 신청자 → Meta Ads Custom Audience 업로드 → 광고 집행
- **사용 툴**: Google Form, Google Sheets, Meta Ads Manager, Slack

### 1.2 핵심 문제
무료 강의 신청자를 대상으로 유료 강의 광고를 집행하는데, 매번 스프레드시트에서 이메일 추출 → Meta Ads에 수동 업로드 → 광고 세팅하는 작업이 반복적이다.

### 1.3 Shadow 솔루션
마케터가 광고 집행 업무를 수행하는 패턴을 관찰하여, 어떤 조건에서 Custom Audience를 생성하고 광고를 집행하는지 학습한다. 이후 자동으로 신청자 데이터를 추출하고 광고 집행까지 자동화한다.

---

## 2. Shadow 데이터 흐름

### 2.1 OBSERVE (관찰)

**수집 데이터:**
- Google Sheets에서 신규 신청자 데이터 확인
- 이메일 주소 컬럼 복사
- Meta Ads Manager 열기
- Custom Audience 생성 페이지 이동
- 이메일 데이터 업로드
- 광고 캠페인 생성 및 타겟팅 설정
- Slack으로 광고 집행 완료 알림 전송

**RawObservation 예시:**
```json
{
  "id": "obs_mkt_001",
  "session_id": "session_mkt_001",
  "timestamp": "2026-01-31T15:00:00Z",
  "before_screenshot_id": "screenshot_before_mkt_001",
  "after_screenshot_id": "screenshot_after_mkt_001",
  "event_id": "event_mkt_click_001"
}
```

**InputEvent 예시:**
```json
{
  "id": "event_mkt_click_001",
  "type": "mouse_click",
  "position": {"x": 500, "y": 250},
  "button": "left",
  "active_window": {
    "title": "무료 강의 신청자 목록 - Google Sheets",
    "app_name": "Chrome",
    "app_bundle_id": "com.google.Chrome"
  }
}
```

### 2.2 ANALYZE (분석)

**행동 라벨링 (VLM):**
```json
{
  "id": "action_mkt_001",
  "observation_id": "obs_mkt_001",
  "action_type": "select",
  "target_element": "spreadsheet_column_email",
  "app": "Chrome",
  "semantic_label": "Google Sheets에서 이메일 주소 컬럼 선택",
  "intent_guess": "광고 타겟팅을 위한 이메일 추출",
  "confidence": 0.93
}
```

**패턴 감지 (LLM):**
3회 이상 관찰 후 DetectedPattern 생성:
```json
{
  "id": "pattern_mkt_001",
  "name": "무료 강의 신청자 → Meta Ads 광고 집행",
  "core_sequence": [
    {"order": 1, "action_type": "navigate", "target_pattern": "Google Sheets", "app": "Chrome"},
    {"order": 2, "action_type": "select", "target_pattern": "이메일 컬럼", "app": "Chrome"},
    {"order": 3, "action_type": "copy", "target_pattern": "이메일 데이터", "app": "Chrome"},
    {"order": 4, "action_type": "navigate", "target_pattern": "Meta Ads Manager", "app": "Chrome"},
    {"order": 5, "action_type": "click", "target_pattern": "Custom Audience 생성", "app": "Chrome"},
    {"order": 6, "action_type": "paste", "target_pattern": "이메일 업로드", "app": "Chrome"},
    {"order": 7, "action_type": "click", "target_pattern": "광고 캠페인 생성", "app": "Chrome"},
    {"order": 8, "action_type": "type", "target_pattern": "광고 설정 입력", "app": "Chrome"},
    {"order": 9, "action_type": "click", "target_pattern": "광고 게시", "app": "Chrome"},
    {"order": 10, "action_type": "navigate", "target_pattern": "Slack", "app": "Slack"},
    {"order": 11, "action_type": "type", "target_pattern": "광고 집행 완료 알림", "app": "Slack"}
  ],
  "uncertainties": [
    {
      "type": "condition",
      "description": "신청자가 몇 명 이상일 때 광고를 집행하는가?",
      "hypothesis": "신규 신청자 50명 이상일 때 광고 집행"
    },
    {
      "type": "quality",
      "description": "광고 예산은 어떻게 설정하는가?",
      "hypothesis": "신청자 수에 비례하여 예산 설정 (1인당 1,000원)"
    }
  ]
}
```

### 2.3 CLARIFY (HITL 질문)

**생성된 질문:**

**질문 1 - 가설 검증:**
```json
{
  "id": "question_mkt_001",
  "type": "hypothesis",
  "question_text": "신규 신청자가 50명 이상일 때 광고를 집행하시는 것 같은데, 맞나요?",
  "context": "최근 3건의 광고 집행 시점 모두 신청자가 50명 이상이었습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 50명 이상일 때 집행합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "아니요, 매주 월요일에 집행합니다", "action": "update_condition"},
    {"id": "opt_3", "label": "신청자 수와 무관하게 수동으로 판단합니다", "action": "reject"}
  ]
}
```

**질문 2 - 품질 확인:**
```json
{
  "id": "question_mkt_002",
  "type": "quality",
  "question_text": "광고 예산을 신청자 수에 비례하여 설정하시나요?",
  "context": "최근 광고 예산을 보면 신청자 1인당 약 1,000원 정도로 설정되었습니다.",
  "options": [
    {"id": "opt_1", "label": "네, 1인당 1,000원으로 계산합니다", "action": "add_rule"},
    {"id": "opt_2", "label": "아니요, 고정 예산 10만원입니다", "action": "update_rule"},
    {"id": "opt_3", "label": "매번 다르게 설정합니다", "action": "reject"}
  ]
}
```

**Slack으로 전송:**
Shadow Slack Bot이 마케터에게 DM으로 질문 전송.

### 2.4 PROCESS (응답 처리)

**사용자 응답:**
```json
{
  "id": "answer_mkt_001",
  "question_id": "question_mkt_001",
  "selected_option_id": "opt_1",
  "user_id": "user_mkt",
  "timestamp": "2026-01-31T15:20:00Z"
}
```

**해석:**
```json
{
  "id": "interpreted_mkt_001",
  "answer_id": "answer_mkt_001",
  "action": "add_rule",
  "spec_update": {
    "path": "decisions.rules",
    "operation": "add",
    "value": {
      "id": "rule_min_applicants",
      "condition": "new_applicants >= 50",
      "action": "create_campaign",
      "description": "신규 신청자 50명 이상일 때 광고 집행"
    }
  },
  "confidence": 1.0
}
```

### 2.5 NOTIFY (알림)

**Slack 알림:**
```
✅ 명세서가 업데이트되었습니다.

- 업무: 광고 집행 자동화
- 변경 사항: 신규 신청자 50명 이상 시 광고 집행 규칙 추가
- 버전: v1.1.0 → v1.2.0

자세한 내용: https://shadow.app/specs/spec_mkt_001
```

---

## 3. 생성되는 에이전트 명세서 (AgentSpec)

```json
{
  "meta": {
    "id": "spec_mkt_001",
    "name": "Meta Ads 광고 집행 자동화",
    "description": "Google Form 신청자 데이터를 Meta Ads Custom Audience로 업로드하고 광고 집행",
    "version": "1.2.0",
    "status": "active"
  },

  "trigger": {
    "description": "Google Sheets에서 신규 신청자가 50명 이상 누적되었을 때",
    "conditions": [
      {
        "type": "content_match",
        "field": "new_applicants_count",
        "pattern": ">= 50"
      }
    ],
    "operator": "AND"
  },

  "workflow": {
    "description": "신청자 데이터 추출 → Custom Audience 생성 → 광고 집행 → Slack 알림",
    "steps": [
      {
        "order": 1,
        "id": "step_read_sheet",
        "action": "read_spreadsheet",
        "target": "Google Sheets",
        "app": "Chrome",
        "description": "스프레드시트에서 신규 신청자 이메일 추출",
        "output": "applicant_emails"
      },
      {
        "order": 2,
        "id": "step_filter_new",
        "action": "filter",
        "description": "이미 광고 타겟팅한 사용자 제외",
        "input": "applicant_emails",
        "output": "new_emails"
      },
      {
        "order": 3,
        "id": "step_navigate_meta",
        "action": "navigate",
        "target": "Meta Ads Manager",
        "app": "Chrome",
        "description": "Meta Ads Manager 열기"
      },
      {
        "order": 4,
        "id": "step_create_audience",
        "action": "create_custom_audience",
        "target": "Meta Ads",
        "app": "Chrome",
        "description": "Custom Audience 생성 및 이메일 업로드",
        "input": "new_emails",
        "output": "audience_id"
      },
      {
        "order": 5,
        "id": "step_calculate_budget",
        "action": "calculate",
        "description": "광고 예산 계산 (신청자 수 * 1,000원)",
        "input": "new_emails.length",
        "output": "campaign_budget"
      },
      {
        "order": 6,
        "id": "step_create_campaign",
        "action": "create_campaign",
        "target": "Meta Ads",
        "app": "Chrome",
        "description": "광고 캠페인 생성 및 타겟팅 설정",
        "input": "audience_id, campaign_budget",
        "output": "campaign_id"
      },
      {
        "order": 7,
        "id": "step_publish_campaign",
        "action": "click",
        "target": "광고 게시 버튼",
        "app": "Chrome",
        "description": "광고 게시"
      },
      {
        "order": 8,
        "id": "step_update_sheet",
        "action": "write_spreadsheet",
        "target": "Google Sheets",
        "app": "Chrome",
        "description": "스프레드시트에 광고 집행 기록 추가",
        "input": "campaign_id, new_emails"
      },
      {
        "order": 9,
        "id": "step_notify_slack",
        "action": "send_message",
        "target": "Slack",
        "app": "Slack",
        "description": "Slack에 광고 집행 완료 알림",
        "input": "campaign_id, new_emails.length, campaign_budget"
      }
    ]
  },

  "decisions": {
    "description": "광고 집행 시점 및 예산 설정 기준",
    "rules": [
      {
        "id": "rule_min_applicants",
        "condition": "new_applicants >= 50",
        "action": "create_campaign",
        "description": "신규 신청자 50명 이상일 때 광고 집행",
        "source": "user_confirmed",
        "confidence": 1.0
      },
      {
        "id": "rule_budget_calculation",
        "condition": "always",
        "action": "calculate_budget_per_applicant",
        "description": "광고 예산 = 신청자 수 * 1,000원",
        "source": "user_confirmed",
        "confidence": 1.0
      },
      {
        "id": "rule_exclude_existing",
        "condition": "email in previous_audiences",
        "action": "skip_email",
        "description": "이미 타겟팅한 이메일은 제외",
        "source": "inferred",
        "confidence": 0.9
      }
    ]
  },

  "boundaries": {
    "always_do": [
      {
        "id": "always_record",
        "description": "광고 집행 후 스프레드시트에 기록",
        "source": "user_confirmed"
      },
      {
        "id": "always_notify",
        "description": "Slack으로 집행 완료 알림 전송",
        "source": "user_confirmed"
      },
      {
        "id": "always_deduplicate",
        "description": "중복 타겟팅 방지 (이전 Custom Audience 확인)",
        "source": "inferred"
      }
    ],
    "ask_first": [
      {
        "id": "ask_high_budget",
        "condition": "campaign_budget > 200000",
        "description": "예산 20만원 초과 시 마케터에게 확인",
        "source": "inferred"
      }
    ],
    "never_do": [
      {
        "id": "never_without_data",
        "description": "신청자 데이터가 없을 때 광고 집행하지 않음",
        "source": "inferred"
      },
      {
        "id": "never_duplicate_campaign",
        "description": "같은 날 중복 캠페인 생성 금지",
        "source": "inferred"
      }
    ]
  },

  "quality": {
    "description": "광고 집행 품질 기준",
    "required_fields": [
      {
        "field": "campaign_name",
        "description": "캠페인 이름",
        "format": "text"
      },
      {
        "field": "audience_size",
        "description": "타겟 오디언스 크기",
        "format": "number"
      },
      {
        "field": "budget",
        "description": "광고 예산",
        "format": "number"
      }
    ],
    "validations": [
      {
        "field": "audience_size",
        "rule": "minimum_50",
        "description": "최소 50명 이상"
      },
      {
        "field": "budget",
        "rule": "positive_number",
        "description": "양수 예산"
      }
    ]
  },

  "exceptions": [
    {
      "id": "exc_invalid_emails",
      "condition": "email format invalid",
      "action": "skip_and_log",
      "description": "이메일 형식 오류는 건너뛰고 로그 기록",
      "source": "inferred"
    },
    {
      "id": "exc_meta_api_error",
      "condition": "Meta Ads API error",
      "action": "retry_3_times_then_notify",
      "description": "API 오류 시 3회 재시도 후 마케터에게 알림",
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
      "name": "Meta Ads Manager",
      "required": true,
      "permissions": ["create_audience", "create_campaign"]
    },
    {
      "type": "app",
      "name": "Slack",
      "required": true,
      "permissions": ["send_messages"]
    }
  ]
}
```

---

## 4. 산출물: 광고 집행 자동화 시스템

### 4.1 자동화 단계

**Phase 1: 신청자 모니터링**
- 매일 Google Sheets에서 신규 신청자 수 확인
- 50명 이상 누적 시 마케터에게 알림 전송
- 광고 집행 예정 리포트 제공 (예산, 타겟 수 등)

**Phase 2: 반자동 광고 집행**
- Custom Audience 자동 생성
- 광고 캠페인 설정 자동화 (예산, 타겟팅)
- 마케터 확인 후 게시

**Phase 3: 완전 자동 광고 집행**
- 신청자 50명 이상 시 자동으로 광고 집행
- 스프레드시트에 집행 기록 자동 업데이트
- Slack으로 집행 완료 알림

### 4.2 대시보드

**표시 정보:**
- 현재 신청자 수 (광고 집행 대기)
- 이번 주 광고 집행 횟수
- Custom Audience 크기 추이
- 광고 예산 사용 현황
- 전환율 (무료 강의 → 유료 강의)

---

## 5. 성공 지표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| 광고 집행 소요 시간 단축 | 30분 → 5분 | 데이터 추출부터 광고 게시까지 시간 |
| 광고 집행 빈도 증가 | 월 2회 → 주 1회 | 자동화로 더 자주 광고 집행 가능 |
| 타겟팅 정확도 | 95% 이상 | 중복 타겟팅 제외율 |
| ROAS (광고 수익률) | 300% 이상 | 광고 비용 대비 매출 |

---

*문서 끝*
