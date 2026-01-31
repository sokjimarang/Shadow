"""Vision Analyzer 추상 베이스 클래스

LLM 모델을 쉽게 교체할 수 있도록 인터페이스를 정의합니다.
- Claude, Gemini, Qwen(로컬) 등 다양한 백엔드 지원
"""

import io
from abc import ABC, abstractmethod
from enum import Enum

from PIL import Image

from shadow.analysis.models import LabeledAction
from shadow.capture.models import Frame, KeyframePair


class AnalyzerBackend(Enum):
    """지원하는 분석기 백엔드"""

    CLAUDE = "claude"
    GEMINI = "gemini"
    QWEN_LOCAL = "qwen_local"  # Ollama 등 로컬 실행


class BaseVisionAnalyzer(ABC):
    """Vision 분석기 추상 베이스 클래스

    모든 Vision LLM 백엔드는 이 클래스를 상속받아 구현합니다.
    Before/After 키프레임 쌍 분석이 기본 인터페이스입니다.
    """

    @abstractmethod
    async def analyze_keyframe_pair(self, pair: KeyframePair) -> LabeledAction:
        """Before/After 키프레임 쌍 분석

        클릭 전후 화면을 비교하여 상태 변화를 분석합니다.

        Args:
            pair: 분석할 키프레임 쌍

        Returns:
            상태 변화가 포함된 동작 라벨
        """
        pass

    @abstractmethod
    async def analyze_batch(self, pairs: list[KeyframePair]) -> list[LabeledAction]:
        """여러 키프레임 쌍 배치 분석

        Args:
            pairs: 분석할 키프레임 쌍 목록

        Returns:
            분석된 동작 라벨 목록
        """
        pass

    @property
    @abstractmethod
    def backend(self) -> AnalyzerBackend:
        """분석기 백엔드 타입"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """사용 중인 모델 이름"""
        pass

    def _prepare_frame_image(
        self,
        frame: Frame,
        max_size: int = 1024,
        click_pos: tuple[int, int] | None = None,
    ) -> tuple[bytes, str]:
        """프레임 이미지를 API용으로 준비

        Args:
            frame: 분석할 프레임
            max_size: 이미지 최대 크기 (토큰 절약)
            click_pos: 클릭 위치 (x, y) - 표시할 경우

        Returns:
            (이미지 bytes, mime_type) 튜플
        """
        img = Image.fromarray(frame.image)
        original_size = img.size

        # 이미지 리사이즈 (토큰 절약)
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # 클릭 위치 표시
        if click_pos is not None:
            from PIL import ImageDraw

            draw = ImageDraw.Draw(img)
            # 리사이즈 비율 계산
            scale_x = img.width / original_size[0]
            scale_y = img.height / original_size[1]
            x = int(click_pos[0] * scale_x)
            y = int(click_pos[1] * scale_y)

            radius = 8
            draw.ellipse(
                [x - radius - 2, y - radius - 2, x + radius + 2, y + radius + 2],
                outline="white",
                width=3,
            )
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill="red",
                outline="white",
                width=2,
            )

        # bytes로 변환
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue(), "image/png"

    def _estimate_image_tokens(self, width: int, height: int) -> int:
        """이미지 토큰 수 추정 (Claude 기준)

        Args:
            width: 이미지 너비
            height: 이미지 높이

        Returns:
            추정 토큰 수
        """
        return (width * height) // 750


__all__ = [
    "LabeledAction",
    "AnalyzerBackend",
    "BaseVisionAnalyzer",
]
