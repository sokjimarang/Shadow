"""LLM 기반 패턴 분석기 추상 베이스 클래스

패턴 감지와 불확실성 추출을 LLM으로 한 번에 처리합니다.
"""

from abc import ABC, abstractmethod
from enum import Enum

from shadow.analysis.models import LabeledAction
from shadow.patterns.models import DetectedPattern


class PatternAnalyzerBackend(Enum):
    """지원하는 패턴 분석기 백엔드"""

    CLAUDE = "claude"


class BasePatternAnalyzer(ABC):
    """LLM 기반 패턴 감지 및 불확실성 분석 추상 클래스

    VLM 분석된 액션 시퀀스에서 반복 패턴을 감지하고,
    각 패턴의 불확실한 지점(uncertainties)을 식별합니다.
    """

    @abstractmethod
    async def detect_patterns(
        self,
        actions: list[LabeledAction],
    ) -> list[DetectedPattern]:
        """액션 시퀀스에서 패턴 감지 + 불확실성 추출

        Args:
            actions: VLM 분석된 액션 시퀀스

        Returns:
            감지된 패턴 목록 (uncertainties 포함)
        """
        pass

    @property
    @abstractmethod
    def backend(self) -> PatternAnalyzerBackend:
        """분석기 백엔드 타입"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """사용 중인 모델 이름"""
        pass


__all__ = ["PatternAnalyzerBackend", "BasePatternAnalyzer"]
