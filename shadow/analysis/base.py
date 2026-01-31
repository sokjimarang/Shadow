"""Vision Analyzer 추상 베이스 클래스

LLM 모델을 쉽게 교체할 수 있도록 인터페이스를 정의합니다.
- Claude, Gemini, Qwen(로컬) 등 다양한 백엔드 지원
"""

import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from PIL import Image

from shadow.capture.models import Keyframe


class AnalyzerBackend(Enum):
    """지원하는 분석기 백엔드"""

    CLAUDE = "claude"
    GEMINI = "gemini"
    QWEN_LOCAL = "qwen_local"  # Ollama 등 로컬 실행


@dataclass
class ActionLabel:
    """분석된 동작 라벨"""

    action: str  # 동작 타입 (click, scroll, type 등)
    target: str  # 대상 UI 요소
    context: str  # 앱/화면 컨텍스트
    description: str  # 동작 설명

    def __str__(self) -> str:
        return f"{self.action}: {self.target} ({self.context})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ActionLabel):
            return False
        # 동작과 대상이 같으면 동일한 액션으로 취급
        return self.action == other.action and self.target == other.target

    def __hash__(self) -> int:
        return hash((self.action, self.target))


class BaseVisionAnalyzer(ABC):
    """Vision 분석기 추상 베이스 클래스

    모든 Vision LLM 백엔드는 이 클래스를 상속받아 구현합니다.
    """

    @abstractmethod
    async def analyze_keyframe(self, keyframe: Keyframe) -> ActionLabel:
        """단일 키프레임 분석

        Args:
            keyframe: 분석할 키프레임

        Returns:
            분석된 동작 라벨
        """
        pass

    @abstractmethod
    async def analyze_batch(self, keyframes: list[Keyframe]) -> list[ActionLabel]:
        """여러 키프레임 배치 분석

        Args:
            keyframes: 분석할 키프레임 목록

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

    def _prepare_image(
        self,
        keyframe: Keyframe,
        max_size: int = 1024,
        mark_click: bool = True,
    ) -> tuple[bytes, str]:
        """키프레임 이미지를 API용으로 준비

        Args:
            keyframe: 분석할 키프레임
            max_size: 이미지 최대 크기 (토큰 절약)
            mark_click: 클릭 위치에 마커 표시 여부

        Returns:
            (이미지 bytes, mime_type) 튜플
        """
        img = Image.fromarray(keyframe.frame.image)

        # 이미지 리사이즈 (토큰 절약)
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # 클릭 위치 표시
        if mark_click and keyframe.trigger_event.x is not None:
            from PIL import ImageDraw

            draw = ImageDraw.Draw(img)
            # 리사이즈 비율 계산
            scale_x = img.width / keyframe.frame.width
            scale_y = img.height / keyframe.frame.height
            x = int(keyframe.trigger_event.x * scale_x)
            y = int(keyframe.trigger_event.y * scale_y)

            radius = 8
            # 빨간 원 + 흰색 테두리
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
