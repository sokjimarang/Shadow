"""pynput 기반 입력 이벤트 수집 모듈"""

import threading
import time
from collections.abc import Callable
from queue import Empty, Queue

from pynput import keyboard, mouse

from shadow.capture.models import InputEvent, InputEventType
from shadow.capture.window import get_active_window


class InputEventCollector:
    """마우스 및 키보드 입력 이벤트 수집"""

    def __init__(self, buffer_size: int = 1000):
        """
        Args:
            buffer_size: 이벤트 버퍼 크기
        """
        self._buffer_size = buffer_size
        self._events: Queue[InputEvent] = Queue(maxsize=buffer_size)
        self._mouse_listener: mouse.Listener | None = None
        self._keyboard_listener: keyboard.Listener | None = None
        self._running = False
        self._callbacks: list[Callable[[InputEvent], None]] = []

    def add_callback(self, callback: Callable[[InputEvent], None]) -> None:
        """이벤트 발생 시 호출될 콜백 추가"""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[InputEvent], None]) -> None:
        """콜백 제거"""
        self._callbacks.remove(callback)

    def _emit_event(self, event: InputEvent) -> None:
        """이벤트 발생 및 콜백 호출"""
        # 버퍼가 가득 차면 오래된 이벤트 제거
        if self._events.full():
            try:
                self._events.get_nowait()
            except Empty:
                pass

        self._events.put(event)

        # 등록된 콜백 호출
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:
                pass  # 콜백 에러 무시

    def _on_mouse_click(
        self, x: int, y: int, button: mouse.Button, pressed: bool
    ) -> None:
        """마우스 클릭 이벤트 핸들러"""
        if not pressed:  # 릴리즈는 무시
            return

        # F-03: 활성 윈도우 정보 수집
        window_info = get_active_window()

        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=x,
            y=y,
            button=button.name,
            app_name=window_info.app_name,
            window_title=window_info.window_title,
            window_info=window_info,
        )
        self._emit_event(event)

    def _on_mouse_move(self, x: int, y: int) -> None:
        """마우스 이동 이벤트 핸들러 (비활성화 - 너무 많은 이벤트 발생)"""
        pass

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """마우스 스크롤 이벤트 핸들러"""
        # F-03: 활성 윈도우 정보 수집
        window_info = get_active_window()

        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_SCROLL,
            x=x,
            y=y,
            dx=dx,
            dy=dy,
            app_name=window_info.app_name,
            window_title=window_info.window_title,
            window_info=window_info,
        )
        self._emit_event(event)

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """키 누름 이벤트 핸들러"""
        # F-03: 활성 윈도우 정보 수집
        window_info = get_active_window()

        key_str = self._key_to_string(key)
        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.KEY_PRESS,
            key=key_str,
            app_name=window_info.app_name,
            window_title=window_info.window_title,
            window_info=window_info,
        )
        self._emit_event(event)

    def _on_key_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        """키 릴리즈 이벤트 핸들러"""
        # F-03: 활성 윈도우 정보 수집
        window_info = get_active_window()

        key_str = self._key_to_string(key)
        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.KEY_RELEASE,
            key=key_str,
            app_name=window_info.app_name,
            window_title=window_info.window_title,
            window_info=window_info,
        )
        self._emit_event(event)

    @staticmethod
    def _key_to_string(key: keyboard.Key | keyboard.KeyCode | None) -> str:
        """키 객체를 문자열로 변환"""
        if key is None:
            return "unknown"
        if isinstance(key, keyboard.Key):
            return key.name
        if isinstance(key, keyboard.KeyCode):
            return key.char or f"vk_{key.vk}"
        return str(key)

    def start(self) -> None:
        """이벤트 수집 시작"""
        if self._running:
            return

        self._running = True

        # 마우스 리스너 시작
        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self._mouse_listener.start()

        # 키보드 리스너 시작
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()

    def stop(self) -> None:
        """이벤트 수집 중지"""
        if not self._running:
            return

        self._running = False

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def get_events(self, timeout: float | None = None) -> list[InputEvent]:
        """수집된 이벤트 가져오기 (버퍼 비우기)

        Args:
            timeout: 첫 이벤트 대기 시간 (None이면 즉시 반환)

        Returns:
            수집된 이벤트 목록
        """
        events = []

        # 첫 이벤트 대기
        if timeout is not None:
            try:
                event = self._events.get(timeout=timeout)
                events.append(event)
            except Empty:
                return events

        # 나머지 이벤트 즉시 가져오기
        while not self._events.empty():
            try:
                events.append(self._events.get_nowait())
            except Empty:
                break

        return events

    def __enter__(self) -> "InputEventCollector":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()
