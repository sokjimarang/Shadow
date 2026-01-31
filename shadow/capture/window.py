"""활성 윈도우 정보 수집 모듈 (macOS)

현재 활성화된 윈도우의 앱 이름과 윈도우 타이틀을 수집합니다.
"""

from dataclasses import dataclass


@dataclass
class WindowInfo:
    """활성 윈도우 정보"""

    app_name: str  # 애플리케이션 이름
    window_title: str  # 윈도우 타이틀


def get_active_window() -> WindowInfo:
    """현재 활성 윈도우 정보 반환 (macOS)

    Returns:
        현재 활성 윈도우의 앱 이름과 타이틀

    Note:
        PyObjC가 설치되지 않았거나 macOS가 아닌 경우 "Unknown" 반환
    """
    try:
        from AppKit import NSWorkspace
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGNullWindowID,
            kCGWindowListOptionOnScreenOnly,
        )

        # 현재 활성 앱 정보
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        app_name = active_app.localizedName() if active_app else "Unknown"

        # 활성 윈도우 타이틀 가져오기
        window_title = "Unknown"

        # 현재 화면의 모든 윈도우 목록
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        )

        if window_list:
            # 활성 앱의 PID
            active_pid = active_app.processIdentifier() if active_app else None

            for window in window_list:
                # 같은 PID의 윈도우 찾기
                if window.get("kCGWindowOwnerPID") == active_pid:
                    title = window.get("kCGWindowName", "")
                    if title:  # 빈 타이틀 제외
                        window_title = title
                        break

        return WindowInfo(app_name=app_name, window_title=window_title)

    except ImportError:
        # PyObjC 미설치 또는 비-macOS 환경
        return WindowInfo(app_name="Unknown", window_title="Unknown")
    except Exception:
        # 기타 에러
        return WindowInfo(app_name="Unknown", window_title="Unknown")
