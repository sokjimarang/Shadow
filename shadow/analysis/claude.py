"""Claude Opus 4.5 Vision 분석기

비용 최적화 기능:
- Prompt Caching: 시스템 프롬프트 캐싱으로 90% 비용 절감
- 이미지 리사이즈: 작은 이미지로 토큰 절약
- 배치 분석: 여러 이미지를 한 번에 분석
"""

import base64
import json
import logging

import anthropic

logger = logging.getLogger(__name__)

from shadow.analysis.base import LabeledAction, AnalyzerBackend, BaseVisionAnalyzer
from shadow.capture.models import KeyframePair
from shadow.config import settings

# Before/After 비교 분석용 시스템 프롬프트 (캐싱 대상)
# Anthropic Prompt Best Practices 적용: XML 태그 구조화, 컨텍스트 제공, Multishot 예시
SYSTEM_PROMPT = """<role>
당신은 GUI 스크린샷의 Before/After를 비교 분석하여 사용자 동작과 그 결과를 식별하는 전문가입니다.
</role>

<context>
이 분석은 업무 자동화 명세서 생성 시스템의 첫 단계입니다.
분석 결과는 반복 패턴 감지 → HITL 질문 생성 → 자동화 명세서 작성에 사용됩니다.
정확한 상태 변화 감지가 후속 단계의 품질을 결정합니다.
</context>

<instructions>
1. 첫 번째 이미지(Before): 클릭 직전 화면 상태
2. 두 번째 이미지(After): 클릭 직후 화면 상태
3. 빨간 원: 클릭 위치 (Before 이미지에 표시)
4. 두 이미지를 비교하여 화면 변화를 구체적으로 분석
</instructions>

<output_format>
다음 JSON 형식으로만 응답하세요:
{
    "action": "click|scroll|type|drag",
    "target": "클릭한 UI 요소 이름",
    "context": "현재 앱 또는 화면 이름",
    "description": "사용자가 수행한 동작 설명",
    "before_state": "클릭 전 화면/요소 상태",
    "after_state": "클릭 후 화면/요소 상태",
    "state_change": "클릭으로 인한 변화 요약"
}
</output_format>

<example>
입력: Chrome 브라우저에서 "새 탭" 버튼 클릭
출력:
{
    "action": "click",
    "target": "새 탭 버튼 (+)",
    "context": "Chrome 브라우저",
    "description": "브라우저 상단의 새 탭 버튼을 클릭",
    "before_state": "탭 1개 열림 (Google 검색)",
    "after_state": "탭 2개 열림 (새 탭 추가됨)",
    "state_change": "새 탭이 생성되어 총 2개 탭이 됨"
}
</example>

<guidelines>
- JSON 외의 텍스트를 출력하지 마세요
- state_change는 구체적인 변화를 기술 (예: "드롭다운 메뉴가 열림", "새 탭이 생성됨")
- 변화가 없으면 state_change에 "변화 없음"이라고 작성
</guidelines>"""


class ClaudeAnalyzer(BaseVisionAnalyzer):
    """Claude Opus 4.5를 사용한 키프레임 분석

    비용 최적화:
    - 시스템 프롬프트 캐싱 (cache_control)
    - 이미지 리사이즈 (기본 1024px)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_image_size: int | None = None,
        use_cache: bool | None = None,
    ):
        """
        Args:
            api_key: Anthropic API 키 (None이면 설정에서 가져옴)
            model: 사용할 모델 (None이면 설정에서 가져옴)
            max_image_size: 이미지 최대 크기 (None이면 설정에서 가져옴)
            use_cache: 프롬프트 캐싱 사용 여부 (None이면 설정에서 가져옴)
        """
        self._api_key = api_key or settings.anthropic_api_key
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다.")

        self._model = model or settings.claude_model
        self._max_image_size = max_image_size or settings.claude_max_image_size
        self._use_cache = use_cache if use_cache is not None else settings.claude_use_cache

        self._client = anthropic.Anthropic(
            api_key=self._api_key,
            timeout=30.0,
        )

    @property
    def backend(self) -> AnalyzerBackend:
        return AnalyzerBackend.CLAUDE

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze_keyframe_pair(self, pair: KeyframePair) -> LabeledAction:
        """F-04: Before/After 키프레임 쌍 분석

        클릭 전후 화면을 비교하여 상태 변화를 분석합니다.

        Args:
            pair: 분석할 키프레임 쌍

        Returns:
            상태 변화가 포함된 동작 라벨
        """
        # Before 이미지 (클릭 위치 표시)
        click_pos = None
        if pair.trigger_event.x is not None and pair.trigger_event.y is not None:
            click_pos = (pair.trigger_event.x, pair.trigger_event.y)

        before_bytes, media_type = self._prepare_frame_image(
            pair.before_frame,
            max_size=self._max_image_size,
            click_pos=click_pos,
        )
        before_b64 = base64.standard_b64encode(before_bytes).decode("utf-8")

        # After 이미지 (클릭 위치 표시 없음)
        after_bytes, _ = self._prepare_frame_image(
            pair.after_frame,
            max_size=self._max_image_size,
            click_pos=None,
        )
        after_b64 = base64.standard_b64encode(after_bytes).decode("utf-8")

        # 컨텍스트 정보 구성
        context_info = []
        if pair.trigger_event.app_name:
            context_info.append(f"앱: {pair.trigger_event.app_name}")
        if pair.trigger_event.window_title:
            context_info.append(f"윈도우: {pair.trigger_event.window_title}")
        x = pair.trigger_event.x or 0
        y = pair.trigger_event.y or 0
        context_info.append(f"클릭 위치: ({x}, {y})")

        user_message = f"""다음 두 스크린샷을 비교 분석해주세요.

[컨텍스트]
{chr(10).join(context_info)}

[Before] 첫 번째 이미지 - 클릭 직전 (빨간 원이 클릭 위치)
[After] 두 번째 이미지 - 클릭 직후"""

        # 시스템 프롬프트 캐싱 설정
        system_content = [{"type": "text", "text": SYSTEM_PROMPT}]
        if self._use_cache:
            system_content[0]["cache_control"] = {"type": "ephemeral"}

        # Prefill: JSON 형식 출력 보장을 위해 응답 시작 부분 지정
        response = self._client.messages.create(
            model=self._model,
            max_tokens=700,
            system=system_content,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "[Before 이미지]"},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": before_b64,
                            },
                        },
                        {"type": "text", "text": "[After 이미지]"},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": after_b64,
                            },
                        },
                        {"type": "text", "text": user_message},
                    ],
                },
                {
                    "role": "assistant",
                    "content": "{",  # Prefill로 JSON 시작
                },
            ],
        )

        # Prefill 문자를 포함하여 파싱
        return self._parse_pair_response("{" + response.content[0].text)

    async def analyze_batch(self, pairs: list[KeyframePair]) -> list[LabeledAction]:
        """여러 키프레임 쌍 배치 분석

        Args:
            pairs: 분석할 키프레임 쌍 목록

        Returns:
            분석된 동작 라벨 목록
        """
        if not pairs:
            return []

        # 단일 쌍인 경우
        if len(pairs) == 1:
            result = await self.analyze_keyframe_pair(pairs[0])
            return [result]

        # 순차 분석 (배치 API는 이미지 2개씩 필요하므로)
        results = []
        for pair in pairs:
            result = await self.analyze_keyframe_pair(pair)
            results.append(result)

        return results

    def _parse_pair_response(self, response_text: str) -> LabeledAction:
        """Before/After 응답 파싱"""
        try:
            text = response_text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            data = json.loads(text)
            return LabeledAction(
                action=data.get("action", "unknown"),
                target=data.get("target", "unknown"),
                context=data.get("context", "unknown"),
                description=data.get("description", ""),
                before_state=data.get("before_state"),
                after_state=data.get("after_state"),
                state_change=data.get("state_change"),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패: {e}, 원본: {response_text[:100]}")
            return LabeledAction(
                action="unknown",
                target="unknown",
                context="unknown",
                description=response_text[:200],
            )

    def estimate_cost(self, pairs: list[KeyframePair]) -> dict:
        """예상 비용 계산

        Args:
            pairs: 분석할 키프레임 쌍 목록

        Returns:
            예상 비용 정보 딕셔너리
        """
        # 이미지 토큰 계산 (Before + After = 2장/쌍)
        total_image_tokens = 0
        for pair in pairs:
            for frame in [pair.before_frame, pair.after_frame]:
                w, h = frame.width, frame.height
                if max(w, h) > self._max_image_size:
                    ratio = self._max_image_size / max(w, h)
                    w, h = int(w * ratio), int(h * ratio)
                total_image_tokens += self._estimate_image_tokens(w, h)

        # 프롬프트 토큰 (대략)
        prompt_tokens = 700  # Before/After 시스템 프롬프트
        prompt_tokens += len(pairs) * 100  # 각 쌍별 컨텍스트

        # 출력 토큰 (대략)
        output_tokens = len(pairs) * 150  # Before/After 분석은 더 긴 출력

        # 캐시 적용 시
        if self._use_cache:
            cached_prompt_cost = prompt_tokens * 0.1
        else:
            cached_prompt_cost = prompt_tokens

        input_tokens = total_image_tokens + cached_prompt_cost
        input_cost = input_tokens * 5 / 1_000_000
        output_cost = output_tokens * 25 / 1_000_000

        return {
            "image_tokens": total_image_tokens,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": input_cost + output_cost,
            "cache_savings": "~90%" if self._use_cache else "0%",
        }
