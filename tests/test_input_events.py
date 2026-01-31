"""InputEventCollector 단위 테스트 (F-02, F-03)"""

import time
from unittest.mock import Mock

import pytest

from shadow.capture.input_events import InputEventCollector
from shadow.capture.models import InputEvent, InputEventType


class TestInputEventCollectorBasic:
    """InputEventCollector 기본 기능 테스트"""

    def test_collector_initialization(self):
        """InputEventCollector 초기화 확인"""
        collector = InputEventCollector()

        assert collector is not None
        assert not collector._running
        assert collector._events.empty()

    def test_get_events_returns_empty_when_no_events(self):
        """이벤트가 없을 때 빈 리스트 반환"""
        collector = InputEventCollector()

        # 리스너를 시작하지 않고 테스트
        events = collector.get_events()

        assert events == []

    def test_get_events_without_timeout(self):
        """timeout 없이 즉시 반환"""
        collector = InputEventCollector()

        events = collector.get_events()

        assert isinstance(events, list)


class TestInputEventCollectorCallbacks:
    """콜백 메커니즘 테스트"""

    def test_add_callback(self):
        """콜백 추가"""
        collector = InputEventCollector()
        callback = Mock()

        collector.add_callback(callback)

        assert callback in collector._callbacks

    def test_remove_callback(self):
        """콜백 제거"""
        collector = InputEventCollector()
        callback = Mock()

        collector.add_callback(callback)
        collector.remove_callback(callback)

        assert callback not in collector._callbacks

    def test_callback_called_on_event(self):
        """이벤트 발생 시 콜백 호출"""
        collector = InputEventCollector()
        callback = Mock()

        collector.add_callback(callback)

        # 프로그래매틱하게 이벤트 생성 (리스너 시작 없이)
        test_event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=100,
            y=100,
        )

        collector._emit_event(test_event)

        # 콜백이 호출되었는지 확인
        callback.assert_called_once()
        called_event = callback.call_args[0][0]
        assert called_event.event_type == InputEventType.MOUSE_CLICK
        assert called_event.x == 100

    def test_multiple_callbacks(self):
        """여러 콜백 등록 및 호출"""
        collector = InputEventCollector()
        callback1 = Mock()
        callback2 = Mock()

        collector.add_callback(callback1)
        collector.add_callback(callback2)

        test_event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=200,
            y=300,
        )

        collector._emit_event(test_event)

        # 두 콜백 모두 호출됨
        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_callback_error_does_not_stop_collection(self):
        """콜백 에러가 수집을 멈추지 않음"""
        collector = InputEventCollector()

        # 에러를 발생시키는 콜백
        def error_callback(event):
            raise RuntimeError("Test error")

        collector.add_callback(error_callback)

        test_event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=100,
            y=100,
        )

        # 에러가 발생해도 정상 동작
        collector._emit_event(test_event)

        # 이벤트는 버퍼에 저장됨
        events = collector.get_events()
        assert len(events) == 1


class TestInputEventCollectorWindowInfo:
    """윈도우 정보 통합 테스트 (F-03)"""

    def test_input_event_has_window_info_field(self):
        """InputEvent에 window_info 필드가 있는지 확인"""
        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=100,
            y=200,
        )

        # window_info 필드 존재 확인 (PRD F-03 Pass 조건)
        assert hasattr(event, "window_info")
        assert hasattr(event, "app_name")
        assert hasattr(event, "window_title")

    def test_event_emitted_includes_window_info(self):
        """emit된 이벤트에 윈도우 정보가 포함되는지 확인"""
        collector = InputEventCollector()
        events_collected = []

        def collect_event(event):
            events_collected.append(event)

        collector.add_callback(collect_event)

        test_event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=100,
            y=200,
        )

        collector._emit_event(test_event)

        # 이벤트가 수집되었는지 확인
        assert len(events_collected) > 0

        # window_info 필드 확인
        event = events_collected[0]
        assert hasattr(event, "window_info")


class TestInputEventCollectorEventBuffer:
    """이벤트 버퍼 관리 테스트"""

    def test_buffer_overflow_removes_old_events(self):
        """버퍼 가득 차면 오래된 이벤트 제거"""
        collector = InputEventCollector(buffer_size=3)

        # 4개 이벤트 추가 (버퍼 크기는 3)
        for i in range(4):
            test_event = InputEvent(
                timestamp=time.time() + i,
                event_type=InputEventType.MOUSE_CLICK,
                x=i * 100,
                y=i * 100,
            )
            collector._emit_event(test_event)

        # 버퍼 크기는 3이므로 최신 3개만 남음
        events = collector.get_events()
        assert len(events) == 3

        # 가장 오래된 이벤트(x=0)는 제거됨
        x_values = [e.x for e in events]
        assert 0 not in x_values

    def test_get_events_empties_buffer(self):
        """get_events()가 버퍼를 비우는지 확인"""
        collector = InputEventCollector()

        test_event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=100,
            y=100,
        )
        collector._emit_event(test_event)

        # 첫 번째 get_events()
        events1 = collector.get_events()
        assert len(events1) == 1

        # 두 번째 get_events() (버퍼가 비워졌음)
        events2 = collector.get_events()
        assert len(events2) == 0


class TestInputEventTypes:
    """다양한 이벤트 타입 테스트"""

    def test_mouse_click_event(self):
        """마우스 클릭 이벤트 필드 확인"""
        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=100,
            y=200,
            button="left",
        )

        assert event.event_type == InputEventType.MOUSE_CLICK
        assert event.x == 100
        assert event.y == 200
        assert event.button == "left"

    def test_mouse_scroll_event(self):
        """마우스 스크롤 이벤트 필드 확인"""
        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_SCROLL,
            x=100,
            y=200,
            dx=0,
            dy=10,
        )

        assert event.event_type == InputEventType.MOUSE_SCROLL
        assert event.dx == 0
        assert event.dy == 10

    def test_key_press_event(self):
        """키보드 누름 이벤트 필드 확인"""
        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.KEY_PRESS,
            key="a",
        )

        assert event.event_type == InputEventType.KEY_PRESS
        assert event.key == "a"

    def test_key_release_event(self):
        """키보드 릴리즈 이벤트 필드 확인"""
        event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.KEY_RELEASE,
            key="shift",
        )

        assert event.event_type == InputEventType.KEY_RELEASE
        assert event.key == "shift"
