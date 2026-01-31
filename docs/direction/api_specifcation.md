# Shadow - API 명세서

**버전: v1.1
작성일: 2026-01-31**

---

## 1. 개요

이 문서는 Shadow 시스템의 API 및 인터페이스를 정의한다.

**범위:**

- Slack Bot API (사용자 ↔ Shadow)
- 내부 모듈 인터페이스 (Agent ↔ Server)
- VLM/LLM 프롬프트 템플릿

---

## 2. Slack Bot API

### 2.1 개요

Shadow는 Slack Bolt (Python)를 사용하여 Slack과 통신한다.

**인증:**

- Bot Token: `xoxb-*`
- Signing Secret: Slack 이벤트 검증용

**권한 스코프:**

- `chat:write` - 메시지 전송
- `im:history` - DM 읽기
- `im:write` - DM 전송
- `users:read` - 사용자 정보

### 2.2 이벤트 수신

### Message Event

사용자가 DM으로 메시지 전송 시

```python
@app.event("message")
def handle_message(event, say):
    """
    Event payload:
    {
        "type": "message",
        "user": "U1234567890",
        "text": "현재 상태",
        "channel": "D1234567890",
        "ts": "1234567890.123456"
    }
    """

```

**처리할 메시지 패턴:**

| 패턴 | 의도 | 응답 |
| --- | --- | --- |
| "현재 상태" / "status" | 상태 확인 | 상태 정보 |
| "녹화 시작" / "start" | 관찰 시작 | 확인 메시지 |
| "녹화 중지" / "stop" | 관찰 중지 | 확인 메시지 |
| "내 패턴" / "patterns" | 패턴 목록 | 패턴 리스트 |
| "명세서 수정: ..." | 수정 요청 | 처리 결과 |
| 기타 | 알 수 없음 | 도움말 |

### Block Actions Event

버튼 클릭 시

```python
@app.action("hitl_answer_*")
def handle_button(ack, body, say):
    """
    Body payload:
    {
        "type": "block_actions",
        "user": { "id": "U1234567890" },
        "actions": [{
            "action_id": "hitl_answer_yes",
            "block_id": "question_001",
            "value": "confirm"
        }],
        "message": { "ts": "1234567890.123456" }
    }
    """

```

### 2.3 메시지 전송

### HITL 질문 메시지

```python
def send_hitl_question(channel_id: str, question: HITLQuestion):
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔍 새로운 패턴을 발견했어요!"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*📋 패턴:* {question.pattern_name}"},
                {"type": "mrkdwn", "text": f"*🔄 반복 횟수:* {question.occurrences}회"}
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"💡 *확인이 필요해요:*\n\n{question.question_text}"
            }
        },
        {
            "type": "actions",
            "block_id": f"question_{question.id}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": option.label},
                    "action_id": f"hitl_answer_{option.id}",
                    "value": option.action
                }
                for option in question.options
            ]
        }
    ]

    if question.allows_freetext:
        blocks.append({
            "type": "input",
            "block_id": f"freetext_{question.id}",
            "element": {
                "type": "plain_text_input",
                "action_id": "freetext_input",
                "placeholder": {"type": "plain_text", "text": "또는 직접 입력..."}
            },
            "label": {"type": "plain_text", "text": "다른 답변"}
        })

    return client.chat_postMessage(channel=channel_id, blocks=blocks)

```

**메시지 예시:**

```
🔍 새로운 패턴을 발견했어요!

📋 패턴: 이메일 → 스프레드시트 복사
🔄 반복 횟수: 3회

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 확인이 필요해요:

금액이 100만원 넘으면 상사 확인을 받으시는 것 같은데, 맞나요?

[맞아요] [아니요, 다른 기준이에요] [잘 모르겠어요]

```

### 상태 응답 메시지

```python
def send_status(channel_id: str, status: ShadowStatus):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🔍 Shadow 상태"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*상태:* {status.state_emoji} {status.state}"},
                {"type": "mrkdwn", "text": f"*녹화 시간:* {status.duration}"},
                {"type": "mrkdwn", "text": f"*이벤트 수:* {status.event_count}"},
                {"type": "mrkdwn", "text": f"*감지된 패턴:* {status.pattern_count}"},
                {"type": "mrkdwn", "text": f"*대기 중 질문:* {status.pending_questions}"},
                {"type": "mrkdwn", "text": f"*마지막 활동:* {status.last_activity}"}
            ]
        }
    ]
    return client.chat_postMessage(channel=channel_id, blocks=blocks)

```

### 업데이트 알림 메시지

```python
def send_spec_update(channel_id: str, spec: AgentSpec, changes: list):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "✅ 명세서가 업데이트되었어요!"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*📝 패턴:* {spec.name}"},
                {"type": "mrkdwn", "text": f"*📌 버전:* {spec.previous_version} → {spec.version}"}
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*변경 사항:*\n" + "\n".join([f"• {c}" for c in changes])
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "상세 보기"},
                    "url": f"{WEB_URL}/specs/{spec.id}"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "되돌리기"},
                    "action_id": f"revert_{spec.id}_{spec.previous_version}",
                    "style": "danger"
                }
            ]
        }
    ]
    return client.chat_postMessage(channel=channel_id, blocks=blocks)

```

---

## 3. 내부 모듈 인터페이스

### 3.1 Agent ↔ Server 통신

### 데이터 전송 (Agent → Server)

**Endpoint:** `POST /api/v1/observations`

**Request:**

```json
{
  "session_id": "session_001",
  "observations": [
    {
      "id": "obs_001",
      "timestamp": "2025-01-31T10:00:00Z",
      "before_screenshot": "base64...",
      "after_screenshot": "base64...",
      "event": {
        "type": "mouse_click",
        "position": {"x": 100, "y": 200},
        "button": "left"
      },
      "active_window": {
        "title": "Inbox - Gmail",
        "app_name": "Google Chrome",
        "app_bundle_id": "com.google.Chrome"
      }
    }
  ]
}

```

**Response:**

```json
{
  "status": "ok",
  "processed": 1,
  "observation_ids": ["obs_001"]
}

```

### 상태 조회 (Agent ↔ Server)

**Endpoint:** `GET /api/v1/status`

**Response:**

```json
{
  "state": "recording",
  "session_id": "session_001",
  "start_time": "2025-01-31T09:00:00Z",
  "event_count": 127,
  "observation_count": 45,
  "pattern_count": 2,
  "pending_questions": 1
}

```

### 제어 명령 (Agent ↔ Server)

**Endpoint:** `POST /api/v1/control`

**Request:**

```json
{
  "command": "start" | "stop" | "pause" | "resume",
  "session_id": "session_001"
}

```

**Response:**

```json
{
  "status": "ok",
  "new_state": "recording",
  "session_id": "session_001"
}

```

### 3.2 모듈 간 인터페이스

### DataCollector → Analyzer

```python
class DataCollector:
    async def get_observations(self,
                               session_id: str,
                               since: datetime = None,
                               limit: int = 100) -> List[RawObservation]:
        """세션의 관찰 데이터 조회"""
        pass

class Analyzer:
    async def analyze_observation(self,
                                  observation: RawObservation,
                                  context: List[LabeledAction]) -> LabeledAction:
        """단일 관찰 데이터 분석"""
        pass

    async def detect_patterns(self,
                              sessions: List[SessionSequence],
                              existing_patterns: List[DetectedPattern]) -> List[DetectedPattern]:
        """패턴 감지"""
        pass

```

### Analyzer → HITLManager

```python
class HITLManager:
    async def create_questions(self,
                               pattern: DetectedPattern) -> List[HITLQuestion]:
        """패턴의 불확실 지점에서 질문 생성"""
        pass

    async def send_questions(self,
                             questions: List[HITLQuestion],
                             channel_id: str) -> List[str]:
        """Slack으로 질문 전송, message_ts 반환"""
        pass

    async def process_answer(self,
                             answer: HITLAnswer) -> InterpretedAnswer:
        """응답 해석"""
        pass

```

### HITLManager → SpecManager

```python
class SpecManager:
    async def create_spec(self,
                          pattern: DetectedPattern,
                          answers: List[InterpretedAnswer] = None) -> AgentSpec:
        """새 명세서 생성"""
        pass

    async def update_spec(self,
                          spec_id: str,
                          updates: List[InterpretedAnswer]) -> AgentSpec:
        """명세서 업데이트"""
        pass

    async def get_spec(self, spec_id: str) -> AgentSpec:
        """명세서 조회"""
        pass

    async def list_specs(self) -> List[AgentSpec]:
        """모든 명세서 목록"""
        pass

```

---

## 4. VLM/LLM 프롬프트 템플릿

### 4.1 행동 라벨링 프롬프트 (VLM)

```
[System]
당신은 사용자의 컴퓨터 화면 행동을 분석하는 AI입니다.
Before/After 스크린샷과 이벤트 로그를 보고, 사용자가 무엇을 했는지 분석하세요.

분석 시 다음을 고려하세요:
1. 화면의 어떤 요소가 변경되었는지
2. 이벤트(클릭, 입력 등)와 화면 변화의 관계
3. 사용자의 의도가 무엇인지

[Input]
Before 스크린샷: {before_image}
After 스크린샷: {after_image}
이벤트 타입: {event_type}
이벤트 위치: ({x}, {y})
키 입력: {key_input}
활성 앱: {app_name}
창 제목: {window_title}

이전 행동 컨텍스트:
{previous_actions_summary}

[Output Format]
JSON 형식으로만 응답하세요:
{
  "action_type": "click | type | copy | paste | scroll | navigate | select",
  "target_element": "요소 이름 (예: search_bar, cell_B3, send_button)",
  "app": "앱 이름",
  "app_context": "앱 내 컨텍스트 (예: inbox, compose, spreadsheet_edit)",
  "semantic_label": "한국어로 행동 설명 (예: Gmail 검색창에 주문번호 입력)",
  "intent_guess": "추측되는 의도 (예: 특정 이메일 찾기)",
  "confidence": 0.0-1.0
}

```

### 4.2 패턴 감지 프롬프트 (LLM)

```
[System]
당신은 업무 패턴 분석 전문가입니다.
여러 세션의 행동 시퀀스를 비교하여 반복되는 패턴을 찾아주세요.

패턴 분석 시 다음을 고려하세요:
1. 핵심적으로 반복되는 행동 시퀀스
2. 변형이 있는 부분 (항상 같지 않은 부분)
3. 조건에 따라 달라지는 것 같은 부분
4. 판단 기준이 있을 것 같은 부분

[Input]
세션 1 ({session1_date}):
{session1_actions}

세션 2 ({session2_date}):
{session2_actions}

세션 3 ({session3_date}):
{session3_actions}

기존 감지된 패턴:
{existing_patterns}

[Output Format]
JSON 형식으로만 응답하세요:
{
  "patterns": [
    {
      "name": "패턴 이름 (한국어)",
      "description": "패턴 설명",
      "core_sequence": [
        {"order": 1, "action": "행동", "app": "앱", "is_variable": false}
      ],
      "apps_involved": ["앱1", "앱2"],
      "variations": [
        {"description": "변형 설명", "occurrence_rate": 0.3}
      ],
      "uncertainties": [
        {
          "type": "condition | exception | quality",
          "description": "불확실한 부분 설명",
          "hypothesis": "AI의 가설"
        }
      ],
      "confidence": 0.0-1.0
    }
  ],
  "analysis_notes": "추가 분석 메모"
}

```

### 4.3 HITL 질문 생성 프롬프트 (LLM)

```
[System]
당신은 사용자에게 업무 규칙을 확인하는 질문을 만드는 AI입니다.
질문은 다음 원칙을 따라야 합니다:
1. 구체적이고 닫힌 질문 (예/아니오로 답할 수 있게)
2. 한국어로 자연스럽게
3. 사용자가 쉽게 이해할 수 있게
4. 판단 기준이나 규칙을 확인하는 내용

질문 유형:
- anomaly: 평소와 다른 행동 확인
- alternative: 다른 방법 선택 이유 확인
- hypothesis: 추론한 규칙 확인
- quality: 품질 기준 확인

[Input]
패턴 정보:
{pattern_info}

불확실 지점:
{uncertainty}

관찰된 예시:
{examples}

[Output Format]
JSON 형식으로만 응답하세요:
{
  "question_type": "anomaly | alternative | hypothesis | quality",
  "question_text": "질문 내용 (한국어)",
  "context": "간단한 배경 설명",
  "options": [
    {"label": "맞아요", "action": "confirm_rule"},
    {"label": "아니요, 다른 기준이에요", "action": "reject_rule"},
    {"label": "잘 모르겠어요", "action": "skip"}
  ],
  "allows_freetext": true
}

```

### 4.4 응답 해석 프롬프트 (LLM)

```
[System]
당신은 사용자의 응답을 해석하여 명세서 업데이트 내용으로 변환하는 AI입니다.

[Input]
원본 질문:
{question}

사용자 응답:
- 응답 타입: {response_type} (button 또는 freetext)
- 선택한 옵션: {selected_option}
- 자유 텍스트: {freetext}

현재 명세서 관련 부분:
{current_spec_section}

[Output Format]
JSON 형식으로만 응답하세요:
{
  "action": "add_rule | add_exception | set_quality | update_rule | reject | needs_clarification",
  "spec_update": {
    "path": "decisions.rules | boundaries.always_do | exceptions | ...",
    "operation": "add | update | delete",
    "value": {
      // 추가/수정할 내용
    }
  },
  "summary": "변경 요약 (한국어)",
  "confidence": 0.0-1.0,
  "follow_up_needed": false,
  "follow_up_question": null
}

```

---

## 5. 에러 코드

### 5.1 API 에러 코드

| 코드 | HTTP | 설명 |
| --- | --- | --- |
| E001 | 500 | 내부 서버 오류 |
| E002 | 400 | 잘못된 요청 형식 |
| E003 | 401 | 인증 실패 |
| E004 | 404 | 리소스 없음 |
| E005 | 429 | 요청 제한 초과 |
| E101 | 500 | VLM API 호출 실패 |
| E102 | 500 | LLM API 호출 실패 |
| E103 | 500 | Slack API 호출 실패 |
| E201 | 400 | 세션 없음 |
| E202 | 400 | 명세서 없음 |
| E203 | 400 | 질문 없음 |

### 5.2 에러 응답 형식

```json
{
  "error": {
    "code": "E001",
    "message": "내부 서버 오류가 발생했습니다",
    "details": "추가 정보 (선택)",
    "timestamp": "2025-01-31T10:00:00Z"
  }
}

```

---

## 6. 레이트 리밋

| API | 제한 | 비고 |
| --- | --- | --- |
| /observations | 100 req/min | Agent → Server |
| VLM (Claude) | 60 req/min | 행동 라벨링 |
| LLM (Claude) | 60 req/min | 패턴/질문 생성 |
| Slack | 1 msg/sec | 메시지 전송 |

---

*문서 끝*