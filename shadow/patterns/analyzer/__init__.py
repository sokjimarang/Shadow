"""LLM 기반 패턴 분석기 모듈"""

from shadow.patterns.analyzer.base import BasePatternAnalyzer, PatternAnalyzerBackend
from shadow.patterns.analyzer.claude import ClaudePatternAnalyzer


def create_pattern_analyzer(
    backend: str = "claude",
    **kwargs,
) -> BasePatternAnalyzer:
    """패턴 분석기 팩토리 함수

    Args:
        backend: 백엔드 타입 ("claude")
        **kwargs: 백엔드별 추가 인자

    Returns:
        패턴 분석기 인스턴스

    Raises:
        ValueError: 지원하지 않는 백엔드인 경우
    """
    if backend.lower() == "claude":
        return ClaudePatternAnalyzer(**kwargs)
    raise ValueError(f"지원하지 않는 백엔드: {backend}")


__all__ = [
    "BasePatternAnalyzer",
    "PatternAnalyzerBackend",
    "ClaudePatternAnalyzer",
    "create_pattern_analyzer",
]
