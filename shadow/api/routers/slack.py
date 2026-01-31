"""Slack 이벤트 수신 API

Slack Event API 및 Interactive Components를 처리합니다.
"""

import json
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from shadow.config import settings
from shadow.slack.verification import is_request_expired, verify_slack_signature

router = APIRouter(prefix="/slack", tags=["slack"])


# === 응답 모델 ===


class URLVerificationResponse(BaseModel):
    """URL Verification 응답"""

    challenge: str


class SlackEventResponse(BaseModel):
    """Slack 이벤트 응답"""

    ok: bool = True


# === Slack Events API ===


@router.post("/events", response_model=URLVerificationResponse | SlackEventResponse)
async def receive_slack_event(
    request: Request,
    x_slack_request_timestamp: str = Header(...),
    x_slack_signature: str = Header(...),
):
    """Slack Event API 엔드포인트

    Slack에서 전송하는 이벤트를 수신합니다:
    - URL Verification (앱 설정 시)
    - Message 이벤트 (DM 메시지)
    - 기타 이벤트

    Args:
        request: FastAPI Request
        x_slack_request_timestamp: Slack request timestamp
        x_slack_signature: Slack request signature

    Returns:
        URL Verification 또는 일반 응답

    Raises:
        HTTPException: 검증 실패 또는 처리 오류 시
    """
    # 요청 body 읽기
    body_bytes = await request.body()

    # 1. Timestamp 검증 (Replay attack 방지)
    if is_request_expired(x_slack_request_timestamp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Request timestamp expired",
        )

    # 2. Signature 검증
    if not settings.slack_signing_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SLACK_SIGNING_SECRET not configured",
        )

    if not verify_slack_signature(
        body_bytes,
        x_slack_request_timestamp,
        x_slack_signature,
        settings.slack_signing_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    # 3. JSON 파싱
    try:
        payload = json.loads(body_bytes)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        )

    # 4. 이벤트 타입별 처리
    event_type = payload.get("type")

    # URL Verification (Slack 앱 설정 시 최초 1회)
    if event_type == "url_verification":
        return URLVerificationResponse(challenge=payload["challenge"])

    # Event Callback (실제 이벤트)
    if event_type == "event_callback":
        event = payload.get("event", {})
        await _handle_event(event)
        return SlackEventResponse(ok=True)

    # 그 외 타입은 무시
    return SlackEventResponse(ok=True)


async def _handle_event(event: dict[str, Any]) -> None:
    """이벤트 처리 (메시지, 반응 등)

    Args:
        event: Slack event payload
    """
    event_type = event.get("type")

    # 메시지 이벤트 (선택 구현, P1)
    if event_type == "message":
        await _handle_message_event(event)


async def _handle_message_event(event: dict[str, Any]) -> None:
    """메시지 이벤트 처리

    사용자가 DM으로 명령을 보냈을 때 처리합니다:
    - "현재 상태" / "status" → 시스템 상태 응답
    - "녹화 시작" / "start" → 녹화 시작
    - "녹화 중지" / "stop" → 녹화 중지

    Args:
        event: Message event payload
    """
    # TODO: P1 기능 - 메시지 명령 처리
    # 현재는 로그만 남기고 무시
    text = event.get("text", "")
    user = event.get("user")
    channel = event.get("channel")

    print(f"[Slack Message] User: {user}, Channel: {channel}, Text: {text}")


# === Slack Interactive Components ===


@router.post("/interactivity", response_model=SlackEventResponse)
async def receive_slack_interactivity(
    request: Request,
    x_slack_request_timestamp: str = Header(...),
    x_slack_signature: str = Header(...),
):
    """Slack Interactive Components 엔드포인트

    버튼 클릭, 메뉴 선택 등 Interactive Components 이벤트를 수신합니다.

    Args:
        request: FastAPI Request
        x_slack_request_timestamp: Slack request timestamp
        x_slack_signature: Slack request signature

    Returns:
        처리 결과

    Raises:
        HTTPException: 검증 실패 또는 처리 오류 시
    """
    # 요청 body 읽기
    body_bytes = await request.body()

    # 1. Timestamp 검증
    if is_request_expired(x_slack_request_timestamp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Request timestamp expired",
        )

    # 2. Signature 검증
    if not settings.slack_signing_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SLACK_SIGNING_SECRET not configured",
        )

    if not verify_slack_signature(
        body_bytes,
        x_slack_request_timestamp,
        x_slack_signature,
        settings.slack_signing_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    # 3. Form 데이터 파싱 (Slack은 application/x-www-form-urlencoded로 전송)
    # Request.form()은 multipart만 지원하므로 body를 직접 파싱
    from urllib.parse import parse_qs

    form_str = body_bytes.decode("utf-8")
    form_dict = parse_qs(form_str)

    # payload는 단일 값이므로 리스트의 첫 번째 요소를 가져옴
    payload_list = form_dict.get("payload")
    if not payload_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing payload",
        )

    payload_str = payload_list[0]

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in payload",
        )

    # 4. Interaction 타입별 처리
    interaction_type = payload.get("type")

    if interaction_type == "block_actions":
        await _handle_block_actions(payload)
        return SlackEventResponse(ok=True)

    # 그 외 타입은 무시
    return SlackEventResponse(ok=True)


async def _handle_block_actions(payload: dict[str, Any]) -> None:
    """Block Actions 처리 (버튼 클릭)

    HITL 질문의 버튼 클릭 시 호출됩니다.

    Args:
        payload: Block actions payload

    Payload 구조:
        {
            "user": {"id": "U1234567890"},
            "actions": [{
                "action_id": "hitl_answer_yes",
                "block_id": "question_001",
                "value": "{\"question_id\":\"...\",\"option_id\":\"...\"}"
            }],
            "message": {"ts": "1234567890.123456"}
        }
    """
    actions = payload.get("actions", [])
    if not actions:
        return

    action = actions[0]  # 첫 번째 action 처리
    action_id = action.get("action_id", "")

    # HITL 답변 버튼인지 확인
    if not action_id.startswith("hitl_answer_"):
        return

    # action.value에서 question_id, option_id 추출
    try:
        value_data = json.loads(action.get("value", "{}"))
    except json.JSONDecodeError:
        value_data = {}

    question_id = value_data.get("question_id")
    option_id = value_data.get("option_id")

    if not question_id or not option_id:
        print(f"[Slack Block Action] Missing question_id or option_id: {value_data}")
        return

    # 사용자 및 메시지 정보
    user = payload.get("user", {})
    user_id = user.get("id")
    message = payload.get("message", {})
    message_ts = message.get("ts")

    print(f"[Slack Block Action] Question: {question_id}, Option: {option_id}, User: {user_id}")

    # TODO: Phase 5에서 실제 비즈니스 로직 구현
    # - HITLRepository.create_answer()
    # - interpret_answer() 호출
    # - update_spec() 호출
    # - Slack 메시지 업데이트
