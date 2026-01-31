"""활성 윈도우 정보 수집 모듈 (macOS)

F-03: 현재 활성화된 윈도우의 앱 이름과 윈도우 타이틀을 수집합니다.
"""

from shadow.capture.models import WindowInfo

try:
    from AppKit import NSWorkspace

    HAS_APPKIT = True
except ImportError:
    HAS_APPKIT = False

try:
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGNullWindowID,
        kCGWindowListOptionOnScreenOnly,
    )

    HAS_QUARTZ = True
except ImportError:
    HAS_QUARTZ = False


class WindowInfoCollector:
    """macOS 활성 윈도우 정보 수집기"""

    def __init__(self):
        """초기화 - AppKit 사용 가능 여부 확인

        Raises:
            RuntimeError: PyObjC가 설치되지 않은 경우
        """
        if not HAS_APPKIT:
            raise RuntimeError(
                "pyobjc-framework-Cocoa가 설치되지 않았습니다. "
                "pip install pyobjc-framework-Cocoa"
            )

        self._workspace = NSWorkspace.sharedWorkspace()

    def get_active_window(self) -> WindowInfo:
        """현재 활성 윈도우 정보 반환

        Returns:
            WindowInfo: 활성 윈도우 정보 (app_name, window_title 포함)

        Raises:
            RuntimeError: 활성 윈도우 정보를 가져올 수 없는 경우
        """
        try:
            active_app = self._workspace.frontmostApplication()

            if active_app is None:
                raise RuntimeError("활성 애플리케이션을 찾을 수 없습니다")

            app_name = active_app.localizedName() or "Unknown"
            bundle_id = active_app.bundleIdentifier()
            process_id = active_app.processIdentifier()

            # F-03: 윈도우 타이틀 수집 (Quartz 사용)
            window_title = self._get_window_title(process_id)

            return WindowInfo(
                app_name=app_name,
                window_title=window_title,
                bundle_id=bundle_id,
                process_id=process_id,
            )
        except Exception as e:
            raise RuntimeError(f"윈도우 정보 수집 실패: {e}")

    def _get_window_title(self, process_id: int) -> str:
        """프로세스 ID로 윈도우 타이틀 가져오기"""
        if not HAS_QUARTZ:
            return "Unknown"

        try:
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            )

            if window_list:
                for window in window_list:
                    if window.get("kCGWindowOwnerPID") == process_id:
                        title = window.get("kCGWindowName", "")
                        if title:
                            return title

            return "Unknown"
        except Exception:
            return "Unknown"

    @staticmethod
    def is_available() -> bool:
        """이 플랫폼에서 사용 가능한지 확인

        Returns:
            bool: macOS에서만 True
        """
        return HAS_APPKIT


def get_active_window() -> WindowInfo:
    """현재 활성 윈도우 정보 반환 (편의 함수)

    Returns:
        현재 활성 윈도우의 앱 이름과 타이틀

    Note:
        PyObjC가 설치되지 않았거나 macOS가 아닌 경우 "Unknown" 반환
    """
    try:
        collector = WindowInfoCollector()
        return collector.get_active_window()
    except RuntimeError:
        return WindowInfo(app_name="Unknown", window_title="Unknown")
    except Exception:
        return WindowInfo(app_name="Unknown", window_title="Unknown")
