"""Gemini Vision AI 분석 모듈

Before/After 키프레임 쌍을 비교 분석합니다.
"""

import json

from google import genai
from google.genai import types

from shadow.analysis.base import AnalyzerBackend, BaseVisionAnalyzer
from shadow.analysis.models import LabeledAction
from shadow.capture.models import KeyframePair
from shadow.config import settings

# Before/After 비교 분석용 시스템 프롬프트
SYSTEM_PROMPT = """당신은 GUI 스크린샷의 Before/After를 비교 분석하여 사용자 동작과 그 결과를 식별하는 전문가입니다.

## 분석 규칙
1. 첫 번째 이미지(Before): 클릭 직전 화면 상태
2. 두 번째 이미지(After): 클릭 직후 화면 상태
3. 빨간 원: 클릭 위치 (Before 이미지에 표시)
4. 두 이미지를 비교하여 화면 변화 분석

## 출력 형식
반드시 다음 JSON 형식으로만 응답하세요:
{
    "action": "click|scroll|type|drag",
    "target": "클릭한 UI 요소 이름",
    "context": "현재 앱 또는 화면 이름",
    "description": "사용자가 수행한 동작 설명",
    "before_state": "클릭 전 화면/요소 상태",
    "after_state": "클릭 후 화면/요소 상태",
    "state_change": "클릭으로 인한 변화 요약"
}

## 주의사항
- JSON 외의 텍스트를 출력하지 마세요
- state_change는 구체적인 변화를 기술하세요 (예: "드롭다운 메뉴가 열림", "새 탭이 생성됨")
- 변화가 없으면 state_change에 "변화 없음"이라고 작성하세요"""


class GeminiAnalyzer(BaseVisionAnalyzer):
    """Gemini를 사용한 Before/After 키프레임 쌍 분석"""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Args:
            api_key: Gemini API 키 (None이면 설정에서 가져옴)
            model: 사용할 모델 (None이면 설정에서 가져옴)
        """
        self._api_key = api_key or settings.gemini_api_key
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

        self._client = genai.Client(api_key=self._api_key)
        self._model = model or settings.gemini_model

    @property
    def backend(self) -> AnalyzerBackend:
        return AnalyzerBackend.GEMINI

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze_keyframe_pair(self, pair: KeyframePair) -> LabeledAction:
        """Before/After 키프레임 쌍 분석"""
        # Before 이미지 (클릭 위치 표시)
        click_pos = None
        if pair.trigger_event.x is not None and pair.trigger_event.y is not None:
            click_pos = (pair.trigger_event.x, pair.trigger_event.y)

        before_bytes, mime_type = self._prepare_frame_image(
            pair.before_frame,
            max_size=1568,  # Gemini 권장 크기
            click_pos=click_pos,
        )
        before_part = types.Part.from_bytes(data=before_bytes, mime_type=mime_type)

        # After 이미지
        after_bytes, _ = self._prepare_frame_image(
            pair.after_frame,
            max_size=1568,
            click_pos=None,
        )
        after_part = types.Part.from_bytes(data=after_bytes, mime_type=mime_type)

        # 컨텍스트 정보
        context_info = []
        if pair.trigger_event.app_name:
            context_info.append(f"앱: {pair.trigger_event.app_name}")
        if pair.trigger_event.window_title:
            context_info.append(f"윈도우: {pair.trigger_event.window_title}")
        x = pair.trigger_event.x or 0
        y = pair.trigger_event.y or 0
        context_info.append(f"클릭 위치: ({x}, {y})")

        user_prompt = f"""다음 두 스크린샷을 비교 분석해주세요.

[컨텍스트]
{chr(10).join(context_info)}

[Before] 첫 번째 이미지 - 클릭 직전 (빨간 원이 클릭 위치)
[After] 두 번째 이미지 - 클릭 직후"""

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=[
                "[Before 이미지]",
                before_part,
                "[After 이미지]",
                after_part,
                user_prompt,
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )

        return self._parse_response(response.text)

    async def analyze_batch(self, pairs: list[KeyframePair]) -> list[LabeledAction]:
        """여러 키프레임 쌍 배치 분석"""
        if not pairs:
            return []

        # 순차 분석
        results = []
        for pair in pairs:
            result = await self.analyze_keyframe_pair(pair)
            results.append(result)

        return results

    def _parse_response(self, response_text: str) -> LabeledAction:
        """응답 파싱"""
        try:
            data = json.loads(response_text)
            return LabeledAction(
                action=data.get("action", "unknown"),
                target=data.get("target", "unknown"),
                context=data.get("context", "unknown"),
                description=data.get("description", ""),
                before_state=data.get("before_state"),
                after_state=data.get("after_state"),
                state_change=data.get("state_change"),
            )
        except json.JSONDecodeError:
            return LabeledAction(
                action="unknown",
                target="unknown",
                context="unknown",
                description=response_text[:200] if response_text else "",
            )
