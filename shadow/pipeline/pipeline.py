"""Shadow E2E 파이프라인

Record → Keyframe → Analyze → Pattern → Question → (Slack) → Spec

실제 모듈만 사용하는 단순한 파이프라인 구조입니다.
Slack 연동은 선택적입니다 (토큰이 없으면 질문 생성까지만 실행).
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

from shadow.analysis.claude import ClaudeAnalyzer
from shadow.analysis.models import LabeledAction
from shadow.capture.models import KeyframePair
from shadow.capture.recorder import Recorder, RecordingSession
from shadow.config import settings
from shadow.hitl.generator import QuestionGenerator
from shadow.hitl.models import Question, Response
from shadow.patterns import ClaudePatternAnalyzer, DetectedPattern
from shadow.preprocessing.keyframe import KeyframeExtractor
from shadow.spec.builder import SpecBuilder
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
    stopped_at: str | None = None  # 어느 단계에서 멈췄는지

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
            "stopped_at": self.stopped_at,
        }


class Pipeline:
    """Shadow E2E 파이프라인

    실제 모듈만 사용하는 단순한 파이프라인입니다.
    Slack 연동은 선택적입니다 (토큰이 없으면 질문 생성까지만 실행).
    """

    def __init__(
        self,
        name: str = "Workflow",
        description: str = "",
        slack_channel: str | None = None,
        verbose: bool = True,
    ):
        """
        Args:
            name: 생성될 명세서 이름
            description: 명세서 설명
            slack_channel: Slack 채널 ID (None이면 Slack 스킵)
            verbose: 로그 출력 여부
        """
        self._name = name
        self._description = description
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
            self._log("\n[1/6] 녹화 중...")
            recorder = Recorder()
            result.session = recorder.record(duration)
            self._log(f"  - 프레임: {len(result.session.frames)}개")
            self._log(f"  - 이벤트: {len(result.session.events)}개")

            # 2. Keyframe 추출
            self._log("\n[2/6] 키프레임 추출 중...")
            extractor = KeyframeExtractor()
            result.keyframes = extractor.extract_pairs(result.session)
            self._log(f"  - 키프레임 쌍: {len(result.keyframes)}개")

            if not result.keyframes:
                result.error = "키프레임이 없습니다 (마우스 클릭이 감지되지 않음)"
                result.stopped_at = "keyframe"
                return result

            # 3. Analyze (VLM)
            self._log("\n[3/6] AI 분석 중...")
            if not settings.anthropic_api_key:
                result.error = "ANTHROPIC_API_KEY가 설정되지 않았습니다"
                result.stopped_at = "analyze"
                return result

            analyzer = ClaudeAnalyzer()
            self._log(f"  - 모델: {analyzer.model_name}")

            # 예상 비용 표시
            cost_info = analyzer.estimate_cost(result.keyframes)
            self._log(f"  - 예상 비용: ${cost_info['total_cost_usd']:.4f}")

            result.actions = await analyzer.analyze_batch(result.keyframes)
            self._log(f"  - 분석된 액션: {len(result.actions)}개")
            for action in result.actions:
                self._log(f"    - {action}")

            if not result.actions:
                result.error = "분석된 액션이 없습니다"
                result.stopped_at = "analyze"
                return result

            # 4. Pattern 감지 (LLM 기반)
            self._log("\n[4/6] 패턴 감지 중 (LLM)...")
            pattern_analyzer = ClaudePatternAnalyzer()
            result.patterns = await pattern_analyzer.detect_patterns(result.actions)
            self._log(f"  - 감지된 패턴: {len(result.patterns)}개")
            for pattern in result.patterns:
                self._log(f"    - {len(pattern.actions)}개 액션, {pattern.count}회 반복")

            if not result.patterns:
                result.error = "감지된 패턴이 없습니다 (3회 이상 반복 필요)"
                result.stopped_at = "pattern"
                return result

            # 5. Question 생성
            self._log("\n[5/6] HITL 질문 생성 중...")
            generator = QuestionGenerator()
            result.questions = generator.generate_from_patterns(result.patterns)
            self._log(f"  - 생성된 질문: {len(result.questions)}개")
            for q in result.questions:
                self._log(f"    - [{q.type.value}] {q.text[:50]}...")

            # 6. Slack 전송 + Response 수집 (선택적)
            if self._slack_channel and settings.slack_bot_token:
                self._log("\n[6/6] Slack 전송 및 응답 수집 중...")
                # TODO: 실제 Slack 연동 구현
                # from shadow.slack.client import SlackClient
                # client = SlackClient()
                # for question in result.questions:
                #     client.send_question(self._slack_channel, question)
                # result.responses = client.collect_responses(result.questions)
                self._log("  [경고] Slack 연동이 아직 구현되지 않았습니다")
                result.stopped_at = "slack"
            else:
                self._log("\n[6/6] Slack 스킵 (토큰 없음 또는 채널 미지정)")
                result.stopped_at = "question"

            # 7. Spec 생성 (응답이 없어도 패턴 기반으로 생성)
            self._log("\n[+] 명세서 생성 중...")
            builder = SpecBuilder(name=self._name, description=self._description)

            for pattern in result.patterns:
                builder.add_pattern(pattern)

            for question, response in result.responses:
                builder.add_response(question, response)

            builder.add_session(result.session_id)
            result.spec = builder.build()

            self._log(f"  - 워크플로우 단계: {len(result.spec.workflow)}개")
            self._log(f"  - 의사결정 규칙: {len(result.spec.decisions)}개")

            result.success = True

        except Exception as e:
            result.error = str(e)
            self._log(f"\n[오류] {e}")
            import traceback
            traceback.print_exc()

        return result

    def run_sync(self, duration: float = 5.0) -> PipelineResult:
        """동기식 파이프라인 실행

        Args:
            duration: 녹화 시간 (초)

        Returns:
            파이프라인 실행 결과
        """
        return asyncio.run(self.run(duration))


def run_pipeline(
    duration: float = 5.0,
    name: str = "Workflow",
    description: str = "",
    slack_channel: str | None = None,
    verbose: bool = True,
) -> PipelineResult:
    """파이프라인 실행 헬퍼 함수

    Args:
        duration: 녹화 시간 (초)
        name: 명세서 이름
        description: 명세서 설명
        slack_channel: Slack 채널 ID (None이면 Slack 스킵)
        verbose: 로그 출력 여부

    Returns:
        파이프라인 실행 결과

    Examples:
        >>> result = run_pipeline(duration=5.0, name="MyWorkflow")
        >>> if result.success:
        ...     print(f"패턴 {len(result.patterns)}개 감지")
    """
    pipeline = Pipeline(
        name=name,
        description=description,
        slack_channel=slack_channel,
        verbose=verbose,
    )
    return pipeline.run_sync(duration)
