"""AI 분석 모듈

지원 백엔드:
- Claude Opus 4.5 (권장)
- Gemini
- Qwen (로컬) - 추후 지원 예정
"""

from shadow.analysis.base import ActionLabel, AnalyzerBackend, BaseVisionAnalyzer
from shadow.analysis.claude import ClaudeAnalyzer
from shadow.analysis.gemini import GeminiAnalyzer


def create_analyzer(
    backend: AnalyzerBackend | str = AnalyzerBackend.CLAUDE,
    **kwargs,
) -> BaseVisionAnalyzer:
    """분석기 팩토리 함수

    Args:
        backend: 사용할 백엔드 (claude, gemini, qwen_local)
        **kwargs: 백엔드별 추가 인자

    Returns:
        생성된 분석기 인스턴스

    Examples:
        >>> analyzer = create_analyzer("claude")
        >>> analyzer = create_analyzer(AnalyzerBackend.GEMINI)
        >>> analyzer = create_analyzer("claude", max_image_size=512)
    """
    if isinstance(backend, str):
        backend = AnalyzerBackend(backend.lower())

    if backend == AnalyzerBackend.CLAUDE:
        return ClaudeAnalyzer(**kwargs)
    elif backend == AnalyzerBackend.GEMINI:
        return GeminiAnalyzer(**kwargs)
    elif backend == AnalyzerBackend.QWEN_LOCAL:
        raise NotImplementedError("Qwen 로컬 백엔드는 아직 구현되지 않았습니다.")
    else:
        raise ValueError(f"지원하지 않는 백엔드: {backend}")


__all__ = [
    "ActionLabel",
    "AnalyzerBackend",
    "BaseVisionAnalyzer",
    "ClaudeAnalyzer",
    "GeminiAnalyzer",
    "create_analyzer",
]
