"""Gemini Vision AI 분석 모듈"""

import json

from google import genai
from google.genai import types

from shadow.analysis.base import ActionLabel, AnalyzerBackend, BaseVisionAnalyzer
from shadow.analysis.prompts import (
    BATCH_ANALYSIS_SYSTEM,
    BATCH_ANALYSIS_USER,
    KEYFRAME_ANALYSIS_SYSTEM,
    KEYFRAME_ANALYSIS_USER,
)
from shadow.capture.models import Keyframe
from shadow.config import settings


class GeminiAnalyzer(BaseVisionAnalyzer):
    """Gemini를 사용한 키프레임 분석"""

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

    def _prepare_gemini_image(self, keyframe: Keyframe) -> types.Part:
        """키프레임 이미지를 Gemini API용으로 준비"""
        image_bytes, mime_type = self._prepare_image(keyframe, max_size=1568)
        return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    async def analyze_keyframe(self, keyframe: Keyframe) -> ActionLabel:
        """단일 키프레임 분석"""
        image_part = self._prepare_gemini_image(keyframe)

        x = keyframe.trigger_event.x or 0
        y = keyframe.trigger_event.y or 0

        user_prompt = KEYFRAME_ANALYSIS_USER.format(x=x, y=y)

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=[image_part, user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=KEYFRAME_ANALYSIS_SYSTEM,
                response_mime_type="application/json",
            ),
        )

        return self._parse_action_label(response.text)

    async def analyze_batch(self, keyframes: list[Keyframe]) -> list[ActionLabel]:
        """여러 키프레임 배치 분석"""
        if not keyframes:
            return []

        contents: list[types.Part | str] = []
        for i, kf in enumerate(keyframes):
            contents.append(f"[스크린샷 {i + 1}]")
            contents.append(self._prepare_gemini_image(kf))

        user_prompt = BATCH_ANALYSIS_USER.format(count=len(keyframes))
        contents.append(user_prompt)

        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=BATCH_ANALYSIS_SYSTEM,
                response_mime_type="application/json",
            ),
        )

        return self._parse_action_labels(response.text)

    def _parse_action_label(self, response_text: str) -> ActionLabel:
        """단일 응답 파싱"""
        try:
            data = json.loads(response_text)
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
                description=response_text,
            )

    def _parse_action_labels(self, response_text: str) -> list[ActionLabel]:
        """배치 응답 파싱"""
        try:
            data = json.loads(response_text)
            if not isinstance(data, list):
                data = [data]

            return [
                ActionLabel(
                    action=item.get("action", "unknown"),
                    target=item.get("target", "unknown"),
                    context=item.get("context", "unknown"),
                    description=item.get("description", ""),
                )
                for item in data
            ]
        except json.JSONDecodeError:
            return [
                ActionLabel(
                    action="unknown",
                    target="unknown",
                    context="unknown",
                    description=response_text,
                )
            ]
