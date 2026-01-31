"""Recorder 통합 테스트 (F-01 + F-02 통합)"""

import time

import numpy as np
import pytest
from pynput.mouse import Button, Controller

from shadow.capture.models import InputEvent, InputEventType
from shadow.capture.recorder import Recorder, RecordingSession


class TestRecorder:
    """Recorder 기본 기능 테스트"""

    def test_recorder_initialization(self):
        """Recorder 초기화 확인"""
        recorder = Recorder()

        assert recorder is not None
        assert not recorder.is_recording

    def test_recorder_record_creates_session(self):
        """녹화가 RecordingSession을 생성하는지 확인"""
        recorder = Recorder(fps=10)

        session = recorder.record(duration=0.5)

        assert isinstance(session, RecordingSession)
        assert session.duration > 0
        assert session.start_time > 0
        assert session.end_time > 0

    def test_recorder_captures_frames(self):
        """녹화 중 프레임이 캡처되는지 확인"""
        recorder = Recorder(fps=10)

        session = recorder.record(duration=0.5)

        # 0.5초 동안 fps=10이면 약 5개 프레임 예상
        assert len(session.frames) >= 3
        assert len(session.frames) <= 10

        # 프레임 검증
        for frame in session.frames:
            assert frame.timestamp > 0
            assert isinstance(frame.image, np.ndarray)
            assert frame.image.ndim == 3
            assert frame.image.shape[2] == 3

    def test_recorder_records_events(self):
        """녹화 중 이벤트가 수집되는지 확인 (실제 마우스 클릭)"""
        recorder = Recorder(fps=10)
        mouse = Controller()

        # 녹화 시작
        recorder.start()
        time.sleep(0.1)

        # 실제 마우스 클릭 시뮬레이션
        initial_position = mouse.position
        mouse.click(Button.left, 1)

        time.sleep(0.2)
        session = recorder.stop()

        # 클릭 이벤트가 수집되었는지 확인
        assert len(session.events) >= 1
        click_events = [e for e in session.events if e.event_type == InputEventType.MOUSE_CLICK]
        assert len(click_events) >= 1


class TestRecordingSession:
    """RecordingSession 데이터 구조 테스트"""

    def test_recording_session_initialization(self):
        """RecordingSession 초기화"""
        session = RecordingSession()

        assert session.frames == []
        assert session.events == []
        assert session.start_time == 0.0
        assert session.end_time == 0.0

    def test_recording_session_duration(self):
        """RecordingSession duration 계산"""
        session = RecordingSession()
        session.start_time = 100.0
        session.end_time = 105.5

        assert session.duration == 5.5


class TestRecorderStartStop:
    """Recorder start/stop 테스트"""

    def test_recorder_start_sets_recording_flag(self):
        """녹화 시작 시 is_recording 플래그 설정"""
        recorder = Recorder()

        recorder.start()

        assert recorder.is_recording

        # 정리
        recorder.stop()

    def test_recorder_stop_returns_session(self):
        """녹화 중지 시 세션 반환"""
        recorder = Recorder(fps=10)

        recorder.start()
        time.sleep(0.3)
        session = recorder.stop()

        assert isinstance(session, RecordingSession)
        assert len(session.frames) > 0

    def test_recorder_stop_resets_recording_flag(self):
        """녹화 중지 후 is_recording 플래그 초기화"""
        recorder = Recorder()

        recorder.start()
        recorder.stop()

        assert not recorder.is_recording

    def test_recorder_stop_without_start_returns_empty_session(self):
        """시작하지 않고 중지하면 빈 세션 반환"""
        recorder = Recorder()

        session = recorder.stop()

        assert isinstance(session, RecordingSession)
        assert len(session.frames) == 0
        assert len(session.events) == 0


class TestRecorderFrameEventSynchronization:
    """프레임과 이벤트 동기화 테스트"""

    def test_frames_and_events_have_consistent_timestamps(self):
        """프레임과 이벤트의 타임스탬프가 일관되는지 확인"""
        recorder = Recorder(fps=10)
        mouse = Controller()

        recorder.start()
        time.sleep(0.1)

        # 실제 마우스 클릭 시뮬레이션
        click_time = time.time()
        mouse.click(Button.left, 1)

        time.sleep(0.2)
        session = recorder.stop()

        # 프레임과 이벤트가 모두 수집되었는지 확인
        assert len(session.frames) > 0
        assert len(session.events) > 0

        # 클릭 이벤트 확인
        click_events = [e for e in session.events if e.event_type == InputEventType.MOUSE_CLICK]
        assert len(click_events) >= 1

        # 타임스탬프 범위 확인
        frame_timestamps = [f.timestamp for f in session.frames]

        # 클릭 이벤트의 타임스탬프가 프레임 타임스탬프 범위 내에 있는지
        for click_event in click_events:
            assert min(frame_timestamps) <= click_event.timestamp <= max(frame_timestamps)

    def test_session_duration_matches_recording_time(self):
        """세션 duration이 실제 녹화 시간과 일치하는지 확인"""
        recorder = Recorder(fps=10)

        expected_duration = 0.5
        session = recorder.record(duration=expected_duration)

        # 오차 허용 (±20%)
        assert abs(session.duration - expected_duration) < expected_duration * 0.2
