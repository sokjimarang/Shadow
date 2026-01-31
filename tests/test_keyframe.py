"""KeyframeExtractor 단위 테스트 (F-01)"""

import time

import numpy as np
import pytest

from shadow.capture.models import Frame, InputEvent, InputEventType
from shadow.capture.recorder import RecordingSession
from shadow.preprocessing.keyframe import KeyframeExtractor


class TestKeyframeExtractor:
    """KeyframeExtractor 기본 기능 테스트"""

    def test_extract_pairs_with_single_click(self):
        """단일 클릭 이벤트에서 Before/After 프레임 쌍 추출"""
        # 고정된 base_time 사용 (실행 시간 영향 제거)
        base_time = 1000.0
        frames = [
            Frame(timestamp=base_time + 0.0, image=np.zeros((100, 100, 3), dtype=np.uint8)),
            Frame(timestamp=base_time + 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8)),
            Frame(timestamp=base_time + 0.2, image=np.zeros((100, 100, 3), dtype=np.uint8)),
            Frame(timestamp=base_time + 0.5, image=np.zeros((100, 100, 3), dtype=np.uint8)),
        ]

        events = [
            InputEvent(
                timestamp=base_time + 0.15,
                event_type=InputEventType.MOUSE_CLICK,
                x=100,
                y=100,
            )
        ]

        session = RecordingSession(frames=frames, events=events)
        extractor = KeyframeExtractor()

        pairs = extractor.extract_pairs(session)

        assert len(pairs) == 1
        pair = pairs[0]

        # Before 프레임은 클릭과 가까운 시점 (time_tolerance 0.1초 내)
        time_diff = abs(pair.before_frame.timestamp - pair.trigger_event.timestamp)
        assert time_diff <= 0.1

        # After 프레임은 클릭 후 (after_delay 0.3초 후 근처)
        assert pair.after_frame.timestamp >= pair.trigger_event.timestamp

        # 트리거 이벤트 확인
        assert pair.trigger_event.event_type == InputEventType.MOUSE_CLICK
        assert pair.trigger_event.timestamp == base_time + 0.15

    def test_extract_pairs_with_multiple_clicks(self):
        """여러 클릭 이벤트에서 프레임 쌍 추출"""
        base_time = time.time()
        frames = [
            Frame(timestamp=base_time + i * 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8))
            for i in range(20)
        ]

        events = [
            InputEvent(
                timestamp=base_time + 0.25,
                event_type=InputEventType.MOUSE_CLICK,
                x=100,
                y=100,
            ),
            InputEvent(
                timestamp=base_time + 0.75,
                event_type=InputEventType.MOUSE_CLICK,
                x=200,
                y=200,
            ),
        ]

        session = RecordingSession(frames=frames, events=events)
        extractor = KeyframeExtractor()

        pairs = extractor.extract_pairs(session)

        assert len(pairs) == 2
        assert pairs[0].trigger_event.x == 100
        assert pairs[1].trigger_event.x == 200

    def test_extract_pairs_ignores_non_trigger_events(self):
        """트리거 이벤트가 아닌 이벤트는 무시"""
        base_time = time.time()
        frames = [
            Frame(timestamp=base_time + i * 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8))
            for i in range(10)
        ]

        events = [
            InputEvent(timestamp=base_time + 0.1, event_type=InputEventType.MOUSE_MOVE, x=50, y=50),
            InputEvent(timestamp=base_time + 0.2, event_type=InputEventType.KEY_PRESS, key="a"),
            InputEvent(timestamp=base_time + 0.3, event_type=InputEventType.MOUSE_CLICK, x=100, y=100),
        ]

        session = RecordingSession(frames=frames, events=events)
        extractor = KeyframeExtractor()

        pairs = extractor.extract_pairs(session)

        # 클릭만 추출
        assert len(pairs) == 1
        assert pairs[0].trigger_event.event_type == InputEventType.MOUSE_CLICK

    def test_extract_pairs_with_custom_trigger_events(self):
        """사용자 정의 트리거 이벤트 설정"""
        base_time = time.time()
        frames = [
            Frame(timestamp=base_time + i * 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8))
            for i in range(10)
        ]

        events = [
            InputEvent(timestamp=base_time + 0.1, event_type=InputEventType.MOUSE_CLICK, x=100, y=100),
            InputEvent(timestamp=base_time + 0.3, event_type=InputEventType.MOUSE_SCROLL, dx=0, dy=10),
        ]

        session = RecordingSession(frames=frames, events=events)

        # 스크롤도 트리거로 설정
        extractor = KeyframeExtractor(
            trigger_events={InputEventType.MOUSE_CLICK, InputEventType.MOUSE_SCROLL}
        )

        pairs = extractor.extract_pairs(session)

        assert len(pairs) == 2
        assert pairs[0].trigger_event.event_type == InputEventType.MOUSE_CLICK
        assert pairs[1].trigger_event.event_type == InputEventType.MOUSE_SCROLL

    def test_extract_pairs_with_custom_after_delay(self):
        """After 프레임 지연 시간 커스터마이징"""
        base_time = time.time()
        frames = [
            Frame(timestamp=base_time + i * 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8))
            for i in range(20)
        ]

        events = [
            InputEvent(
                timestamp=base_time + 0.5,
                event_type=InputEventType.MOUSE_CLICK,
                x=100,
                y=100,
            )
        ]

        session = RecordingSession(frames=frames, events=events)

        # After 지연 시간을 0.5초로 설정
        extractor = KeyframeExtractor(after_delay=0.5)

        pairs = extractor.extract_pairs(session)

        assert len(pairs) == 1
        pair = pairs[0]

        # After 프레임은 클릭 후 약 0.5초 후
        time_diff = pair.after_frame.timestamp - pair.trigger_event.timestamp
        assert 0.4 <= time_diff <= 0.6  # 0.5초 ± 0.1초 오차 허용

    def test_extract_pairs_no_frames_returns_empty(self):
        """프레임이 없으면 빈 리스트 반환"""
        events = [
            InputEvent(
                timestamp=time.time(),
                event_type=InputEventType.MOUSE_CLICK,
                x=100,
                y=100,
            )
        ]

        session = RecordingSession(frames=[], events=events)
        extractor = KeyframeExtractor()

        pairs = extractor.extract_pairs(session)

        assert len(pairs) == 0

    def test_extract_pairs_no_events_returns_empty(self):
        """이벤트가 없으면 빈 리스트 반환"""
        base_time = time.time()
        frames = [
            Frame(timestamp=base_time + i * 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8))
            for i in range(10)
        ]

        session = RecordingSession(frames=frames, events=[])
        extractor = KeyframeExtractor()

        pairs = extractor.extract_pairs(session)

        assert len(pairs) == 0

    def test_extract_alias_method(self):
        """extract() 메서드가 extract_pairs()의 별칭으로 동작하는지 확인"""
        base_time = time.time()
        frames = [
            Frame(timestamp=base_time + i * 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8))
            for i in range(10)
        ]

        events = [
            InputEvent(
                timestamp=base_time + 0.3,
                event_type=InputEventType.MOUSE_CLICK,
                x=100,
                y=100,
            )
        ]

        session = RecordingSession(frames=frames, events=events)
        extractor = KeyframeExtractor()

        pairs_from_extract = extractor.extract(session)
        pairs_from_extract_pairs = extractor.extract_pairs(session)

        assert len(pairs_from_extract) == len(pairs_from_extract_pairs)
        assert len(pairs_from_extract) == 1


class TestKeyframeExtractorEdgeCases:
    """KeyframeExtractor 엣지 케이스 테스트"""

    def test_extract_pairs_with_click_before_all_frames(self):
        """클릭이 모든 프레임보다 이전 시점인 경우"""
        base_time = time.time()

        # 클릭이 프레임들보다 이전
        events = [
            InputEvent(
                timestamp=base_time - 1.0,
                event_type=InputEventType.MOUSE_CLICK,
                x=100,
                y=100,
            )
        ]

        frames = [
            Frame(timestamp=base_time + i * 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8))
            for i in range(10)
        ]

        session = RecordingSession(frames=frames, events=events)
        extractor = KeyframeExtractor()

        pairs = extractor.extract_pairs(session)

        # Before 프레임을 찾을 수 없으므로 쌍이 생성되지 않음
        assert len(pairs) == 0

    def test_extract_pairs_with_click_after_all_frames(self):
        """클릭이 모든 프레임 이후 시점인 경우"""
        base_time = time.time()

        frames = [
            Frame(timestamp=base_time + i * 0.1, image=np.zeros((100, 100, 3), dtype=np.uint8))
            for i in range(10)
        ]

        # 클릭이 프레임들보다 이후
        events = [
            InputEvent(
                timestamp=base_time + 2.0,
                event_type=InputEventType.MOUSE_CLICK,
                x=100,
                y=100,
            )
        ]

        session = RecordingSession(frames=frames, events=events)
        extractor = KeyframeExtractor()

        pairs = extractor.extract_pairs(session)

        # Before 프레임은 마지막 프레임, After는 동일 프레임 (fallback)
        assert len(pairs) == 1
        pair = pairs[0]
        assert pair.before_frame.timestamp == frames[-1].timestamp
        assert pair.after_frame.timestamp == frames[-1].timestamp
