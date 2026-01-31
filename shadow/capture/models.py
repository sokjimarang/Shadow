"""데이터 모델 정의"""

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray


class InputEventType(Enum):
    """입력 이벤트 타입"""

    MOUSE_CLICK = "mouse_click"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"


@dataclass
class WindowInfo:
    """활성 윈도우 정보"""

    app_name: str  # 애플리케이션 이름
    bundle_id: str | None = None  # Bundle ID
    process_id: int | None = None  # 프로세스 ID


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
    window_info: WindowInfo | None = None  # 활성 윈도우 정보


@dataclass
class Keyframe:
    """키프레임 - 특정 이벤트 시점의 프레임"""

    frame: Frame
    trigger_event: InputEvent  # 이 프레임을 트리거한 이벤트
