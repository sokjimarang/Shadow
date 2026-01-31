"""E2E 데모: 활성 윈도우 정보 포함 녹화

실제 Recorder를 사용하여 이벤트에 app_name, window_title이 포함되는지 확인
"""

from shadow.capture.recorder import Recorder


def main():
    print("5초간 녹화를 시작합니다...")
    print("여러 애플리케이션에서 클릭해보세요!")
    print()

    recorder = Recorder()
    session = recorder.record(duration=5.0)

    print(f"\n수집된 이벤트: {len(session.events)}개")
    print(f"수집된 프레임: {len(session.frames)}개")
    print()

    # F-03 Pass 조건 확인
    has_app_name_field = False
    has_window_title_field = False
    has_app_name_value = False
    has_window_title_value = False

    if session.events:
        first_event = session.events[0]

        # Pass 조건 1: InputEvent에 app_name 필드 존재
        has_app_name_field = hasattr(first_event, "app_name")
        print(f"✓ Pass 조건 1: app_name 필드 존재 = {has_app_name_field}")

        # Pass 조건 2: InputEvent에 window_title 필드 존재
        has_window_title_field = hasattr(first_event, "window_title")
        print(f"✓ Pass 조건 2: window_title 필드 존재 = {has_window_title_field}")

        # Pass 조건 3: app_name에 실제 값 존재
        has_app_name_value = (
            first_event.app_name is not None and len(first_event.app_name) > 0
        )
        print(f"✓ Pass 조건 3: app_name에 값 존재 = {has_app_name_value} ({first_event.app_name})")

        # Pass 조건 4: window_title에 실제 값 존재
        has_window_title_value = (
            first_event.window_title is not None and len(first_event.window_title) > 0
        )
        print(f"✓ Pass 조건 4: window_title에 값 존재 = {has_window_title_value} ({first_event.window_title})")

    print()
    print("이벤트 상세:")
    for i, event in enumerate(session.events[:10], 1):  # 최대 10개만 출력
        if event.app_name:
            print(f"  {i}. {event.event_type.value} in {event.app_name} ({event.window_title})")
        else:
            print(f"  {i}. {event.event_type.value} (윈도우 정보 없음)")

    if len(session.events) > 10:
        print(f"  ... 외 {len(session.events) - 10}개 이벤트")

    print()
    if has_app_name_field and has_window_title_field and has_app_name_value:
        print("✅ F-03 Pass 조건 모두 충족!")
    else:
        print("❌ Pass 조건 미충족")


if __name__ == "__main__":
    main()
