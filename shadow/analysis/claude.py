"""Claude Opus 4.5 Vision 분석기

비용 최적화 기능:
- Prompt Caching: 시스템 프롬프트 캐싱으로 90% 비용 절감
- 이미지 리사이즈: 작은 이미지로 토큰 절약
- 배치 분석: 여러 이미지를 한 번에 분석
"""

import base64
import json

import anthropic

from shadow.analysis.base import ActionLabel, AnalyzerBackend, BaseVisionAnalyzer
from shadow.capture.models import Keyframe
from shadow.config import settings

# 시스템 프롬프트 (캐싱 대상)
SYSTEM_PROMPT = """당신은 GUI 스크린샷을 분석하여 사용자가 수행한 동작을 식별하는 전문가입니다.

## 분석 규칙
1. 빨간 원으로 표시된 마우스 클릭 위치와 해당 UI 요소를 정확히 식별
2. 클릭한 요소의 기능을 간결하게 설명
3. 일관된 라벨 형식 유지 (같은 버튼은 항상 같은 이름으로)

## 출력 형식
반드시 다음 JSON 형식으로만 응답하세요:
{
    "action": "click|scroll|type|drag",
    "target": "클릭한 UI 요소 이름 (버튼, 메뉴, 아이콘 등)",
    "context": "현재 앱 또는 화면 이름",
    "description": "사용자가 수행한 동작에 대한 간결한 설명"
}

## 주의사항
- JSON 외의 텍스트를 출력하지 마세요
- target은 구체적이고 일관되게 작성하세요 (예: "새로고침 버튼", "검색창", "파일 메뉴")
- 같은 UI 요소는 항상 동일한 target 이름을 사용하세요"""


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

        self._client = anthropic.Anthropic(api_key=self._api_key)

    @property
    def backend(self) -> AnalyzerBackend:
        return AnalyzerBackend.CLAUDE

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze_keyframe(self, keyframe: Keyframe) -> ActionLabel:
        """단일 키프레임 분석"""
        image_bytes, media_type = self._prepare_image(
            keyframe, max_size=self._max_image_size
        )
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        # 클릭 좌표 정보
        x = keyframe.trigger_event.x or 0
        y = keyframe.trigger_event.y or 0

        user_message = f"이 스크린샷에서 빨간 원으로 표시된 마우스 클릭 위치({x}, {y})를 분석해주세요."

        # 시스템 프롬프트 캐싱 설정
        system_content = [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
            }
        ]

        if self._use_cache:
            system_content[0]["cache_control"] = {"type": "ephemeral"}

        # API 호출 (동기 - anthropic SDK는 기본 동기)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=500,
            system=system_content,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": user_message,
                        },
                    ],
                }
            ],
        )

        return self._parse_response(response.content[0].text)

    async def analyze_batch(self, keyframes: list[Keyframe]) -> list[ActionLabel]:
        """여러 키프레임 배치 분석

        여러 이미지를 한 번의 API 호출로 분석하여 비용 절감
        """
        if not keyframes:
            return []

        # 단일 키프레임인 경우
        if len(keyframes) == 1:
            result = await self.analyze_keyframe(keyframes[0])
            return [result]

        # 메시지 컨텐츠 구성
        content = []

        for i, kf in enumerate(keyframes):
            image_bytes, media_type = self._prepare_image(
                kf, max_size=self._max_image_size
            )
            image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

            x = kf.trigger_event.x or 0
            y = kf.trigger_event.y or 0

            content.append(
                {
                    "type": "text",
                    "text": f"[스크린샷 {i + 1}] 클릭 위치: ({x}, {y})",
                }
            )
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                }
            )

        content.append(
            {
                "type": "text",
                "text": f"위 {len(keyframes)}개의 스크린샷을 분석하고, 각각에 대해 JSON 배열로 응답해주세요.",
            }
        )

        # 시스템 프롬프트 (배치용)
        batch_system = SYSTEM_PROMPT + """

## 배치 분석 시
여러 스크린샷이 제공되면 JSON 배열로 응답하세요:
[
    {"action": "...", "target": "...", "context": "...", "description": "..."},
    {"action": "...", "target": "...", "context": "...", "description": "..."}
]"""

        system_content = [{"type": "text", "text": batch_system}]
        if self._use_cache:
            system_content[0]["cache_control"] = {"type": "ephemeral"}

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1000,
            system=system_content,
            messages=[{"role": "user", "content": content}],
        )

        return self._parse_batch_response(response.content[0].text, len(keyframes))

    def _parse_response(self, response_text: str) -> ActionLabel:
        """단일 응답 파싱"""
        try:
            # JSON 블록 추출 (```json ... ``` 형식 처리)
            text = response_text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            data = json.loads(text)
            return ActionLabel(
                action=data.get("action", "unknown"),
                target=data.get("target", "unknown"),
                context=data.get("context", "unknown"),
                description=data.get("description", ""),
            )
        except json.JSONDecodeError:
            return ActionLabel(
                action="unknown",
                target="unknown",
                context="unknown",
                description=response_text[:200],
            )

    def _parse_batch_response(
        self, response_text: str, expected_count: int
    ) -> list[ActionLabel]:
        """배치 응답 파싱"""
        try:
            text = response_text.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            data = json.loads(text)

            if not isinstance(data, list):
                data = [data]

            results = []
            for item in data:
                results.append(
                    ActionLabel(
                        action=item.get("action", "unknown"),
                        target=item.get("target", "unknown"),
                        context=item.get("context", "unknown"),
                        description=item.get("description", ""),
                    )
                )

            # 예상 개수보다 적으면 unknown으로 채움
            while len(results) < expected_count:
                results.append(
                    ActionLabel(
                        action="unknown",
                        target="unknown",
                        context="unknown",
                        description="분석 실패",
                    )
                )

            return results[:expected_count]

        except json.JSONDecodeError:
            # 파싱 실패 시 모두 unknown
            return [
                ActionLabel(
                    action="unknown",
                    target="unknown",
                    context="unknown",
                    description="분석 실패",
                )
                for _ in range(expected_count)
            ]

    def estimate_cost(self, keyframes: list[Keyframe]) -> dict:
        """예상 비용 계산

        Args:
            keyframes: 분석할 키프레임 목록

        Returns:
            예상 비용 정보 딕셔너리
        """
        # 이미지 토큰 계산
        total_image_tokens = 0
        for kf in keyframes:
            # 리사이즈 후 크기 추정
            w, h = kf.frame.width, kf.frame.height
            if max(w, h) > self._max_image_size:
                ratio = self._max_image_size / max(w, h)
                w, h = int(w * ratio), int(h * ratio)
            total_image_tokens += self._estimate_image_tokens(w, h)

        # 프롬프트 토큰 (대략)
        prompt_tokens = 500  # 시스템 프롬프트
        prompt_tokens += len(keyframes) * 50  # 각 이미지별 텍스트

        # 출력 토큰 (대략)
        output_tokens = len(keyframes) * 100

        # 캐시 적용 시
        if self._use_cache:
            # 첫 호출: 캐시 쓰기 (1.25x)
            # 이후 호출: 캐시 읽기 (0.1x)
            cached_prompt_cost = prompt_tokens * 0.1  # 캐시 읽기 가정
        else:
            cached_prompt_cost = prompt_tokens

        input_tokens = total_image_tokens + cached_prompt_cost
        input_cost = input_tokens * 5 / 1_000_000  # $5/1M
        output_cost = output_tokens * 25 / 1_000_000  # $25/1M

        return {
            "image_tokens": total_image_tokens,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": input_cost + output_cost,
            "cache_savings": "~90%" if self._use_cache else "0%",
        }
