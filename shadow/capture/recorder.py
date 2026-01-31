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
        self._session: RecordingSession | None = None

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

    def start(self) -> None:
        """녹화 시작 (백그라운드 스레드에서 실행)

        stop()을 호출하면 녹화가 중지되고 세션을 반환받을 수 있습니다.
        """
        self._stop_event.clear()
        self._recording = True
        self._session = RecordingSession()
        self._session.start_time = time.time()

        # 입력 이벤트 수집 시작
        self._input_collector.start()
        self._screen_capture_context = self._screen_capture.session()
        self._screen_capture_context.__enter__()

        # 백그라운드 캡처 스레드 시작
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def _capture_loop(self) -> None:
        """백그라운드 캡처 루프"""
        for frame in self._screen_capture.capture_continuous():
            if self._session:
                self._session.frames.append(frame)
                events = self._input_collector.get_events()
                self._session.events.extend(events)

            if self._stop_event.is_set():
                break

    def stop(self) -> RecordingSession:
        """녹화 중지 및 세션 반환

        Returns:
            녹화된 세션 (start()가 호출되지 않았으면 빈 세션)
        """
        self._stop_event.set()

        # 캡처 스레드 종료 대기
        if hasattr(self, '_capture_thread') and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=2.0)

        # 컨텍스트 정리
        if hasattr(self, '_screen_capture_context'):
            self._screen_capture_context.__exit__(None, None, None)

        # 입력 수집기 정리
        self._input_collector.stop()

        self._recording = False

        if self._session:
            self._session.end_time = time.time()
            session = self._session
            self._session = None
            return session

        return RecordingSession()

    @property
    def is_recording(self) -> bool:
        """녹화 중 여부"""
        return self._recording
