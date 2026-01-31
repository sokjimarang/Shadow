"""Repository 레이어

Supabase 테이블과 상호작용하는 데이터 접근 레이어
"""

from shadow.api.repositories.detected_patterns import DetectedPatternRepository
from shadow.api.repositories.hitl import HITLRepository
from shadow.api.repositories.interpreted_answers import InterpretedAnswerRepository
from shadow.api.repositories.labeled_actions import LabeledActionRepository
from shadow.api.repositories.observations import ObservationRepository
from shadow.api.repositories.session_sequences import SessionSequenceRepository
from shadow.api.repositories.sessions import SessionRepository
from shadow.api.repositories.specs import SpecRepository
from shadow.api.repositories.users import ConfigRepository, UserRepository

__all__ = [
    # System Layer
    "SessionRepository",
    "UserRepository",
    "ConfigRepository",
    # Raw Data Layer
    "ObservationRepository",
    # Analysis Layer
    "LabeledActionRepository",
    "SessionSequenceRepository",
    # Pattern Layer
    "DetectedPatternRepository",
    # HITL Layer
    "HITLRepository",
    "InterpretedAnswerRepository",
    # Spec Layer
    "SpecRepository",
]
