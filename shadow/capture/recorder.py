"""캡처 + 입력 이벤트 동기화 오케스트레이터"""

import threading
import time
from dataclasses import dataclass, field

from shadow.capture.input_events import InputEventCollector
from shadow.capture.models import Frame, InputEvent
from shadow.capture.screen import ScreenCapture


@dataclass
class RecordingSession:
    """녹화 세션 결과"""

    frames: list[Frame] = field(default_factory=list)
    events: list[InputEvent] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def duration(self) -> float:
        """녹화 시간 (초)"""
        return self.end_time - self.start_time


class Recorder:
    """화면 캡처와 입력 이벤트를 동시에 수집하는 녹화기"""

    def __init__(self, monitor: int | None = None, fps: int | None = None):
        """
        Args:
            monitor: 캡처할 모니터 번호 (1-based)
            fps: 초당 프레임 수
        """
        self._screen_capture = ScreenCapture(monitor=monitor, fps=fps)
        self._input_collector = InputEventCollector()
        self._recording = False
        self._stop_event = threading.Event()

    def record(self, duration: float) -> RecordingSession:
        """지정된 시간 동안 녹화

        Args:
            duration: 녹화 시간 (초)

        Returns:
            녹화된 프레임과 이벤트를 포함한 세션
        """
        session = RecordingSession()
        session.start_time = time.time()

        self._stop_event.clear()
        self._recording = True

        # 입력 이벤트 수집 시작
        with self._input_collector:
            # 화면 캡처 시작
            with self._screen_capture.session():
                end_time = session.start_time + duration

                for frame in self._screen_capture.capture_continuous():
                    session.frames.append(frame)

                    # 이벤트 수집
                    events = self._input_collector.get_events()
                    session.events.extend(events)

                    # 종료 조건 확인
                    if time.time() >= end_time or self._stop_event.is_set():
                        break

        session.end_time = time.time()
        self._recording = False

        return session

    def stop(self) -> None:
        """녹화 중지 요청"""
        self._stop_event.set()

    @property
    def is_recording(self) -> bool:
        """녹화 중 여부"""
        return self._recording
