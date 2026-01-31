"""HITL 질문 및 응답 모델

패턴 불확실성에서 질문을 생성하고 사용자 응답을 처리합니다.
기존 dataclass를 Pydantic으로 대체합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """질문 유형"""

    HYPOTHESIS = "hypothesis"  # 가설 검증 (이 패턴이 맞나요?)
    QUALITY = "quality"  # 품질 확인 (결과물 품질 기준)
    CONDITION = "condition"  # 조건 확인 (언제 이 작업을 수행?)
    VARIANT = "variant"  # 변형 확인 (다른 방법도 있나요?)
    ANOMALY = "anomaly"  # 이상 케이스
    ALTERNATIVE = "alternative"  # 대안 선택


class QuestionStatus(str, Enum):
    """질문 상태"""

    PENDING = "pending"  # 대기 중
    SENT = "sent"  # 전송됨
    ANSWERED = "answered"  # 응답 완료
    EXPIRED = "expired"  # 만료됨


class ResponseType(str, Enum):
    """응답 유형"""

    BUTTON = "button"  # 버튼 선택
    FREETEXT = "freetext"  # 자유 텍스트


class InterpretedAction(str, Enum):
    """해석된 응답 액션"""

    ADD_RULE = "add_rule"  # 규칙 추가
    ADD_EXCEPTION = "add_exception"  # 예외 추가
    SET_QUALITY = "set_quality"  # 품질 기준 설정
    REJECT = "reject"  # 거부
    NEEDS_CLARIFICATION = "needs_clarification"  # 추가 확인 필요


class QuestionOption(BaseModel):
    """질문 선택지 (기존 dataclass 대체)"""

    id: str
    text: str  # 표시할 텍스트 (기존 호환)
    label: str | None = None  # 표시 텍스트 (문서 스펙)
    action: str | None = None  # 시스템이 취할 행동
    value: dict[str, Any] = Field(default_factory=dict)  # 선택 시 저장될 값
    is_default: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        # text와 label 동기화
        if self.label is None:
            self.label = self.text
        if self.text is None:
            self.text = self.label

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "id": self.id,
            "text": self.text,
            "value": self.value,
        }


class Question(BaseModel):
    """HITL 질문 (기존 dataclass 대체)

    패턴의 불확실 지점에 대해 사용자에게 확인을 요청합니다.
    """

    id: str | UUID = Field(default_factory=lambda: str(uuid4()))
    type: QuestionType
    text: str  # 질문 텍스트 (기존 호환)
    question_text: str | None = None  # 질문 내용 (문서 스펙)
    options: list[QuestionOption]

    # 기존 dataclass 필드
    source_pattern_id: str | None = None
    source_uncertainty_index: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

    # 문서 스펙 필드
    pattern_id: UUID | None = None
    uncertainty_id: str | None = None
    context: str | None = None  # 배경 설명
    allows_freetext: bool = False
    priority: int = Field(default=3, ge=1, le=5)
    status: QuestionStatus = QuestionStatus.PENDING
    sent_at: datetime | None = None
    answered_at: datetime | None = None
    slack_message_ts: str | None = None

    model_config = {"use_enum_values": True}

    def __init__(self, **data):
        super().__init__(**data)
        # text와 question_text 동기화
        if self.question_text is None:
            self.question_text = self.text
        if self.text is None:
            self.text = self.question_text

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "id": str(self.id),
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "text": self.text,
            "options": [o.to_dict() for o in self.options],
            "source_pattern_id": self.source_pattern_id,
            "source_uncertainty_index": self.source_uncertainty_index,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Question":
        """딕셔너리에서 생성 (기존 호환)"""
        return cls(
            id=data["id"],
            type=QuestionType(data["type"]),
            text=data["text"],
            options=[
                QuestionOption(
                    id=o["id"],
                    text=o["text"],
                    value=o.get("value", {}),
                )
                for o in data["options"]
            ],
            source_pattern_id=data.get("source_pattern_id"),
            source_uncertainty_index=data.get("source_uncertainty_index"),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
        )

    def mark_sent(self, slack_message_ts: str | None = None) -> None:
        """전송 완료 표시"""
        self.status = QuestionStatus.SENT
        self.sent_at = datetime.now()
        self.slack_message_ts = slack_message_ts

    def mark_answered(self) -> None:
        """응답 완료 표시"""
        self.status = QuestionStatus.ANSWERED
        self.answered_at = datetime.now()


class Response(BaseModel):
    """사용자 응답 (기존 dataclass 대체)"""

    id: UUID = Field(default_factory=uuid4)
    question_id: str | UUID
    selected_option_id: str | None = None
    selected_value: dict[str, Any] = Field(default_factory=dict)
    freetext: str | None = None
    response_type: ResponseType = ResponseType.BUTTON
    user_id: str | None = None
    channel_id: str | None = None
    responded_at: datetime = Field(default_factory=datetime.now)
    timestamp: datetime | None = None  # 문서 스펙 (responded_at 별칭)

    model_config = {"use_enum_values": True}

    def __init__(self, **data):
        super().__init__(**data)
        # timestamp와 responded_at 동기화
        if self.timestamp is None:
            self.timestamp = self.responded_at

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "question_id": str(self.question_id),
            "selected_option_id": self.selected_option_id,
            "selected_value": self.selected_value,
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "responded_at": self.responded_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Response":
        """딕셔너리에서 생성 (기존 호환)"""
        return cls(
            question_id=data["question_id"],
            selected_option_id=data["selected_option_id"],
            selected_value=data["selected_value"],
            user_id=data.get("user_id"),
            channel_id=data.get("channel_id"),
            responded_at=datetime.fromisoformat(data["responded_at"]) if "responded_at" in data else datetime.now(),
        )


class SpecUpdate(BaseModel):
    """명세서 업데이트 정보"""

    path: str  # JSON path (예: "workflow[0].condition")
    operation: Literal["add", "update", "delete"]
    value: Any


class InterpretedAnswer(BaseModel):
    """해석된 응답

    사용자 응답을 분석하여 시스템이 취할 행동을 결정합니다.
    """

    id: UUID = Field(default_factory=uuid4)
    answer_id: UUID
    action: InterpretedAction
    spec_update: SpecUpdate | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    applied: bool = False
    applied_at: datetime | None = None

    model_config = {"use_enum_values": True}

    def apply(self) -> None:
        """명세서에 반영 완료 표시"""
        self.applied = True
        self.applied_at = datetime.now()
