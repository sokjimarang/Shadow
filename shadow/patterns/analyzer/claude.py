"""Claude를 사용한 LLM 패턴 분석기

패턴 감지 + 불확실성 추출을 한 번의 LLM 호출로 처리합니다.

비용 최적화:
- Prompt Caching: 시스템 프롬프트 캐싱으로 90% 비용 절감
"""

import json
import logging
from uuid import uuid4

import anthropic

from shadow.analysis.models import LabeledAction
from shadow.config import settings
from shadow.patterns.analyzer.base import BasePatternAnalyzer, PatternAnalyzerBackend
from shadow.patterns.models import DetectedPattern, Uncertainty, UncertaintyType

logger = logging.getLogger(__name__)

# 패턴 감지 + 불확실성 추출 시스템 프롬프트
# Anthropic Prompt Best Practices 적용: XML 태그 구조화, 컨텍스트 제공, Chain of Thought, Multishot 예시
PATTERN_DETECTION_PROMPT = """<role>
당신은 사용자의 반복 업무 패턴을 분석하는 전문가입니다.
</role>

<context>
이 분석은 업무 자동화 시스템의 핵심 단계입니다.
감지된 패턴과 불확실성은 사용자에게 질문(HITL)을 생성하고, 최종 자동화 명세서를 작성하는 데 사용됩니다.
정확한 패턴 감지와 불확실성 식별이 자동화 품질을 결정합니다.
</context>

<instructions>
주어진 액션 시퀀스에서 반복되는 패턴을 찾고, 각 패턴의 불확실한 지점을 식별하세요.

분석 전 다음을 고려하세요:
1. 어떤 액션들이 유사한 목적을 가지는가?
2. 반복되는 시퀀스의 시작점은 어디인가?
3. 어떤 부분이 조건부이거나 선택적인가?
</instructions>

<pattern_criteria>
- 3회 이상 유사하게 반복되는 액션 시퀀스
- 정확히 같지 않아도 의미적으로 같은 작업이면 패턴으로 인식
- 패턴의 시작 인덱스들을 명시
</pattern_criteria>

<uncertainty_types>
- CONDITION: 조건부 판단 ("금액이 X 이상일 때만...")
- QUALITY: 품질 기준 ("결과물에 날짜가 필수인가?")
- VARIANT: 변형 존재 ("다른 방법도 사용함")
- SEQUENCE: 순서 불확실 ("순서가 바뀌어도 되는가?")
- OPTIONAL: 선택적 단계 ("가끔 생략됨")
- EXCEPTION: 예외 케이스 ("특수한 경우 다르게 처리")
- ALTERNATIVE: 대안 존재 ("다른 방법으로도 가능")
</uncertainty_types>

<output_format>
다음 JSON 형식으로만 응답하세요:
{
    "patterns": [
        {
            "name": "패턴 이름 (간결하게)",
            "description": "패턴이 하는 일 설명",
            "action_indices": [0, 3, 6],
            "actions_per_occurrence": 2,
            "confidence": 0.9,
            "uncertainties": [
                {
                    "type": "CONDITION",
                    "description": "불확실 지점 설명",
                    "hypothesis": "~인 것 같습니다. 맞나요?",
                    "related_action_indices": [1]
                }
            ]
        }
    ],
    "analysis_summary": "전체 분석 요약"
}
</output_format>

<example>
입력:
[0] click: 이메일 목록 @ Gmail - 첫 번째 이메일 선택
[1] click: 전달 버튼 @ Gmail - 이메일 전달 시작
[2] type: 받는 사람 필드 @ Gmail - team@company.com 입력
[3] click: 전송 버튼 @ Gmail - 이메일 전송
[4] click: 이메일 목록 @ Gmail - 두 번째 이메일 선택
[5] click: 전달 버튼 @ Gmail - 이메일 전달 시작
[6] type: 받는 사람 필드 @ Gmail - team@company.com 입력
[7] click: 전송 버튼 @ Gmail - 이메일 전송

출력:
{
    "patterns": [
        {
            "name": "이메일 전달",
            "description": "이메일을 선택하여 특정 주소로 전달하는 패턴",
            "action_indices": [0, 4],
            "actions_per_occurrence": 4,
            "confidence": 0.95,
            "uncertainties": [
                {
                    "type": "CONDITION",
                    "description": "어떤 이메일을 전달 대상으로 선택하는지 기준 불명확",
                    "hypothesis": "모든 이메일을 전달하나요, 아니면 특정 조건의 이메일만 전달하나요?",
                    "related_action_indices": [0, 4]
                }
            ]
        }
    ],
    "analysis_summary": "Gmail에서 이메일을 선택하여 team@company.com으로 전달하는 반복 패턴 1개 감지"
}
</example>

<guidelines>
- JSON 외의 텍스트를 출력하지 마세요
- 패턴이 없으면 patterns를 빈 배열로 반환
- action_indices는 각 패턴 발생의 시작 인덱스
- actions_per_occurrence는 한 번의 패턴에 포함된 액션 수
- hypothesis는 사용자에게 질문할 형태로 작성
</guidelines>"""


class ClaudePatternAnalyzer(BasePatternAnalyzer):
    """Claude를 사용한 패턴 분석기

    액션 시퀀스에서 LLM으로 패턴 감지 + 불확실성 추출을 한 번에 처리합니다.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        use_cache: bool | None = None,
        max_patterns: int | None = None,
        max_uncertainties: int | None = None,
        min_confidence: float | None = None,
    ):
        """
        Args:
            api_key: Anthropic API 키 (None이면 설정에서 가져옴)
            model: 사용할 모델 (None이면 설정에서 가져옴)
            use_cache: 프롬프트 캐싱 사용 여부 (None이면 설정에서 가져옴)
            max_patterns: 최대 감지 패턴 수 (None이면 설정에서 가져옴)
            max_uncertainties: 패턴당 최대 불확실성 수 (None이면 설정에서 가져옴)
            min_confidence: 최소 신뢰도 (None이면 설정에서 가져옴)
        """
        self._api_key = api_key or settings.anthropic_api_key
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self._model = model or settings.claude_model
        self._use_cache = use_cache if use_cache is not None else settings.claude_use_cache
        self._max_patterns = max_patterns or getattr(settings, "pattern_max_patterns", 5)
        self._max_uncertainties = max_uncertainties or getattr(
            settings, "pattern_max_uncertainties", 5
        )
        self._min_confidence = min_confidence or getattr(settings, "pattern_min_confidence", 0.3)

        self._client = anthropic.Anthropic(
            api_key=self._api_key,
            timeout=60.0,
        )

    @property
    def backend(self) -> PatternAnalyzerBackend:
        return PatternAnalyzerBackend.CLAUDE

    @property
    def model_name(self) -> str:
        return self._model

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
        if not actions:
            return []

        # 액션 시퀀스를 텍스트로 변환
        action_text = self._format_actions(actions)

        # 시스템 프롬프트 캐싱 설정
        system_content = [{"type": "text", "text": PATTERN_DETECTION_PROMPT}]
        if self._use_cache:
            system_content[0]["cache_control"] = {"type": "ephemeral"}

        try:
            # Prefill: JSON 형식 출력 보장을 위해 응답 시작 부분 지정
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2000,
                system=system_content,
                messages=[
                    {
                        "role": "user",
                        "content": f"다음 액션 시퀀스에서 반복 패턴을 분석해주세요:\n\n{action_text}",
                    },
                    {
                        "role": "assistant",
                        "content": '{"patterns": [',  # Prefill로 JSON 시작
                    },
                ],
            )

            # Prefill 문자를 포함하여 파싱
            return self._parse_response('{"patterns": [' + response.content[0].text, actions)

        except anthropic.APIError as e:
            logger.error(f"Claude API 호출 실패: {e}")
            return []

    def _format_actions(self, actions: list[LabeledAction]) -> str:
        """액션 목록을 분석용 텍스트로 변환

        Args:
            actions: 액션 목록

        Returns:
            포맷된 텍스트
        """
        lines = []
        for i, action in enumerate(actions):
            line = f"[{i}] {action.action}: {action.target}"
            if action.context:
                line += f" @ {action.context}"
            if action.description:
                line += f" - {action.description}"
            if action.state_change:
                line += f" (변화: {action.state_change})"
            lines.append(line)
        return "\n".join(lines)

    def _parse_response(
        self, response_text: str, actions: list[LabeledAction]
    ) -> list[DetectedPattern]:
        """LLM 응답을 DetectedPattern 목록으로 파싱

        Args:
            response_text: LLM 응답 텍스트
            actions: 원본 액션 목록

        Returns:
            파싱된 패턴 목록
        """
        try:
            # JSON 추출
            text = response_text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                # ```json 또는 ``` 제거
                start_idx = 1
                end_idx = len(lines) - 1
                text = "\n".join(lines[start_idx:end_idx])

            data = json.loads(text)
            patterns = []

            for p in data.get("patterns", [])[:self._max_patterns]:
                # 신뢰도 필터링
                confidence = p.get("confidence", 1.0)
                if confidence < self._min_confidence:
                    continue

                # 패턴에 포함된 액션 추출
                occurrence_indices = p.get("action_indices", [])
                actions_per_occurrence = p.get("actions_per_occurrence", 1)

                # 첫 번째 발생의 액션들 추출
                pattern_actions = []
                if occurrence_indices and len(actions) > occurrence_indices[0]:
                    start_idx = occurrence_indices[0]
                    end_idx = min(start_idx + actions_per_occurrence, len(actions))
                    pattern_actions = actions[start_idx:end_idx]

                # 불확실성 파싱
                uncertainties = []
                for u in p.get("uncertainties", [])[:self._max_uncertainties]:
                    uncertainty_type = self._parse_uncertainty_type(u.get("type", "VARIANT"))
                    uncertainties.append(
                        Uncertainty(
                            id=str(uuid4())[:8],
                            type=uncertainty_type,
                            description=u.get("description", ""),
                            hypothesis=u.get("hypothesis"),
                            related_action_indices=u.get("related_action_indices", []),
                        )
                    )

                pattern = DetectedPattern(
                    name=p.get("name", "Unknown Pattern"),
                    description=p.get("description"),
                    actions=pattern_actions,
                    occurrence_indices=occurrence_indices,
                    confidence=confidence,
                    uncertainties=uncertainties,
                )
                patterns.append(pattern)

            return patterns

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패: {e}, 원본: {response_text[:200]}")
            return []
        except Exception as e:
            logger.warning(f"패턴 파싱 실패: {e}")
            return []

    def _parse_uncertainty_type(self, type_str: str) -> UncertaintyType:
        """문자열을 UncertaintyType으로 변환

        Args:
            type_str: 불확실성 타입 문자열

        Returns:
            UncertaintyType enum 값
        """
        type_map = {
            "CONDITION": UncertaintyType.CONDITION,
            "EXCEPTION": UncertaintyType.EXCEPTION,
            "QUALITY": UncertaintyType.QUALITY,
            "ALTERNATIVE": UncertaintyType.ALTERNATIVE,
            "VARIANT": UncertaintyType.VARIANT,
            "SEQUENCE": UncertaintyType.SEQUENCE,
            "OPTIONAL": UncertaintyType.OPTIONAL,
        }
        return type_map.get(type_str.upper(), UncertaintyType.VARIANT)


__all__ = ["ClaudePatternAnalyzer"]
