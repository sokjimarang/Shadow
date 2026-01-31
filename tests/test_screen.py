"""ScreenCapture 단위 테스트 (F-01)"""

import time

import numpy as np
import pytest

from shadow.capture.screen import ScreenCapture


class TestScreenCapture:
    """ScreenCapture 기본 기능 테스트"""

    def test_capture_frame_returns_valid_frame(self):
        """프레임 캡처가 유효한 Frame 객체를 반환하는지 확인"""
        capture = ScreenCapture()

        with capture.session():
            frame = capture.capture_frame()

            # Frame 검증
            assert frame is not None
            assert hasattr(frame, "timestamp")
            assert hasattr(frame, "image")
            assert isinstance(frame.timestamp, float)
            assert isinstance(frame.image, np.ndarray)

    def test_capture_frame_has_correct_shape(self):
        """캡처된 프레임이 올바른 shape (H, W, 3)을 가지는지 확인"""
        capture = ScreenCapture()

        with capture.session():
            frame = capture.capture_frame()

            # RGB 이미지 (H, W, 3)
            assert frame.image.ndim == 3
            assert frame.image.shape[2] == 3
            assert frame.height > 0
            assert frame.width > 0

    def test_capture_frame_outside_session_raises_error(self):
        """세션 없이 캡처 시도하면 에러 발생"""
        capture = ScreenCapture()

        with pytest.raises(RuntimeError, match="캡처 세션이 시작되지 않음"):
            capture.capture_frame()

    def test_fps_setting(self):
        """FPS 설정이 올바르게 적용되는지 확인"""
        fps = 10
        capture = ScreenCapture(fps=fps)

        assert capture._fps == fps
        assert capture._frame_interval == 1.0 / fps

    def test_monitor_info_returns_valid_dict(self):
        """모니터 정보가 유효한 딕셔너리를 반환하는지 확인"""
        capture = ScreenCapture()

        info = capture.monitor_info

        assert isinstance(info, dict)
        assert "width" in info
        assert "height" in info
        assert info["width"] > 0
        assert info["height"] > 0

    def test_capture_continuous_yields_frames(self):
        """연속 캡처가 프레임을 생성하는지 확인"""
        capture = ScreenCapture(fps=30)

        with capture.session():
            frame_count = 0
            for frame in capture.capture_continuous():
                frame_count += 1
                assert frame is not None
                assert isinstance(frame.image, np.ndarray)

                # 3개 프레임만 캡처 후 종료
                if frame_count >= 3:
                    break

            assert frame_count == 3

    def test_capture_continuous_respects_fps(self):
        """연속 캡처가 FPS를 준수하는지 확인"""
        fps = 10
        capture = ScreenCapture(fps=fps)

        with capture.session():
            timestamps = []
            for frame in capture.capture_continuous():
                timestamps.append(frame.timestamp)

                # 5개 프레임 캡처
                if len(timestamps) >= 5:
                    break

            # 프레임 간 시간 차이 검증 (오차 허용)
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i - 1]
                expected_interval = 1.0 / fps
                # 50% 오차 허용 (시스템 부하 고려)
                assert abs(interval - expected_interval) < expected_interval * 0.5


class TestScreenCaptureResolution:
    """해상도 관련 테스트"""

    def test_frame_resolution_matches_monitor(self):
        """프레임 해상도가 모니터 정보와 일치하는지 확인"""
        capture = ScreenCapture()
        monitor_info = capture.monitor_info

        with capture.session():
            frame = capture.capture_frame()

            assert frame.width == monitor_info["width"]
            assert frame.height == monitor_info["height"]

    def test_frame_properties(self):
        """Frame의 width, height 프로퍼티가 올바른지 확인"""
        capture = ScreenCapture()

        with capture.session():
            frame = capture.capture_frame()

            assert frame.width == frame.image.shape[1]
            assert frame.height == frame.image.shape[0]
