"""Pattern Layer 모델

감지된 패턴, 템플릿, 변형을 정의합니다.
기존 Pattern dataclass와 Uncertainty dataclass를 대체합니다.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field, model_validator

if TYPE_CHECKING:
    from shadow.analysis.models import LabeledAction


class PatternStatus(str, Enum):
    """패턴 상태"""

    DETECTED = "detected"  # 최초 감지
    CONFIRMING = "confirming"  # 확인 중 (HITL 진행)
    CONFIRMED = "confirmed"  # 사용자 확인 완료
    REJECTED = "rejected"  # 사용자가 거부


class UncertaintyType(str, Enum):
    """불확실성 유형"""

    CONDITION = "condition"  # 조건부 판단
    EXCEPTION = "exception"  # 예외 케이스
    QUALITY = "quality"  # 품질 기준
    ALTERNATIVE = "alternative"  # 대안 존재
    VARIANT = "variant"  # 변형 존재
    SEQUENCE = "sequence"  # 순서 불확실
    OPTIONAL = "optional"  # 선택적 단계


class ActionTemplate(BaseModel):
    """패턴 내 행동 템플릿

    패턴을 구성하는 개별 행동의 추상화된 표현입니다.
    """

    order: int  # 순서
    action_type: str  # 행동 타입
    target_pattern: str  # 대상 패턴 (정규식 또는 설명)
    app: str  # 앱 이름
    is_variable: bool = False  # 가변 요소 여부
    description: str | None = None  # 설명


class Variation(BaseModel):
    """패턴 변형

    동일한 패턴의 다른 실행 방식을 나타냅니다.
    """

    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    description: str  # 변형 설명
    occurrence_rate: float = Field(ge=0.0, le=1.0)  # 발생 비율
    example_session_id: UUID | None = None  # 예시 세션 ID
    differs_at: list[int] = Field(default_factory=list)  # 다른 부분 인덱스


class Uncertainty(BaseModel):
    """불확실 지점 (기존 dataclass 대체)

    패턴에서 HITL을 통해 확인이 필요한 부분입니다.
    """

    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    type: UncertaintyType
    description: str  # 불확실 지점 설명
    hypothesis: str | None = None  # AI 가설
    related_action_indices: list[int] = Field(default_factory=list)
    # 기존 dataclass 호환 필드
    source_action_indices: list[int] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False  # 해결 여부
    resolution: str | None = None  # 해결 내용

    model_config = {"use_enum_values": True}

    @model_validator(mode="after")
    def sync_indices(self) -> "Uncertainty":
        """related_action_indices와 source_action_indices 동기화"""
        if self.source_action_indices and not self.related_action_indices:
            self.related_action_indices = self.source_action_indices
        elif self.related_action_indices and not self.source_action_indices:
            self.source_action_indices = self.related_action_indices
        return self

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "description": self.description,
            "context": self.context,
            "confidence": 0.5,  # 기존 호환
            "source_action_indices": self.source_action_indices,
        }


class DetectedPattern(BaseModel):
    """감지된 패턴 (기존 Pattern dataclass 대체)

    패턴 감지와 저장/API 모두에서 사용됩니다.
    """

    id: UUID = Field(default_factory=uuid4)
    pattern_id: str | None = None  # 기존 호환용 ID

    # 핵심 필드 (기존 Pattern 호환)
    actions: list[Any] = Field(default_factory=list)  # list[LabeledAction]
    occurrence_indices: list[int] = Field(default_factory=list)  # 패턴이 시작되는 인덱스들

    # 저장용 필드
    name: str | None = None  # 패턴 이름 (자동 생성)
    description: str | None = None  # 패턴 설명
    core_sequence: list[ActionTemplate] = Field(default_factory=list)  # 핵심 행동 시퀀스
    apps_involved: list[str] = Field(default_factory=list)  # 관련 앱 목록
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    session_ids: list[UUID] = Field(default_factory=list)  # 관련 세션 ID 목록
    variations: list[Variation] = Field(default_factory=list)
    uncertainties: list[Uncertainty] = Field(default_factory=list)
    status: PatternStatus = PatternStatus.DETECTED
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    spec_id: UUID | None = None  # 연결된 명세서 ID

    model_config = {"use_enum_values": True}

    @model_validator(mode="after")
    def auto_generate_id(self) -> "DetectedPattern":
        """패턴 ID 자동 생성"""
        if self.pattern_id is None and self.actions:
            sig = "-".join(f"{a.action}:{a.target}" for a in self.actions)
            self.pattern_id = f"pattern-{hash(sig) & 0xFFFFFFFF:08x}"
        return self

    @computed_field
    @property
    def count(self) -> int:
        """반복 횟수 (기존 호환)"""
        return len(self.occurrence_indices) if self.occurrence_indices else self.occurrences

    @computed_field
    @property
    def occurrences(self) -> int:
        """발생 횟수"""
        return len(self.occurrence_indices) if self.occurrence_indices else 0

    def __str__(self) -> str:
        if self.actions:
            action_str = " → ".join(str(a) for a in self.actions)
            return f"[{action_str}] x {self.count}회"
        elif self.name:
            return f"{self.name} ({self.count}회)"
        return f"Pattern({self.count}회)"

    def add_occurrence(self, session_id: UUID | None = None) -> None:
        """패턴 발생 추가"""
        self.last_seen = datetime.now()
        if session_id and session_id not in self.session_ids:
            self.session_ids.append(session_id)

    def should_confirm(self, min_occurrences: int = 3) -> bool:
        """HITL 확인이 필요한지 여부"""
        return (
            self.count >= min_occurrences
            and self.status == PatternStatus.DETECTED
            and len(self.uncertainties) > 0
        )

    def to_storage_format(self) -> "DetectedPattern":
        """저장 형식으로 변환 (ActionTemplate 생성)"""
        if not self.core_sequence and self.actions:
            # 앱 목록 추출
            apps = list(set(a.context.split("/")[0] for a in self.actions))
            self.apps_involved = apps

            # ActionTemplate 생성
            self.core_sequence = [
                ActionTemplate(
                    order=i,
                    action_type=a.action,
                    target_pattern=a.target,
                    app=a.context.split("/")[0] if "/" in a.context else a.context,
                    description=a.description,
                )
                for i, a in enumerate(self.actions)
            ]

            # 이름 자동 생성
            if not self.name:
                actions_str = " → ".join(a.action for a in self.actions[:3])
                self.name = f"{apps[0] if apps else 'Unknown'}: {actions_str}"
                if len(self.actions) > 3:
                    self.name += "..."

        return self
