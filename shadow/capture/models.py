"""데이터 모델 정의

Raw Data Layer 모델들을 정의합니다.
- 내부 처리용: dataclass 기반 (Frame, InputEvent, KeyframePair)
- 저장/API용: Pydantic 기반 (Screenshot, InputEventRecord, RawObservation)
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class InputEventType(Enum):
    """입력 이벤트 타입"""

    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"


class MouseButton(str, Enum):
    """마우스 버튼"""

    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class ClickType(str, Enum):
    """클릭 타입"""

    SINGLE = "single"
    DOUBLE = "double"


class ScreenshotType(str, Enum):
    """스크린샷 타입"""

    BEFORE = "before"
    AFTER = "after"


@dataclass
class Frame:
    """화면 캡처 프레임"""

    timestamp: float  # Unix timestamp
    image: NDArray[np.uint8]  # RGB 이미지 (H, W, 3)

    @property
    def height(self) -> int:
        return self.image.shape[0]

    @property
    def width(self) -> int:
        return self.image.shape[1]


@dataclass
class InputEvent:
    """입력 이벤트"""

    timestamp: float  # Unix timestamp
    event_type: InputEventType
    x: int | None = None  # 마우스 X 좌표
    y: int | None = None  # 마우스 Y 좌표
    button: str | None = None  # 마우스 버튼 (left, right, middle)
    key: str | None = None  # 키보드 키
    dx: int | None = None  # 스크롤 X 변화량
    dy: int | None = None  # 스크롤 Y 변화량
    # F-03: 활성 윈도우 정보
    app_name: str | None = None  # 애플리케이션 이름
    window_title: str | None = None  # 윈도우 타이틀


@dataclass
class KeyframePair:
    """F-01: Before/After 프레임 쌍

    클릭 직전(Before)과 직후(After) 화면을 함께 저장하여
    액션의 결과를 VLM이 분석할 수 있도록 합니다.
    """

    before_frame: Frame  # 클릭 직전 프레임
    after_frame: Frame  # 클릭 직후 프레임 (0.3초 후)
    trigger_event: InputEvent  # 트리거 이벤트 (클릭 등)


# =============================================================================
# Pydantic 모델 (저장/API용)
# =============================================================================


class Resolution(BaseModel):
    """해상도"""

    width: int
    height: int


class Position(BaseModel):
    """좌표 위치"""

    x: int
    y: int


class ActiveWindow(BaseModel):
    """활성 윈도우 정보"""

    title: str
    app_name: str
    app_bundle_id: str | None = None


class Screenshot(BaseModel):
    """화면 캡처 데이터 (저장용)

    원본 이미지는 분석 후 삭제되고, 썸네일만 보관됩니다.
    """

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    type: ScreenshotType
    data: str  # base64 인코딩된 원본 이미지 (분석 후 삭제)
    thumbnail: str  # base64 인코딩된 썸네일 (보관)
    resolution: Resolution
    trigger_event_id: UUID
    session_id: UUID

    model_config = {"use_enum_values": True}


class InputEventRecord(BaseModel):
    """입력 이벤트 데이터 (저장용)

    기존 InputEvent dataclass의 저장/API 버전입니다.
    """

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    type: Literal["mouse_click", "mouse_move", "key_press", "key_release", "scroll"]
    position: Position | None = None
    button: MouseButton | None = None
    click_type: ClickType | None = None
    key: str | None = None
    modifiers: list[str] = Field(default_factory=list)
    active_window: ActiveWindow
    session_id: UUID

    model_config = {"use_enum_values": True}

    @classmethod
    def from_dataclass(
        cls,
        event: "InputEvent",
        session_id: UUID,
        event_id: UUID | None = None,
    ) -> "InputEventRecord":
        """dataclass InputEvent에서 변환"""
        position = None
        if event.x is not None and event.y is not None:
            position = Position(x=event.x, y=event.y)

        # scroll 이벤트 타입 매핑
        event_type_map = {
            InputEventType.MOUSE_CLICK: "mouse_click",
            InputEventType.MOUSE_MOVE: "mouse_move",
            InputEventType.MOUSE_SCROLL: "scroll",
            InputEventType.KEY_PRESS: "key_press",
            InputEventType.KEY_RELEASE: "key_release",
        }

        return cls(
            id=event_id or uuid4(),
            timestamp=datetime.fromtimestamp(event.timestamp),
            type=event_type_map[event.event_type],
            position=position,
            button=MouseButton(event.button) if event.button else None,
            key=event.key,
            active_window=ActiveWindow(
                title=event.window_title or "",
                app_name=event.app_name or "",
            ),
            session_id=session_id,
        )


class RawObservation(BaseModel):
    """원시 관찰 데이터

    Screenshot + InputEvent를 묶어서 하나의 관찰 단위로 만듭니다.
    Before/After 스크린샷과 트리거 이벤트를 함께 저장합니다.
    """

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    timestamp: datetime
    before_screenshot_id: UUID
    after_screenshot_id: UUID
    event_id: UUID

    @classmethod
    def from_keyframe_pair(
        cls,
        pair: "KeyframePair",
        session_id: UUID,
        before_screenshot_id: UUID,
        after_screenshot_id: UUID,
        event_id: UUID,
    ) -> "RawObservation":
        """KeyframePair에서 변환"""
        return cls(
            session_id=session_id,
            timestamp=datetime.fromtimestamp(pair.trigger_event.timestamp),
            before_screenshot_id=before_screenshot_id,
            after_screenshot_id=after_screenshot_id,
            event_id=event_id,
        )
