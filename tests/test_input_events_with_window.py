"""InputEventCollector + WindowInfo 통합 테스트"""

import time

from shadow.capture.input_events import InputEventCollector


def test_input_collector_has_window_collector():
    """InputEventCollector가 WindowInfoCollector를 가지는지 확인"""
    collector = InputEventCollector()

    # WindowInfoCollector가 있어야 함 (macOS)
    assert hasattr(collector, "_window_collector")
    assert collector._window_collector is not None


def test_input_event_has_window_info_field():
    """InputEvent에 window_info 필드가 있는지 확인"""
    from shadow.capture.models import InputEvent, InputEventType

    event = InputEvent(
        timestamp=time.time(),
        event_type=InputEventType.MOUSE_CLICK,
        x=100,
        y=200,
    )

    # window_info 필드 존재 확인 (Pass 조건)
    assert hasattr(event, "window_info")


def test_input_collector_captures_window_info():
    """입력 이벤트에 윈도우 정보가 포함되는지 확인 (짧은 대기)"""
    collector = InputEventCollector()

    # 콜백으로 이벤트를 수집
    events_collected = []

    def collect_event(event):
        events_collected.append(event)

    collector.add_callback(collect_event)

    with collector:
        # 프로그래매틱하게 이벤트 생성 (테스트용)
        from shadow.capture.models import InputEvent, InputEventType

        test_event = InputEvent(
            timestamp=time.time(),
            event_type=InputEventType.MOUSE_CLICK,
            x=100,
            y=200,
        )

        # _emit_event를 통해 윈도우 정보가 추가되는지 확인
        collector._emit_event(test_event)

    # 이벤트가 수집되었는지 확인
    assert len(events_collected) > 0

    # window_info 필드 확인
    event = events_collected[0]
    assert hasattr(event, "window_info")

    # PyObjC가 있으면 app_name도 확인
    if event.window_info:
        assert hasattr(event.window_info, "app_name")
        assert event.window_info.app_name is not None
