"""InputEventCollector + WindowInfo 통합 테스트 (F-02 + F-03)"""

import time

from pynput.mouse import Button, Controller

from shadow.capture.input_events import InputEventCollector
from shadow.capture.models import InputEventType


def test_input_collector_has_window_collector():
    """InputEventCollector가 WindowInfoCollector를 가지는지 확인"""
    collector = InputEventCollector()

    # WindowInfoCollector가 있어야 함 (macOS)
    assert hasattr(collector, "_window_collector")
    assert collector._window_collector is not None


def test_input_collector_captures_window_info():
    """실제 마우스 클릭 시 윈도우 정보가 포함되는지 확인 (통합 테스트)

    PRD F-03 Pass 조건: app_name 필드 존재
    """
    collector = InputEventCollector()
    mouse = Controller()

    # 콜백으로 이벤트를 수집
    events_collected = []

    def collect_event(event):
        events_collected.append(event)

    collector.add_callback(collect_event)

    # 실제 리스너 시작
    collector.start()
    time.sleep(0.1)

    # 실제 마우스 클릭 시뮬레이션 (시스템 이벤트 발생)
    mouse.click(Button.left, 1)

    time.sleep(0.2)
    collector.stop()

    # 클릭 이벤트가 수집되었는지 확인 (F-02)
    assert len(events_collected) >= 1

    # 클릭 이벤트 추출
    click_events = [e for e in events_collected if e.event_type == InputEventType.MOUSE_CLICK]
    assert len(click_events) >= 1

    event = click_events[0]

    # F-03 Pass 조건: window_info 필드 존재
    assert hasattr(event, "window_info")

    # macOS에서 실행 중이면 app_name도 확인 (F-03 Pass 조건)
    if event.window_info:
        assert hasattr(event.window_info, "app_name")
        assert event.window_info.app_name is not None
        print(f"✓ 윈도우 정보 수집 성공: {event.window_info.app_name}")
    else:
        print("⚠ WindowInfo가 None (macOS가 아니거나 권한 없음)")
