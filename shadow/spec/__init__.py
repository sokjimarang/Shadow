"""명세서(Spec) 모듈

패턴과 HITL 응답을 기반으로 자동화 명세서를 생성합니다.
"""

from shadow.spec.builder import SpecBuilder, SpecStorage
from shadow.spec.models import (
    # Dataclass 모델 (내부 처리용)
    DecisionRule,
    Spec,
    SpecMeta,
    WorkflowStep,
    # Pydantic 모델 (저장/API용)
    AgentSpec,
    ChangeSource,
    ChangeType,
    SpecChange,
    SpecHistory,
    SpecStatus,
)

__all__ = [
    # Dataclass 모델
    "DecisionRule",
    "Spec",
    "SpecMeta",
    "WorkflowStep",
    # Pydantic 모델
    "AgentSpec",
    "SpecStatus",
    "SpecHistory",
    "SpecChange",
    "ChangeType",
    "ChangeSource",
    # 빌더
    "SpecBuilder",
    "SpecStorage",
]
