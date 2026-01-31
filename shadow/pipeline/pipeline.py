"""E2E 파이프라인 오케스트레이터

전체 플로우를 조율하고 각 단계의 결과를 관리합니다.
Record → Analyze → Patterns → Questions → Slack → Response → Spec
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

from shadow.analysis.models import LabeledAction
from shadow.capture.models import KeyframePair
from shadow.capture.recorder import RecordingSession
from shadow.hitl.models import Question, Response
from shadow.patterns.models import DetectedPattern
from shadow.spec.models import Spec


@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""

    # 각 단계별 결과
    session: RecordingSession | None = None
    keyframes: list[KeyframePair] = field(default_factory=list)
    actions: list[LabeledAction] = field(default_factory=list)
    patterns: list[DetectedPattern] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    responses: list[tuple[Question, Response]] = field(default_factory=list)
    spec: Spec | None = None

    # 메타데이터
    session_id: str = field(default_factory=lambda: f"session-{uuid.uuid4().hex[:8]}")
    success: bool = False
    error: str | None = None

    # 단계별 통계
    @property
    def stats(self) -> dict[str, Any]:
        """실행 통계"""
        return {
            "frames": len(self.session.frames) if self.session else 0,
            "events": len(self.session.events) if self.session else 0,
            "keyframes": len(self.keyframes),
            "actions": len(self.actions),
            "patterns": len(self.patterns),
            "questions": len(self.questions),
            "responses": len(self.responses),
            "has_spec": self.spec is not None,
        }


class Pipeline:
    """E2E 파이프라인 오케스트레이터

    각 컴포넌트를 의존성 주입받아 전체 플로우를 실행합니다.
    Mock/실제 구현을 자유롭게 교체할 수 있습니다.
    """

    def __init__(
        self,
        recorder,
        keyframe_extractor,
        analyzer,
        pattern_detector,
        question_generator,
        slack_client,
        response_handler,
        spec_builder,
        slack_channel: str = "mock-channel",
        verbose: bool = True,
    ):
        """
        Args:
            recorder: 녹화기 (RecorderProtocol)
            keyframe_extractor: 키프레임 추출기 (KeyframeExtractorProtocol)
            analyzer: VLM 분석기 (AnalyzerProtocol)
            pattern_detector: 패턴 감지기 (PatternDetectorProtocol)
            question_generator: 질문 생성기 (QuestionGeneratorProtocol)
            slack_client: Slack 클라이언트 (SlackClientProtocol)
            response_handler: 응답 핸들러 (ResponseHandlerProtocol)
            spec_builder: 명세서 빌더 (SpecBuilderProtocol)
            slack_channel: Slack 채널 ID
            verbose: 로그 출력 여부
        """
        self._recorder = recorder
        self._keyframe_extractor = keyframe_extractor
        self._analyzer = analyzer
        self._pattern_detector = pattern_detector
        self._question_generator = question_generator
        self._slack_client = slack_client
        self._response_handler = response_handler
        self._spec_builder = spec_builder
        self._slack_channel = slack_channel
        self._verbose = verbose

    def _log(self, message: str) -> None:
        """로그 출력"""
        if self._verbose:
            print(message)

    async def run(self, duration: float = 5.0) -> PipelineResult:
        """전체 파이프라인 실행

        Args:
            duration: 녹화 시간 (초)

        Returns:
            파이프라인 실행 결과
        """
        result = PipelineResult()

        try:
            # 1. Record
            self._log("\n[1/7] 녹화 중...")
            result.session = self._recorder.record(duration)
            self._log(f"  - 프레임: {len(result.session.frames)}개")
            self._log(f"  - 이벤트: {len(result.session.events)}개")

            # 2. Keyframe 추출
            self._log("\n[2/7] 키프레임 추출 중...")
            result.keyframes = self._keyframe_extractor.extract(result.session)
            self._log(f"  - 키프레임 쌍: {len(result.keyframes)}개")

            if not result.keyframes:
                result.error = "키프레임이 없습니다"
                return result

            # 3. Analyze (VLM)
            self._log("\n[3/7] AI 분석 중...")
            result.actions = await self._analyzer.analyze_batch(result.keyframes)
            self._log(f"  - 액션: {len(result.actions)}개")
            for action in result.actions:
                self._log(f"    - {action}")

            if not result.actions:
                result.error = "분석된 액션이 없습니다"
                return result

            # 4. Pattern 감지
            self._log("\n[4/7] 패턴 감지 중...")
            result.patterns = self._pattern_detector.detect(result.actions)
            self._log(f"  - 패턴: {len(result.patterns)}개")
            for pattern in result.patterns:
                self._log(f"    - {pattern}")

            if not result.patterns:
                result.error = "감지된 패턴이 없습니다 (3회 이상 반복 필요)"
                return result

            # 5. Question 생성
            self._log("\n[5/7] HITL 질문 생성 중...")
            result.questions = self._question_generator.generate_from_patterns(result.patterns)
            self._log(f"  - 질문: {len(result.questions)}개")
            for q in result.questions:
                self._log(f"    - [{q.type}] {q.text[:40]}...")

            # 6. Slack 전송 + Response 수집
            self._log("\n[6/7] Slack 전송 및 응답 수집 중...")
            for question in result.questions:
                self._slack_client.send_question(self._slack_channel, question)

            result.responses = self._response_handler.collect_responses(result.questions)
            self._log(f"  - 응답: {len(result.responses)}개")

            # 7. Spec 생성
            self._log("\n[7/7] 명세서 생성 중...")
            result.spec = self._spec_builder.build_from_pipeline(
                patterns=result.patterns,
                responses=result.responses,
                session_id=result.session_id,
            )
            self._log(f"  - 워크플로우 단계: {len(result.spec.workflow)}개")
            # decisions가 dict일 수도 있고 다른 구조일 수도 있음
            if hasattr(result.spec.decisions, 'get'):
                rules_count = len(result.spec.decisions.get('rules', []))
            elif hasattr(result.spec.decisions, 'rules'):
                rules_count = len(result.spec.decisions.rules)
            elif isinstance(result.spec.decisions, list):
                rules_count = len(result.spec.decisions)
            else:
                rules_count = 0
            self._log(f"  - 의사결정 규칙: {rules_count}개")

            result.success = True

        except Exception as e:
            result.error = str(e)
            self._log(f"\n[오류] {e}")

        return result

    def run_sync(self, duration: float = 5.0) -> PipelineResult:
        """동기식 파이프라인 실행 (asyncio.run 래퍼)

        Args:
            duration: 녹화 시간 (초)

        Returns:
            파이프라인 실행 결과
        """
        return asyncio.run(self.run(duration))
