"""활성 윈도우 정보 수집 모듈"""

try:
    from AppKit import NSWorkspace

    HAS_APPKIT = True
except ImportError:
    HAS_APPKIT = False

from shadow.capture.models import WindowInfo


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
            WindowInfo: 활성 윈도우 정보

        Raises:
            RuntimeError: 활성 윈도우 정보를 가져올 수 없는 경우
        """
        try:
            active_app = self._workspace.frontmostApplication()

            if active_app is None:
                raise RuntimeError("활성 애플리케이션을 찾을 수 없습니다")

            return WindowInfo(
                app_name=active_app.localizedName() or "Unknown",
                bundle_id=active_app.bundleIdentifier(),
                process_id=active_app.processIdentifier(),
            )
        except Exception as e:
            raise RuntimeError(f"윈도우 정보 수집 실패: {e}")

    @staticmethod
    def is_available() -> bool:
        """이 플랫폼에서 사용 가능한지 확인

        Returns:
            bool: macOS에서만 True
        """
        return HAS_APPKIT
