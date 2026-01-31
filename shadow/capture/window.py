"""활성 윈도우 정보 수집 모듈 (macOS)

F-03: 현재 활성화된 윈도우의 앱 이름과 윈도우 타이틀을 수집합니다.
"""

import logging
import os
import sys

from shadow.capture.models import WindowInfo

logger = logging.getLogger(__name__)

try:
    from AppKit import NSRunningApplication, NSWorkspace

    HAS_APPKIT = True
except ImportError:
    HAS_APPKIT = False

try:
    from Quartz import (
        CGDisplayBounds,
        CGMainDisplayID,
        CGWindowListCopyWindowInfo,
        kCGNullWindowID,
        kCGWindowListExcludeDesktopElements,
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
            # 전략: NSWorkspace + Quartz 조합
            # 1. NSWorkspace로 활성 앱 PID 가져오기
            # 2. Quartz로 해당 PID의 윈도우 타이틀 찾기

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

    def get_window_at_point(self, x: int, y: int) -> WindowInfo:
        """지정 좌표에 위치한 윈도우 정보 반환

        마우스 클릭 좌표 기준으로 실제 대상 앱/타이틀을 찾기 위해 사용.
        (PRD는 다중 모니터를 비목표로 두므로 메인 디스플레이 기준으로 변환)
        """
        if not HAS_QUARTZ:
            return self.get_active_window()

        try:
            frontmost_app = self._workspace.frontmostApplication()
            frontmost_pid = (
                frontmost_app.processIdentifier() if frontmost_app else None
            )
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
                kCGNullWindowID,
            )

            if not window_list:
                return self.get_active_window()

            usable_windows = []
            for window in window_list:
                if not self._is_usable_window(window):
                    continue
                bounds = window.get("kCGWindowBounds", {})
                if not bounds:
                    continue
                usable_windows.append((window, bounds))

            # Quartz 좌표계는 좌하단 기준이므로 y를 반전 (단일 모니터 가정)
            display_bounds = CGDisplayBounds(CGMainDisplayID())
            display_height = int(display_bounds.size.height)
            cg_y = display_height - y

            def find_window_at_point(px: int, py: int) -> dict | None:
                for window, bounds in usable_windows:
                    wx = int(bounds.get("X", 0))
                    wy = int(bounds.get("Y", 0))
                    ww = int(bounds.get("Width", 0))
                    wh = int(bounds.get("Height", 0))

                    if wx <= px <= wx + ww and wy <= py <= wy + wh:
                        return window
                return None

            direct_match = find_window_at_point(x, y)
            inverted_match = find_window_at_point(x, cg_y)

            selected = None
            if direct_match and inverted_match and frontmost_pid is not None:
                direct_pid = direct_match.get("kCGWindowOwnerPID")
                inverted_pid = inverted_match.get("kCGWindowOwnerPID")
                if direct_pid == frontmost_pid:
                    selected = direct_match
                elif inverted_pid == frontmost_pid:
                    selected = inverted_match
                else:
                    selected = direct_match
            else:
                selected = direct_match or inverted_match

            if selected:
                return self._window_info_from_window_dict(selected)

            return self.get_active_window()
        except Exception:
            return self.get_active_window()

    def _get_active_window_via_quartz(self) -> WindowInfo | None:
        """Quartz API로 활성 윈도우 정보 가져오기 (스레드 안전)

        Note: 현재 사용되지 않음 - frontmostApplication() 사용 중
        """
        try:
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
                kCGNullWindowID,
            )

            if not window_list:
                return None

            # kCGWindowLayer가 0인 윈도우 중 가장 먼저 나오는 것이 활성 윈도우
            for window in window_list:
                if not self._is_usable_window(window):
                    continue

                # Layer 0 = 일반 애플리케이션 윈도우
                layer = window.get("kCGWindowLayer", 0)
                if layer == 0:
                    return self._window_info_from_window_dict(window)

            return None
        except Exception:
            return None

    def _get_window_title(self, process_id: int) -> str:
        """프로세스 ID로 윈도우 타이틀 가져오기"""
        if not HAS_QUARTZ:
            return "Unknown"

        try:
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
                kCGNullWindowID,
            )

            if window_list:
                for window in window_list:
                    if window.get("kCGWindowOwnerPID") != process_id:
                        continue
                    if not self._is_usable_window(window):
                        continue
                    title = window.get("kCGWindowName", "")
                    if title:
                        return title

            return "Unknown"
        except Exception:
            return "Unknown"

    def _window_info_from_window_dict(self, window: dict) -> WindowInfo:
        """Quartz window dict를 WindowInfo로 변환"""
        app_name = window.get("kCGWindowOwnerName") or "Unknown"
        window_title = window.get("kCGWindowName") or "Unknown"
        process_id = window.get("kCGWindowOwnerPID")
        bundle_id = None

        if process_id is not None:
            try:
                running_app = NSRunningApplication.runningApplicationWithProcessIdentifier(
                    process_id
                )
                if running_app:
                    bundle_id = running_app.bundleIdentifier()
            except Exception:
                bundle_id = None

        return WindowInfo(
            app_name=app_name,
            window_title=window_title,
            bundle_id=bundle_id,
            process_id=process_id,
        )

    @staticmethod
    def _is_usable_window(window: dict) -> bool:
        """시스템/오버레이 윈도우 제외 필터"""
        if not window:
            return False

        layer = window.get("kCGWindowLayer", 0)
        if layer != 0:
            return False

        owner = (window.get("kCGWindowOwnerName") or "").strip()
        if owner in {
            "Window Server",
            "Dock",
            "Control Center",
            "Notification Center",
            "스크린샷",
            "Screenshot",
            "TextInputMenuAgent",
            "SystemUIServer",
        }:
            return False

        if window.get("kCGWindowIsOnscreen") is False:
            return False

        alpha = window.get("kCGWindowAlpha")
        if alpha is not None and alpha == 0:
            return False

        return True

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
    except RuntimeError as exc:
        logger.warning(
            "Active window info unavailable (macOS only): %s",
            exc,
        )
        return WindowInfo(app_name="Unknown", window_title="Unknown")
    except Exception:
        logger.exception("Active window info unexpected error")
        return WindowInfo(app_name="Unknown", window_title="Unknown")


def get_window_at_point(x: int, y: int) -> WindowInfo:
    """좌표 기반 윈도우 정보 반환 (편의 함수)"""
    try:
        collector = WindowInfoCollector()
        return collector.get_window_at_point(x, y)
    except RuntimeError as exc:
        logger.warning(
            "Active window info unavailable (macOS only): %s",
            exc,
        )
        return WindowInfo(app_name="Unknown", window_title="Unknown")
    except Exception:
        logger.exception("Active window info unexpected error")
        return WindowInfo(app_name="Unknown", window_title="Unknown")


def get_current_process_info() -> dict[str, str | int | None]:
    """현재 프로세스의 앱/번들 정보를 반환 (권한 안내용)"""
    pid = os.getpid()
    app_name = None
    bundle_id = None

    if HAS_APPKIT:
        try:
            running_app = NSRunningApplication.runningApplicationWithProcessIdentifier(pid)
            if running_app:
                app_name = running_app.localizedName()
                bundle_id = running_app.bundleIdentifier()
        except Exception:
            app_name = None
            bundle_id = None

    return {
        "pid": pid,
        "app_name": app_name,
        "bundle_id": bundle_id,
        "executable": sys.executable,
    }
