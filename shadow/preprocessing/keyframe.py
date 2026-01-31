"""키프레임 추출 모듈"""

from shadow.capture.models import Frame, InputEvent, InputEventType, Keyframe
from shadow.capture.recorder import RecordingSession


class KeyframeExtractor:
    """클릭 이벤트 시점의 키프레임 추출"""

    def __init__(
        self,
        trigger_events: set[InputEventType] | None = None,
        time_tolerance: float = 0.1,
    ):
        """
        Args:
            trigger_events: 키프레임을 트리거하는 이벤트 타입 (기본: 마우스 클릭)
            time_tolerance: 이벤트와 프레임 간 허용 시간차 (초)
        """
        self._trigger_events = trigger_events or {InputEventType.MOUSE_CLICK}
        self._time_tolerance = time_tolerance

    def extract(self, session: RecordingSession) -> list[Keyframe]:
        """녹화 세션에서 키프레임 추출

        Args:
            session: 녹화 세션

        Returns:
            추출된 키프레임 목록
        """
        keyframes = []

        # 트리거 이벤트 필터링
        trigger_events = [
            e for e in session.events if e.event_type in self._trigger_events
        ]

        for event in trigger_events:
            # 이벤트 시점에 가장 가까운 프레임 찾기
            closest_frame = self._find_closest_frame(event, session.frames)
            if closest_frame is not None:
                keyframes.append(Keyframe(frame=closest_frame, trigger_event=event))

        return keyframes

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

    def extract_from_events(
        self, frames: list[Frame], events: list[InputEvent]
    ) -> list[Keyframe]:
        """프레임과 이벤트 목록에서 직접 키프레임 추출

        Args:
            frames: 프레임 목록
            events: 이벤트 목록

        Returns:
            추출된 키프레임 목록
        """
        # 임시 세션 생성하여 재사용
        from shadow.capture.recorder import RecordingSession

        session = RecordingSession(frames=frames, events=events)
        return self.extract(session)
