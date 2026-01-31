"""파이프라인 컴포넌트 프로토콜 정의

각 컴포넌트의 인터페이스를 정의하여 Mock/실제 구현을 교체 가능하게 합니다.
"""

from typing import Protocol, runtime_checkable

from shadow.analysis.models import LabeledAction
from shadow.capture.models import KeyframePair
from shadow.capture.recorder import RecordingSession
from shadow.hitl.models import Question, Response
from shadow.patterns.models import DetectedPattern
from shadow.spec.models import Spec


@runtime_checkable
class RecorderProtocol(Protocol):
    """녹화기 프로토콜"""

    def record(self, duration: float) -> RecordingSession:
        """지정된 시간 동안 녹화

        Args:
            duration: 녹화 시간 (초)

        Returns:
            녹화된 세션
        """
        ...


@runtime_checkable
class KeyframeExtractorProtocol(Protocol):
    """키프레임 추출기 프로토콜"""

    def extract(self, session: RecordingSession) -> list[KeyframePair]:
        """세션에서 키프레임 쌍 추출

        Args:
            session: 녹화 세션

        Returns:
            키프레임 쌍 목록
        """
        ...


@runtime_checkable
class AnalyzerProtocol(Protocol):
    """VLM 분석기 프로토콜"""

    async def analyze_batch(self, keyframes: list[KeyframePair]) -> list[LabeledAction]:
        """키프레임 배치 분석

        Args:
            keyframes: 분석할 키프레임 쌍 목록

        Returns:
            라벨링된 액션 목록
        """
        ...


@runtime_checkable
class PatternAnalyzerProtocol(Protocol):
    """패턴 분석기 프로토콜 (LLM 기반)"""

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
        ...


@runtime_checkable
class QuestionGeneratorProtocol(Protocol):
    """질문 생성기 프로토콜"""

    def generate_from_patterns(self, patterns: list[DetectedPattern]) -> list[Question]:
        """패턴에서 HITL 질문 생성

        Args:
            patterns: 분석된 패턴 목록

        Returns:
            생성된 질문 목록
        """
        ...


@runtime_checkable
class SlackClientProtocol(Protocol):
    """Slack 클라이언트 프로토콜"""

    def send_question(self, channel: str, question: Question) -> dict:
        """질문을 Slack으로 전송

        Args:
            channel: Slack 채널 ID
            question: 전송할 질문

        Returns:
            전송 결과 (message_ts 등)
        """
        ...


@runtime_checkable
class ResponseHandlerProtocol(Protocol):
    """응답 핸들러 프로토콜"""

    def collect_responses(self, questions: list[Question]) -> list[tuple[Question, Response]]:
        """질문에 대한 응답 수집

        Args:
            questions: 응답을 수집할 질문 목록

        Returns:
            (질문, 응답) 튜플 목록
        """
        ...


@runtime_checkable
class SpecBuilderProtocol(Protocol):
    """명세서 빌더 프로토콜"""

    def build_from_pipeline(
        self,
        patterns: list[DetectedPattern],
        responses: list[tuple[Question, Response]],
        session_id: str | None = None,
    ) -> Spec:
        """파이프라인 결과로 명세서 생성

        Args:
            patterns: 감지된 패턴 목록
            responses: (질문, 응답) 튜플 목록
            session_id: 세션 ID (선택)

        Returns:
            생성된 명세서
        """
        ...
