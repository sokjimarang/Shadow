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
)
from shadow.capture.recorder import Recorder, RecordingSession
from shadow.capture.screen import ScreenCapture

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
    # 수집기
    "ScreenCapture",
    "InputEventCollector",
    "Recorder",
    "RecordingSession",
]
