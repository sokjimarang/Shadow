"""데이터 수집 모듈"""

from shadow.capture.input_events import InputEventCollector
from shadow.capture.models import (
    # Dataclass 모델 (내부 처리용)
    Frame,
    InputEvent,
    InputEventType,
    KeyframePair,
    # Pydantic 모델 (저장/API용)
    ActiveWindow,
    ClickType,
    InputEventRecord,
    MouseButton,
    Position,
    RawObservation,
    Resolution,
    Screenshot,
    ScreenshotType,
    WindowInfo
)
from shadow.capture.recorder import Recorder, RecordingSession
from shadow.capture.screen import ScreenCapture
from shadow.capture.window import WindowInfoCollector, get_active_window

__all__ = [
    # Dataclass 모델
    "Frame",
    "InputEvent",
    "InputEventType",
    "KeyframePair",
    # Pydantic 모델
    "Screenshot",
    "ScreenshotType",
    "InputEventRecord",
    "RawObservation",
    "Position",
    "Resolution",
    "ActiveWindow",
    "MouseButton",
    "ClickType",
    "WindowInfo",
    # 수집기
    "ScreenCapture",
    "InputEventCollector",
    "WindowInfoCollector",
    "get_active_window",
    "Recorder",
    "RecordingSession",
]
