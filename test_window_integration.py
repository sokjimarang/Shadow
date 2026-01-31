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
        # F-03: app_name, window_title 직접 사용
        app_info = f"in {event.app_name}" if event.app_name else "no window info"
        title_info = f"({event.window_title})" if event.window_title else ""
        print(f"{i}. {event.event_type.value} {app_info} {title_info}")

    # F-03 필드 존재 확인
    if events:
        print(f"\n✓ app_name 필드 존재: {hasattr(events[0], 'app_name')}")
        print(f"✓ window_title 필드 존재: {hasattr(events[0], 'window_title')}")
        if events[0].app_name:
            print(f"✓ app_name 값: {events[0].app_name}")
        if events[0].window_title:
            print(f"✓ window_title 값: {events[0].window_title}")
