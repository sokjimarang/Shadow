"""명세서 데이터 모델

패턴 분석 + HITL 응답을 종합한 자동화 명세서입니다.
기존 dataclass를 Pydantic으로 대체합니다.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SpecStatus(str, Enum):
    """명세서 상태"""

    DRAFT = "draft"  # 초안
    ACTIVE = "active"  # 활성화
    ARCHIVED = "archived"  # 보관됨


class ChangeType(str, Enum):
    """변경 유형"""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ChangeSource(str, Enum):
    """변경 소스"""

    PATTERN_DETECTION = "pattern_detection"  # 패턴 감지
    HITL_ANSWER = "hitl_answer"  # HITL 응답
    MANUAL = "manual"  # 수동 편집


class DecisionRule(BaseModel):
    """의사결정 규칙 (기존 dataclass 대체)

    HITL 질문 응답으로부터 생성된 규칙입니다.
    """

    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    condition: str  # 조건 (예: "파일 크기가 1MB 이상일 때")
    action: str  # 수행할 액션 (예: "압축 후 업로드")
    confirmed_by: str  # question_id
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "id": self.id,
            "condition": self.condition,
            "action": self.action,
            "confirmed_by": self.confirmed_by,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DecisionRule":
        """딕셔너리에서 생성 (기존 호환)"""
        return cls(
            id=data["id"],
            condition=data["condition"],
            action=data["action"],
            confirmed_by=data["confirmed_by"],
            confidence=data.get("confidence", 1.0),
        )


class WorkflowStep(BaseModel):
    """워크플로우 단계 (기존 dataclass 대체)"""

    order: int  # 실행 순서
    action: str  # 수행할 동작
    target: str  # 대상 UI 요소
    context: str  # 컨텍스트 (앱, 화면 등)
    description: str = ""  # 상세 설명
    optional: bool = False  # 선택적 단계 여부

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "order": self.order,
            "action": self.action,
            "target": self.target,
            "context": self.context,
            "description": self.description,
            "optional": self.optional,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        """딕셔너리에서 생성 (기존 호환)"""
        return cls(
            order=data["order"],
            action=data["action"],
            target=data["target"],
            context=data["context"],
            description=data.get("description", ""),
            optional=data.get("optional", False),
        )


class SpecMeta(BaseModel):
    """명세서 메타데이터 (기존 dataclass 대체)"""

    name: str
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    description: str = ""
    source_sessions: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "source_sessions": self.source_sessions,
        }


class Spec(BaseModel):
    """자동화 명세서 (기존 dataclass 대체)

    패턴 분석 + HITL 응답을 종합한 최종 결과물입니다.
    """

    meta: SpecMeta
    workflow: list[WorkflowStep] = Field(default_factory=list)
    decisions: list[DecisionRule] = Field(default_factory=list)
    raw_patterns: list[dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환 (기존 호환)"""
        return {
            "meta": self.meta.to_dict(),
            "workflow": [w.to_dict() for w in self.workflow],
            "decisions": {"rules": [d.to_dict() for d in self.decisions]},
            "raw_patterns": self.raw_patterns,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Spec":
        """딕셔너리에서 생성 (기존 호환)"""
        meta_data = data["meta"]
        return cls(
            meta=SpecMeta(
                name=meta_data["name"],
                version=meta_data.get("version", "1.0"),
                created_at=datetime.fromisoformat(meta_data["created_at"]) if "created_at" in meta_data else datetime.now(),
                description=meta_data.get("description", ""),
                source_sessions=meta_data.get("source_sessions", []),
            ),
            workflow=[WorkflowStep.from_dict(w) for w in data.get("workflow", [])],
            decisions=[DecisionRule.from_dict(d) for d in data.get("decisions", {}).get("rules", [])],
            raw_patterns=data.get("raw_patterns", []),
        )


class SpecChange(BaseModel):
    """명세서 변경 내역 항목"""

    path: str  # JSON path
    old_value: Any | None = None
    new_value: Any | None = None
    description: str | None = None


class AgentSpec(BaseModel):
    """에이전트 명세서

    패턴 분석 + HITL 응답을 종합한 최종 자동화 명세서입니다.
    """

    id: UUID = Field(default_factory=uuid4)
    pattern_id: UUID
    version: str = "1.0.0"  # semver
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: SpecStatus = SpecStatus.DRAFT
    content: dict[str, Any] = Field(default_factory=dict)  # 명세서 내용

    model_config = {"use_enum_values": True}

    @classmethod
    def from_spec(cls, spec: Spec, pattern_id: UUID) -> "AgentSpec":
        """Spec에서 변환"""
        return cls(
            pattern_id=pattern_id,
            version=spec.meta.version,
            created_at=spec.meta.created_at,
            updated_at=datetime.now(),
            content=spec.to_dict(),
        )

    def activate(self) -> None:
        """명세서 활성화"""
        self.status = SpecStatus.ACTIVE
        self.updated_at = datetime.now()

    def archive(self) -> None:
        """명세서 보관"""
        self.status = SpecStatus.ARCHIVED
        self.updated_at = datetime.now()

    def bump_version(self, bump_type: Literal["major", "minor", "patch"] = "patch") -> str:
        """버전 증가"""
        parts = self.version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1

        self.version = f"{major}.{minor}.{patch}"
        self.updated_at = datetime.now()
        return self.version


class SpecHistory(BaseModel):
    """명세서 변경 이력"""

    id: UUID = Field(default_factory=uuid4)
    spec_id: UUID
    version: str  # 변경된 버전
    previous_version: str | None = None  # 이전 버전
    change_type: ChangeType
    change_summary: str  # 변경 요약
    changes: list[SpecChange] = Field(default_factory=list)
    source: ChangeSource
    source_id: str | None = None  # 소스 ID (answer_id 등)
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"use_enum_values": True}

    @classmethod
    def create_initial(cls, spec: AgentSpec) -> "SpecHistory":
        """초기 생성 이력"""
        return cls(
            spec_id=spec.id,
            version=spec.version,
            change_type=ChangeType.CREATE,
            change_summary="명세서 초기 생성",
            source=ChangeSource.PATTERN_DETECTION,
        )

    @classmethod
    def from_hitl(
        cls,
        spec: AgentSpec,
        previous_version: str,
        answer_id: str,
        changes: list[SpecChange],
        summary: str,
    ) -> "SpecHistory":
        """HITL 응답으로 인한 변경 이력"""
        return cls(
            spec_id=spec.id,
            version=spec.version,
            previous_version=previous_version,
            change_type=ChangeType.UPDATE,
            change_summary=summary,
            changes=changes,
            source=ChangeSource.HITL_ANSWER,
            source_id=answer_id,
        )
