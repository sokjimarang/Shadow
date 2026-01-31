"""InputEventCollector + WindowInfo 통합 테스트"""

import time

from shadow.capture.input_events import InputEventCollector

if __name__ == "__main__":
    print("5초간 이벤트 수집 시작... (마우스 클릭해보세요)")

    collector = InputEventCollector()
    with collector:
        time.sleep(5)
        events = collector.get_events()

    print(f"\n수집된 이벤트: {len(events)}개")
    for i, event in enumerate(events, 1):
        app_info = (
            f"in {event.window_info.app_name}" if event.window_info else "no window info"
        )
        print(f"{i}. {event.event_type.value} {app_info}")

    # window_info 필드 존재 확인
    if events:
        print(f"\n✓ window_info 필드 존재: {hasattr(events[0], 'window_info')}")
        if events[0].window_info:
            print(f"✓ app_name 필드 존재: {hasattr(events[0].window_info, 'app_name')}")
            print(f"✓ app_name 값: {events[0].window_info.app_name}")
