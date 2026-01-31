"""Analysis Layer 모델

라벨링된 행동과 세션 시퀀스를 정의합니다.
기존 ActionLabel dataclass를 대체하는 Pydantic 모델입니다.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field


class ActionType(str, Enum):
    """행동 타입"""

    CLICK = "click"
    TYPE = "type"
    COPY = "copy"
    PASTE = "paste"
    SCROLL = "scroll"
    NAVIGATE = "navigate"
    SELECT = "select"
    DRAG = "drag"


class SessionStatus(str, Enum):
    """세션 상태"""

    RECORDING = "recording"
    COMPLETED = "completed"
    ANALYZED = "analyzed"


class LabeledAction(BaseModel):
    """라벨링된 행동 (ActionLabel 대체)

    VLM 분석 결과로 생성된 행동 라벨입니다.
    패턴 감지와 저장/API 모두에서 사용됩니다.
    """

    # 식별자 (저장 시 필요)
    id: UUID = Field(default_factory=uuid4)

    # 핵심 필드 (기존 ActionLabel 호환)
    action: str  # 동작 타입 (click, scroll, type 등)
    target: str  # 대상 UI 요소
    context: str  # 앱/화면 컨텍스트
    description: str  # 동작 설명

    # Before/After 분석 필드
    before_state: str | None = None  # 클릭 전 상태
    after_state: str | None = None  # 클릭 후 상태
    state_change: str | None = None  # 상태 변화 설명

    # 저장용 필드 (선택적)
    observation_id: UUID | None = None
    timestamp: datetime | None = None
    intent_guess: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    session_id: UUID | None = None

    model_config = {"use_enum_values": True}

    def __str__(self) -> str:
        return f"{self.action}: {self.target} ({self.context})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LabeledAction):
            return False
        # 동작과 대상이 같으면 동일한 액션으로 취급 (패턴 감지용)
        return self.action == other.action and self.target == other.target

    def __hash__(self) -> int:
        return hash((self.action, self.target))

    @computed_field
    @property
    def action_type(self) -> ActionType:
        """action 문자열을 ActionType으로 변환"""
        action_type_map = {
            "click": ActionType.CLICK,
            "type": ActionType.TYPE,
            "copy": ActionType.COPY,
            "paste": ActionType.PASTE,
            "scroll": ActionType.SCROLL,
            "navigate": ActionType.NAVIGATE,
            "select": ActionType.SELECT,
            "drag": ActionType.DRAG,
        }
        return action_type_map.get(self.action.lower(), ActionType.CLICK)

    @computed_field
    @property
    def target_element(self) -> str:
        """target의 별칭 (문서 스펙 호환)"""
        return self.target

    @computed_field
    @property
    def semantic_label(self) -> str:
        """description의 별칭 (문서 스펙 호환)"""
        return self.description

    @computed_field
    @property
    def app(self) -> str:
        """context에서 앱 이름 추출"""
        return self.context.split("/")[0] if "/" in self.context else self.context

    @computed_field
    @property
    def app_context(self) -> str | None:
        """context에서 앱 내 컨텍스트 추출"""
        return self.context.split("/")[1] if "/" in self.context else None

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "action": self.action,
            "target": self.target,
            "context": self.context,
            "description": self.description,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "state_change": self.state_change,
        }


class SessionSequence(BaseModel):
    """세션 내 행동 시퀀스

    하나의 녹화 세션에서 발생한 모든 행동의 순서를 추적합니다.
    """

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    start_time: datetime
    end_time: datetime | None = None
    action_ids: list[UUID] = Field(default_factory=list)
    apps_used: list[str] = Field(default_factory=list)
    action_count: int = 0
    status: SessionStatus = SessionStatus.RECORDING

    model_config = {"use_enum_values": True}

    def add_action(self, action: LabeledAction) -> None:
        """행동 추가"""
        self.action_ids.append(action.id)
        self.action_count = len(self.action_ids)
        if action.app not in self.apps_used:
            self.apps_used.append(action.app)

    def complete(self, end_time: datetime | None = None) -> None:
        """시퀀스 완료"""
        self.end_time = end_time or datetime.now()
        self.status = SessionStatus.COMPLETED

    def mark_analyzed(self) -> None:
        """분석 완료 표시"""
        self.status = SessionStatus.ANALYZED


