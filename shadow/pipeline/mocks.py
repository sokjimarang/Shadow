"""파이프라인 Mock 구현체

테스트 및 데모용 Mock 구현을 제공합니다.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import field
from typing import TYPE_CHECKING

import numpy as np

from shadow.analysis.models import LabeledAction
from shadow.capture.models import Frame, InputEvent, InputEventType, KeyframePair
from shadow.capture.recorder import RecordingSession
from shadow.hitl.models import Question, Response
from shadow.patterns.models import DetectedPattern, Uncertainty, UncertaintyType

if TYPE_CHECKING:
    from shadow.pipeline.pipeline import Pipeline


class MockRecorder:
    """Mock 녹화기 - 더미 세션 반환"""

    def __init__(
        self,
        frame_count: int = 10,
        event_count: int = 6,
        duration: float = 5.0,
    ):
        """
        Args:
            frame_count: 생성할 더미 프레임 수
            event_count: 생성할 더미 이벤트 수
            duration: 가상 녹화 시간
        """
        self._frame_count = frame_count
        self._event_count = event_count
        self._duration = duration

    def record(self, duration: float | None = None) -> RecordingSession:
        """더미 세션 생성

        Args:
            duration: 무시됨 (Mock에서는 고정된 더미 데이터 반환)

        Returns:
            더미 데이터가 포함된 세션
        """
        actual_duration = duration or self._duration
        start_time = time.time()

        # 더미 프레임 생성
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        frames = [
            Frame(
                timestamp=start_time + (i * actual_duration / self._frame_count),
                image=dummy_image,
            )
            for i in range(self._frame_count)
        ]

        # 더미 이벤트 생성 (클릭 이벤트)
        events = [
            InputEvent(
                timestamp=start_time + (i * actual_duration / self._event_count),
                event_type=InputEventType.MOUSE_CLICK,
                x=100 + i * 50,
                y=200 + i * 30,
                button="left",
                app_name="MockApp",
                window_title="Mock Window",
            )
            for i in range(self._event_count)
        ]

        return RecordingSession(
            frames=frames,
            events=events,
            start_time=start_time,
            end_time=start_time + actual_duration,
        )


class MockKeyframeExtractor:
    """Mock 키프레임 추출기 - 이벤트 기반 더미 키프레임 생성"""

    def extract(self, session: RecordingSession) -> list[KeyframePair]:
        """세션에서 키프레임 쌍 추출 (Mock)

        각 클릭 이벤트에 대해 Before/After 프레임 쌍 생성
        """
        pairs = []
        click_events = [
            e for e in session.events
            if e.event_type == InputEventType.MOUSE_CLICK
        ]

        for i, event in enumerate(click_events):
            # Before: 이벤트 직전 프레임
            before_idx = min(i, len(session.frames) - 1)
            # After: 이벤트 직후 프레임
            after_idx = min(i + 1, len(session.frames) - 1)

            pairs.append(
                KeyframePair(
                    before_frame=session.frames[before_idx],
                    after_frame=session.frames[after_idx],
                    trigger_event=event,
                )
            )

        return pairs


class MockAnalyzer:
    """Mock VLM 분석기 - 더미 LabeledAction 반환"""

    def __init__(self, actions: list[LabeledAction] | None = None):
        """
        Args:
            actions: 반환할 더미 액션 목록 (None이면 기본 패턴 생성)
        """
        self._actions = actions

    def _create_default_actions(self, count: int) -> list[LabeledAction]:
        """기본 더미 액션 생성 (PRD: 3회 반복 패턴)"""
        # 2개 액션이 3회 반복되는 패턴
        base_actions = [
            LabeledAction(
                action="click",
                target="저장 버튼",
                context="MockApp",
                description="파일 저장 버튼 클릭",
                before_state="저장되지 않은 상태",
                after_state="저장 완료",
                state_change="파일이 저장됨",
            ),
            LabeledAction(
                action="click",
                target="확인 버튼",
                context="MockApp - 다이얼로그",
                description="확인 다이얼로그에서 확인 클릭",
                before_state="다이얼로그 표시됨",
                after_state="다이얼로그 닫힘",
                state_change="저장 확인됨",
            ),
        ]

        # 3회 반복
        actions = []
        for _ in range(3):
            for base in base_actions:
                actions.append(
                    LabeledAction(
                        action=base.action,
                        target=base.target,
                        context=base.context,
                        description=base.description,
                        before_state=base.before_state,
                        after_state=base.after_state,
                        state_change=base.state_change,
                    )
                )

        return actions[:count] if count < len(actions) else actions

    async def analyze_batch(self, keyframes: list[KeyframePair]) -> list[LabeledAction]:
        """키프레임 분석 (Mock)

        Args:
            keyframes: 키프레임 쌍 목록

        Returns:
            더미 LabeledAction 목록
        """
        if self._actions:
            return self._actions

        return self._create_default_actions(len(keyframes))


class MockSlackClient:
    """Mock Slack 클라이언트 - 실제 전송 없이 로깅"""

    def __init__(self, verbose: bool = True):
        """
        Args:
            verbose: 로그 출력 여부
        """
        self._verbose = verbose
        self._sent_questions: list[Question] = []

    def send_question(self, channel: str, question: Question) -> dict:
        """질문 전송 (Mock - 로깅만)

        Args:
            channel: Slack 채널 ID
            question: 전송할 질문

        Returns:
            Mock 전송 결과
        """
        self._sent_questions.append(question)

        if self._verbose:
            print(f"  [MockSlack] 질문 전송: {question.text[:50]}...")

        return {
            "ok": True,
            "channel": channel,
            "ts": f"mock-{time.time()}",
            "question_id": str(question.id),
        }

    @property
    def sent_questions(self) -> list[Question]:
        """전송된 질문 목록"""
        return self._sent_questions


class MockResponseHandler:
    """Mock 응답 핸들러 - 자동 응답 시뮬레이션"""

    def __init__(
        self,
        auto_select_index: int = 0,
        verbose: bool = True,
    ):
        """
        Args:
            auto_select_index: 자동 선택할 옵션 인덱스 (기본: 첫 번째)
            verbose: 로그 출력 여부
        """
        self._auto_select_index = auto_select_index
        self._verbose = verbose

    def collect_responses(
        self, questions: list[Question]
    ) -> list[tuple[Question, Response]]:
        """질문에 대한 응답 수집 (Mock - 자동 선택)

        Args:
            questions: 응답을 수집할 질문 목록

        Returns:
            (질문, 응답) 튜플 목록
        """
        responses = []

        for question in questions:
            # 옵션 인덱스 범위 확인
            option_idx = min(self._auto_select_index, len(question.options) - 1)
            selected_option = question.options[option_idx]

            response = Response(
                question_id=question.id,
                selected_option_id=selected_option.id,
                selected_value=selected_option.value,
                user_id="mock_user",
            )

            if self._verbose:
                print(f"  [MockResponse] {question.id[:8]}... → {selected_option.text}")

            responses.append((question, response))

        return responses


class MockPatternAnalyzer:
    """Mock 패턴 분석기 - LLM 없이 더미 패턴 반환"""

    def __init__(self, patterns: list[DetectedPattern] | None = None):
        """
        Args:
            patterns: 반환할 더미 패턴 목록 (None이면 기본 패턴 생성)
        """
        self._patterns = patterns

    def _create_default_patterns(
        self, actions: list[LabeledAction]
    ) -> list[DetectedPattern]:
        """기본 더미 패턴 생성"""
        if len(actions) < 6:
            return []

        # 2개 액션이 3회 반복되는 패턴 생성
        pattern_actions = actions[:2] if len(actions) >= 2 else actions[:1]

        return [
            DetectedPattern(
                name="저장 패턴",
                description="파일을 저장하고 확인하는 반복 작업",
                actions=pattern_actions,
                occurrence_indices=[0, 2, 4],
                confidence=0.9,
                uncertainties=[
                    Uncertainty(
                        type=UncertaintyType.CONDITION,
                        description="저장 전 조건 확인 여부",
                        hypothesis="저장 전에 특정 조건을 확인하나요?",
                        related_action_indices=[0],
                    ),
                    Uncertainty(
                        type=UncertaintyType.OPTIONAL,
                        description="확인 다이얼로그 생략 가능 여부",
                        hypothesis="확인 다이얼로그를 생략할 수 있나요?",
                        related_action_indices=[1],
                    ),
                ],
            )
        ]

    async def detect_patterns(
        self, actions: list[LabeledAction]
    ) -> list[DetectedPattern]:
        """패턴 감지 (Mock)

        Args:
            actions: 액션 시퀀스

        Returns:
            더미 DetectedPattern 목록
        """
        if self._patterns:
            return self._patterns

        return self._create_default_patterns(actions)


class MockSpecBuilder:
    """Mock 명세서 빌더 - SpecBuilder 래퍼"""

    def __init__(self, name: str = "MockWorkflow", description: str = "Mock E2E 명세서"):
        self._name = name
        self._description = description

    def build_from_pipeline(
        self,
        patterns: list[DetectedPattern],
        responses: list[tuple[Question, Response]],
        session_id: str | None = None,
    ):
        """파이프라인 결과로 명세서 생성"""
        from shadow.spec.builder import SpecBuilder

        builder = SpecBuilder(name=self._name, description=self._description)

        for pattern in patterns:
            builder.add_pattern(pattern)

        for question, response in responses:
            builder.add_response(question, response)

        if session_id:
            builder.add_session(session_id)

        return builder.build()


def create_mock_pipeline(
    name: str = "MockWorkflow",
    verbose: bool = True,
) -> "Pipeline":
    """Mock 컴포넌트로 구성된 파이프라인 생성

    Args:
        name: 명세서 이름
        verbose: 로그 출력 여부

    Returns:
        Mock 파이프라인 인스턴스
    """
    from shadow.hitl.generator import QuestionGenerator
    from shadow.pipeline.pipeline import Pipeline

    return Pipeline(
        recorder=MockRecorder(),
        keyframe_extractor=MockKeyframeExtractor(),
        analyzer=MockAnalyzer(),
        pattern_analyzer=MockPatternAnalyzer(),  # LLM 기반 패턴 분석기 Mock
        question_generator=QuestionGenerator(),  # 실제 구현 사용
        slack_client=MockSlackClient(verbose=verbose),
        response_handler=MockResponseHandler(verbose=verbose),
        spec_builder=MockSpecBuilder(name=name),
    )
