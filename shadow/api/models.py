"""API 요청/응답 모델

API 명세서 기반 Pydantic 모델 정의
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ====== Agent ↔ Server API 모델 ======


class EventData(BaseModel):
    """이벤트 데이터"""

    type: str = Field(..., description="이벤트 타입")
    position: dict[str, int] | None = Field(None, description="마우스 위치 {x, y}")
    button: str | None = Field(None, description="마우스 버튼")


class ActiveWindow(BaseModel):
    """활성 윈도우 정보"""

    title: str = Field(..., description="창 제목")
    app_name: str = Field(..., description="앱 이름")
    app_bundle_id: str = Field(..., description="앱 번들 ID")


class ObservationData(BaseModel):
    """단일 관찰 데이터"""

    id: str = Field(..., description="관찰 ID")
    timestamp: str = Field(..., description="관찰 시각 (ISO 8601)")
    before_screenshot: str = Field(..., description="Before 스크린샷 (base64)")
    after_screenshot: str = Field(..., description="After 스크린샷 (base64)")
    event: EventData = Field(..., description="이벤트 정보")
    active_window: ActiveWindow = Field(..., description="활성 윈도우")


class ObservationsRequest(BaseModel):
    """관찰 데이터 전송 요청"""

    session_id: str = Field(..., description="세션 ID")
    observations: list[ObservationData] = Field(..., description="관찰 데이터 배열")


class ObservationsResponse(BaseModel):
    """관찰 데이터 전송 응답"""

    status: str = Field(default="ok")
    processed: int = Field(..., description="처리된 개수")
    observation_ids: list[str] = Field(..., description="처리된 관찰 ID 목록")


class SystemStatus(BaseModel):
    """시스템 상태 정보"""

    state: str = Field(..., description="현재 상태 (recording/idle/analyzing)")
    session_id: str | None = Field(None, description="현재 세션 ID")
    start_time: str | None = Field(None, description="세션 시작 시각")
    event_count: int = Field(default=0, description="이벤트 수")
    observation_count: int = Field(default=0, description="관찰 수")
    pattern_count: int = Field(default=0, description="감지된 패턴 수")
    pending_questions: int = Field(default=0, description="대기 중인 질문 수")


class ControlCommand(str):
    """제어 명령"""

    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"


class ControlRequest(BaseModel):
    """제어 명령 요청"""

    command: str = Field(..., description="명령: start/stop/pause/resume")
    session_id: str | None = Field(None, description="세션 ID (stop/pause/resume 시 필요)")


class ControlResponse(BaseModel):
    """제어 명령 응답"""

    status: str = Field(default="ok")
    new_state: str = Field(..., description="새로운 상태")
    session_id: str | None = Field(None, description="세션 ID")


# ====== HITL API 모델 ======


class HITLQuestionResponse(BaseModel):
    """HITL 질문 응답 (shadow-web에서 수신)"""

    question_id: str = Field(..., description="질문 ID")
    user_id: str = Field(..., description="응답한 사용자 ID")
    response_type: str = Field(..., description="응답 타입: button/freetext")
    selected_option_id: str | None = Field(None, description="선택된 옵션 ID")
    freetext: str | None = Field(None, description="자유 텍스트 응답")
    timestamp: str = Field(..., description="응답 시각 (ISO 8601)")


class HITLQuestionItem(BaseModel):
    """HITL 질문 목록 항목"""

    id: str
    pattern_id: str
    question_text: str
    status: str
    created_at: str


class HITLQuestionsResponse(BaseModel):
    """HITL 질문 목록 응답"""

    count: int
    questions: list[HITLQuestionItem]


# ====== Spec API 모델 ======


class SpecSummary(BaseModel):
    """명세서 요약"""

    id: str
    pattern_id: str
    version: str
    status: str
    created_at: str
    updated_at: str


class SpecListResponse(BaseModel):
    """명세서 목록 응답"""

    count: int
    specs: list[SpecSummary]


class SpecDetailResponse(BaseModel):
    """명세서 상세 응답"""

    id: str
    pattern_id: str
    version: str
    created_at: str
    updated_at: str
    status: str
    content: dict[str, Any] = Field(..., description="명세서 내용")


class SpecCreateRequest(BaseModel):
    """명세서 생성 요청"""

    pattern_id: str
    content: dict[str, Any]


class SpecUpdateRequest(BaseModel):
    """명세서 업데이트 요청"""

    content: dict[str, Any]
    change_summary: str | None = None


# ====== 공통 응답 모델 ======


class SuccessResponse(BaseModel):
    """일반 성공 응답"""

    status: str = Field(default="ok")
    message: str | None = None
