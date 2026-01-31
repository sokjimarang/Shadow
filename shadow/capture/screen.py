"""MSS 기반 화면 캡처 모듈"""

import time
from collections.abc import Generator
from contextlib import contextmanager

import mss
import numpy as np
from numpy.typing import NDArray

from shadow.capture.models import Frame
from shadow.config import settings


class ScreenCapture:
    """MSS를 사용한 화면 캡처"""

    def __init__(self, monitor: int | None = None, fps: int | None = None):
        """
        Args:
            monitor: 캡처할 모니터 번호 (1-based, None이면 설정 사용)
            fps: 초당 프레임 수 (None이면 설정 사용)
        """
        self._monitor = monitor or settings.capture_monitor
        self._fps = fps or settings.capture_fps
        self._frame_interval = 1.0 / self._fps
        self._sct: mss.mss | None = None

    @contextmanager
    def session(self) -> Generator["ScreenCapture", None, None]:
        """캡처 세션 컨텍스트 매니저"""
        self._sct = mss.mss()
        try:
            yield self
        finally:
            self._sct.close()
            self._sct = None

    def capture_frame(self) -> Frame:
        """단일 프레임 캡처

        Returns:
            캡처된 Frame 객체
        """
        if self._sct is None:
            raise RuntimeError("캡처 세션이 시작되지 않음. session() 컨텍스트 내에서 사용하세요.")

        monitor = self._sct.monitors[self._monitor]
        screenshot = self._sct.grab(monitor)

        # BGRA -> RGB 변환
        img = np.array(screenshot)
        rgb = img[:, :, :3][:, :, ::-1].copy()

        return Frame(timestamp=time.time(), image=rgb)

    def capture_continuous(self) -> Generator[Frame, None, None]:
        """연속 프레임 캡처 제너레이터

        설정된 FPS에 맞춰 프레임을 생성합니다.

        Yields:
            캡처된 Frame 객체
        """
        if self._sct is None:
            raise RuntimeError("캡처 세션이 시작되지 않음. session() 컨텍스트 내에서 사용하세요.")

        next_capture_time = time.time()

        while True:
            current_time = time.time()

            # 다음 캡처 시간까지 대기
            if current_time < next_capture_time:
                time.sleep(next_capture_time - current_time)

            frame = self.capture_frame()
            yield frame

            next_capture_time += self._frame_interval

    @property
    def monitor_info(self) -> dict:
        """현재 모니터 정보"""
        if self._sct is None:
            with mss.mss() as sct:
                return dict(sct.monitors[self._monitor])
        return dict(self._sct.monitors[self._monitor])
