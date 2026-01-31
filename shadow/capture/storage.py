"""세션 저장 모듈

녹화 세션, 이벤트, 이미지를 파일로 저장합니다.
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image

from shadow.capture.models import Frame, InputEvent, InputEventType, KeyframePair
from shadow.capture.recorder import RecordingSession


class SessionStorage:
    """녹화 세션 저장소

    세션 데이터를 다음 구조로 저장합니다:
    outputs/
    └── session_<timestamp>/
        ├── session.json       # 세션 메타데이터
        ├── events.json        # 모든 입력 이벤트
        └── keyframes/
            ├── 001_before.png
            ├── 001_after.png
            ├── 001_event.json
            ├── 002_before.png
            ...
    """

    def __init__(self, base_dir: str | Path = "outputs"):
        """
        Args:
            base_dir: 출력 기본 디렉토리
        """
        self._base_dir = Path(base_dir)

    def save_session(
        self,
        session: RecordingSession,
        pairs: list[KeyframePair],
        name: str | None = None,
    ) -> Path:
        """세션과 키프레임 쌍 저장

        Args:
            session: 녹화 세션
            pairs: 키프레임 쌍 목록
            name: 세션 이름 (None이면 타임스탬프 사용)

        Returns:
            저장된 세션 디렉토리 경로
        """
        # 세션 디렉토리 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = name or f"session_{timestamp}"
        session_dir = self._base_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)

        # 키프레임 디렉토리
        keyframes_dir = session_dir / "keyframes"
        keyframes_dir.mkdir(exist_ok=True)

        # 세션 메타데이터 저장
        session_meta = {
            "name": session_name,
            "created_at": timestamp,
            "frame_count": len(session.frames),
            "event_count": len(session.events),
            "keyframe_pair_count": len(pairs),
            "duration_seconds": self._calculate_duration(session),
        }
        (session_dir / "session.json").write_text(
            json.dumps(session_meta, indent=2, ensure_ascii=False)
        )

        # 이벤트 저장
        events_data = [self._event_to_dict(e) for e in session.events]
        (session_dir / "events.json").write_text(
            json.dumps(events_data, indent=2, ensure_ascii=False)
        )

        # 키프레임 쌍 저장
        for i, pair in enumerate(pairs):
            prefix = f"{i + 1:03d}"
            self._save_keyframe_pair(keyframes_dir, prefix, pair)

        return session_dir

    def _save_keyframe_pair(
        self, directory: Path, prefix: str, pair: KeyframePair
    ) -> None:
        """키프레임 쌍 저장"""
        # Before 이미지
        before_path = directory / f"{prefix}_before.png"
        Image.fromarray(pair.before_frame.image).save(before_path)

        # After 이미지
        after_path = directory / f"{prefix}_after.png"
        Image.fromarray(pair.after_frame.image).save(after_path)

        # 이벤트 정보
        event_data = self._event_to_dict(pair.trigger_event)
        event_data["before_timestamp"] = pair.before_frame.timestamp
        event_data["after_timestamp"] = pair.after_frame.timestamp
        event_path = directory / f"{prefix}_event.json"
        event_path.write_text(json.dumps(event_data, indent=2, ensure_ascii=False))

    def _event_to_dict(self, event: InputEvent) -> dict[str, Any]:
        """InputEvent를 딕셔너리로 변환"""
        return {
            "timestamp": event.timestamp,
            "event_type": event.event_type.value,
            "x": event.x,
            "y": event.y,
            "button": event.button,
            "key": event.key,
            "dx": event.dx,
            "dy": event.dy,
            "app_name": event.app_name,
            "window_title": event.window_title,
        }

    def _calculate_duration(self, session: RecordingSession) -> float:
        """세션 지속 시간 계산"""
        if not session.frames:
            return 0.0
        return session.frames[-1].timestamp - session.frames[0].timestamp

    def load_session_events(self, session_dir: str | Path) -> list[dict[str, Any]]:
        """세션 이벤트 로드

        Args:
            session_dir: 세션 디렉토리 경로

        Returns:
            이벤트 딕셔너리 목록
        """
        events_path = Path(session_dir) / "events.json"
        if not events_path.exists():
            return []
        return json.loads(events_path.read_text())

    def load_keyframe_pairs(
        self, session_dir: str | Path
    ) -> list[tuple[Path, Path, dict[str, Any]]]:
        """키프레임 쌍 경로 및 이벤트 로드

        Args:
            session_dir: 세션 디렉토리 경로

        Returns:
            (before_path, after_path, event_data) 튜플 목록
        """
        keyframes_dir = Path(session_dir) / "keyframes"
        if not keyframes_dir.exists():
            return []

        pairs = []
        # 이벤트 파일 기준으로 정렬
        event_files = sorted(keyframes_dir.glob("*_event.json"))

        for event_file in event_files:
            prefix = event_file.stem.replace("_event", "")
            before_path = keyframes_dir / f"{prefix}_before.png"
            after_path = keyframes_dir / f"{prefix}_after.png"

            if before_path.exists() and after_path.exists():
                event_data = json.loads(event_file.read_text())
                pairs.append((before_path, after_path, event_data))

        return pairs
