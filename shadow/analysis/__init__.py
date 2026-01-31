"""AI 분석 모듈

지원 백엔드:
- Claude Opus 4.5
- NVIDIA NIM Nemotron VL
"""

from shadow.analysis.base import AnalyzerBackend, BaseVisionAnalyzer
from shadow.analysis.claude import ClaudeAnalyzer
from shadow.analysis.nemotron import NemotronAnalyzer
from shadow.analysis.models import (
    ActionType,
    LabeledAction,
    SessionSequence,
    SessionStatus,
)


def create_analyzer(
    backend: AnalyzerBackend | str = AnalyzerBackend.CLAUDE,
    **kwargs,
) -> BaseVisionAnalyzer:
    """분석기 팩토리 함수

    Args:
        backend: 사용할 백엔드
        **kwargs: 백엔드별 추가 인자

    Returns:
        생성된 분석기 인스턴스

    Examples:
        >>> analyzer = create_analyzer("claude")
        >>> analyzer = create_analyzer("claude", max_image_size=512)
    """
    if isinstance(backend, str):
        backend = AnalyzerBackend(backend.lower())

    if backend == AnalyzerBackend.CLAUDE:
        return ClaudeAnalyzer(**kwargs)
    elif backend == AnalyzerBackend.NEMOTRON:
        return NemotronAnalyzer(**kwargs)
    else:
        raise ValueError(f"지원하지 않는 백엔드: {backend}")


__all__ = [
    # Pydantic 모델
    "LabeledAction",
    "ActionType",
    "SessionSequence",
    "SessionStatus",
    # 분석기 베이스
    "AnalyzerBackend",
    "BaseVisionAnalyzer",
    # 분석기 구현체
    "ClaudeAnalyzer",
    "NemotronAnalyzer",
    "create_analyzer",
]
