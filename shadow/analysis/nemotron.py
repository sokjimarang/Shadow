"""NVIDIA NIM Nemotron VL Vision 분석기

OpenAI 호환 API를 사용하여 NVIDIA NIM의 Nemotron VL 모델에 접근합니다.
문서/OCR에 특화된 Vision Language Model입니다.
"""

import asyncio
import base64
import json
import logging

from openai import OpenAI

from shadow.analysis.base import AnalyzerBackend, BaseVisionAnalyzer
from shadow.analysis.models import LabeledAction
from shadow.capture.models import KeyframePair
from shadow.config import settings

logger = logging.getLogger(__name__)

# Claude와 동일한 시스템 프롬프트 사용
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


class NemotronAnalyzer(BaseVisionAnalyzer):
    """NVIDIA NIM Nemotron VL을 사용한 키프레임 분석

    OpenAI 호환 API를 사용합니다.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_image_size: int | None = None,
        base_url: str | None = None,
    ):
        """
        Args:
            api_key: NVIDIA API 키 (None이면 설정에서 가져옴)
            model: 사용할 모델 (None이면 설정에서 가져옴)
            max_image_size: 이미지 최대 크기 (None이면 설정에서 가져옴)
            base_url: API 베이스 URL (None이면 설정에서 가져옴)
        """
        self._api_key = api_key or settings.nvidia_api_key
        if not self._api_key:
            raise ValueError("NVIDIA_API_KEY가 설정되지 않았습니다.")

        self._model = model or settings.nemotron_model
        self._max_image_size = max_image_size or settings.nemotron_max_image_size
        self._base_url = base_url or settings.nemotron_base_url

        self._client = OpenAI(
            base_url=self._base_url,
            api_key=self._api_key,
        )

    @property
    def backend(self) -> AnalyzerBackend:
        return AnalyzerBackend.NEMOTRON

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze_keyframe_pair(self, pair: KeyframePair) -> LabeledAction:
        """Before/After 키프레임 쌍 분석

        Args:
            pair: 분석할 키프레임 쌍

        Returns:
            상태 변화가 포함된 동작 라벨
        """
        # Before 이미지 (클릭 위치 표시)
        click_pos = None
        if pair.trigger_event.x is not None and pair.trigger_event.y is not None:
            click_pos = (pair.trigger_event.x, pair.trigger_event.y)

        before_bytes, _ = self._prepare_frame_image(
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

        # OpenAI 호환 API 호출 (동기 -> 비동기 래핑)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "[Before 이미지]"},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{before_b64}"},
                            },
                            {"type": "text", "text": "[After 이미지]"},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{after_b64}"},
                            },
                            {"type": "text", "text": user_message},
                        ],
                    },
                ],
                max_tokens=512,
            ),
        )

        return self._parse_response(response.choices[0].message.content)

    async def analyze_batch(self, pairs: list[KeyframePair]) -> list[LabeledAction]:
        """여러 키프레임 쌍 배치 분석 (순차 처리)

        NVIDIA NIM은 배치 API를 지원하지 않으므로 순차 처리합니다.

        Args:
            pairs: 분석할 키프레임 쌍 목록

        Returns:
            분석된 동작 라벨 목록
        """
        results = []
        for pair in pairs:
            try:
                result = await self.analyze_keyframe_pair(pair)
                results.append(result)
            except Exception as e:
                logger.error(f"키프레임 분석 실패: {e}")
                results.append(
                    LabeledAction(
                        action="error",
                        target="unknown",
                        context="unknown",
                        description=str(e)[:200],
                    )
                )
        return results

    def _parse_response(self, response_text: str) -> LabeledAction:
        """API 응답 파싱

        Args:
            response_text: JSON 형식의 응답 텍스트

        Returns:
            파싱된 LabeledAction
        """
        try:
            text = response_text.strip()
            # 마크다운 코드 블록 제거
            if text.startswith("```"):
                lines = text.split("\n")
                # 첫 줄 (```json 등)과 마지막 줄 (```) 제거
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

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
