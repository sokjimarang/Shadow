"""키프레임 추출 모듈

Before/After 프레임 쌍(KeyframePair)을 추출합니다.
"""

from shadow.capture.models import Frame, InputEvent, InputEventType, KeyframePair
from shadow.capture.recorder import RecordingSession


class KeyframeExtractor:
    """클릭 이벤트 시점의 Before/After 프레임 쌍 추출"""

    def __init__(
        self,
        trigger_events: set[InputEventType] | None = None,
        time_tolerance: float = 0.1,
        after_delay: float = 0.3,
    ):
        """
        Args:
            trigger_events: 키프레임을 트리거하는 이벤트 타입 (기본: 마우스 클릭)
            time_tolerance: 이벤트와 프레임 간 허용 시간차 (초)
            after_delay: After 프레임 지연 시간 (초, 기본 0.3초)
        """
        self._trigger_events = trigger_events or {InputEventType.MOUSE_CLICK}
        self._time_tolerance = time_tolerance
        self._after_delay = after_delay

    def _find_closest_frame(
        self, event: InputEvent, frames: list[Frame]
    ) -> Frame | None:
        """이벤트 시점에 가장 가까운 프레임 찾기

        이벤트 발생 직전의 프레임을 반환합니다 (사용자가 클릭한 화면).
        """
        if not frames:
            return None

        # 이벤트 시점 직전 또는 가장 가까운 프레임 찾기
        best_frame = None
        best_diff = float("inf")

        for frame in frames:
            # 프레임이 이벤트보다 이전이거나 허용 오차 내인 경우
            time_diff = event.timestamp - frame.timestamp

            if -self._time_tolerance <= time_diff <= self._time_tolerance:
                if abs(time_diff) < best_diff:
                    best_diff = abs(time_diff)
                    best_frame = frame

        # 허용 오차 내 프레임이 없으면 가장 가까운 이전 프레임 사용
        if best_frame is None:
            before_frames = [f for f in frames if f.timestamp <= event.timestamp]
            if before_frames:
                best_frame = before_frames[-1]  # 가장 최근 프레임

        return best_frame

    def extract_pairs(self, session: RecordingSession) -> list[KeyframePair]:
        """F-01: Before/After 프레임 쌍 추출

        클릭 직전(Before)과 직후(After) 프레임을 함께 추출합니다.

        Args:
            session: 녹화 세션

        Returns:
            KeyframePair 목록
        """
        pairs = []

        # 트리거 이벤트 필터링
        trigger_events = [
            e for e in session.events if e.event_type in self._trigger_events
        ]

        for event in trigger_events:
            # Before: 이벤트 직전 프레임
            before_frame = self._find_closest_frame(event, session.frames)
            if before_frame is None:
                continue

            # After: 이벤트 후 _after_delay 초 후 프레임
            after_timestamp = event.timestamp + self._after_delay
            after_frame = self._find_frame_at_timestamp(after_timestamp, session.frames)

            if after_frame is None:
                # After 프레임이 없으면 마지막 프레임 사용
                after_frames = [f for f in session.frames if f.timestamp > event.timestamp]
                if after_frames:
                    after_frame = after_frames[-1]
                else:
                    after_frame = before_frame  # fallback

            pairs.append(
                KeyframePair(
                    before_frame=before_frame,
                    after_frame=after_frame,
                    trigger_event=event,
                )
            )

        return pairs

    def _find_frame_at_timestamp(
        self, timestamp: float, frames: list[Frame]
    ) -> Frame | None:
        """특정 타임스탬프에 가장 가까운 프레임 찾기"""
        if not frames:
            return None

        # 타임스탬프 이후 프레임 중 가장 가까운 것
        after_frames = [f for f in frames if f.timestamp >= timestamp]
        if after_frames:
            return min(after_frames, key=lambda f: abs(f.timestamp - timestamp))

        # 없으면 이전 프레임 중 가장 가까운 것
        before_frames = [f for f in frames if f.timestamp < timestamp]
        if before_frames:
            return max(before_frames, key=lambda f: f.timestamp)

        return None

    def extract_pairs_from_events(
        self, frames: list[Frame], events: list[InputEvent]
    ) -> list[KeyframePair]:
        """프레임과 이벤트 목록에서 직접 KeyframePair 추출"""
        from shadow.capture.recorder import RecordingSession

        session = RecordingSession(frames=frames, events=events)
        return self.extract_pairs(session)
