"""System Layer 모델

세션, 사용자, 설정 등 시스템 레벨 모델을 정의합니다.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """세션 상태"""

    ACTIVE = "active"  # 녹화 중
    PAUSED = "paused"  # 일시 정지
    COMPLETED = "completed"  # 완료


class Session(BaseModel):
    """관찰 세션

    사용자의 화면 녹화 세션을 나타냅니다.
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: datetime | None = None
    status: SessionStatus = SessionStatus.ACTIVE
    event_count: int = 0
    observation_count: int = 0

    model_config = {"use_enum_values": True}

    def pause(self) -> None:
        """세션 일시 정지"""
        self.status = SessionStatus.PAUSED

    def resume(self) -> None:
        """세션 재개"""
        self.status = SessionStatus.ACTIVE

    def complete(self, end_time: datetime | None = None) -> None:
        """세션 완료"""
        self.end_time = end_time or datetime.now()
        self.status = SessionStatus.COMPLETED

    def increment_event(self) -> None:
        """이벤트 카운트 증가"""
        self.event_count += 1

    def increment_observation(self) -> None:
        """관찰 카운트 증가"""
        self.observation_count += 1


class UserSettings(BaseModel):
    """사용자 설정"""

    notification_enabled: bool = True
    auto_pause_on_idle: bool = True
    idle_timeout_seconds: int = 300  # 5분


class User(BaseModel):
    """사용자

    Shadow 시스템 사용자 정보입니다.
    """

    id: UUID = Field(default_factory=uuid4)
    slack_user_id: str
    slack_channel_id: str  # DM 채널 ID
    created_at: datetime = Field(default_factory=datetime.now)
    settings: UserSettings = Field(default_factory=UserSettings)


class Config(BaseModel):
    """시스템 설정

    사용자별 시스템 설정입니다.
    """

    user_id: UUID
    excluded_apps: list[str] = Field(default_factory=list)  # 제외할 앱 목록
    capture_interval_ms: int = 100  # 캡처 간격 (밀리초)
    min_pattern_occurrences: int = 3  # 패턴 최소 발생 횟수
    hitl_max_questions: int = 5  # 한 번에 최대 질문 수

    def exclude_app(self, app_name: str) -> None:
        """앱 제외 목록에 추가"""
        if app_name not in self.excluded_apps:
            self.excluded_apps.append(app_name)

    def include_app(self, app_name: str) -> None:
        """앱 제외 목록에서 제거"""
        if app_name in self.excluded_apps:
            self.excluded_apps.remove(app_name)

    def is_app_excluded(self, app_name: str) -> bool:
        """앱이 제외 목록에 있는지 확인"""
        return app_name in self.excluded_apps
