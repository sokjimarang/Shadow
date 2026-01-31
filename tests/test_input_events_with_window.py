"""InputEventCollector + WindowInfo 통합 테스트"""

import time

from shadow.capture.input_events import InputEventCollector
from shadow.capture.models import InputEvent, InputEventType


def test_input_event_has_window_fields():
    """InputEvent에 app_name, window_title 필드가 있는지 확인"""
    event = InputEvent(
        timestamp=time.time(),
        event_type=InputEventType.MOUSE_CLICK,
        x=100,
        y=200,
    )

    # F-03: app_name, window_title 필드 존재 확인
    assert hasattr(event, "app_name")
    assert hasattr(event, "window_title")


def test_input_collector_captures_window_info():
    """입력 이벤트에 윈도우 정보가 포함되는지 확인"""
    collector = InputEventCollector()

    # 콜백으로 이벤트를 수집
    events_collected = []

    def collect_event(event):
        events_collected.append(event)

    collector.add_callback(collect_event)

    with collector:
        # _on_mouse_click을 통해 윈도우 정보가 추가되는지 확인
        from pynput.mouse import Button
        collector._on_mouse_click(100, 200, Button.left, True)

    # 이벤트가 수집되었는지 확인
    assert len(events_collected) > 0

    # F-03: app_name, window_title 필드 확인
    event = events_collected[0]
    assert hasattr(event, "app_name")
    assert hasattr(event, "window_title")
    # macOS에서는 실제 값이 있어야 함
    assert event.app_name is not None
    assert event.window_title is not None
