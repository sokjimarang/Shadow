"""사용자 및 설정 Repository

users 및 configs 테이블과 상호작용
"""

from datetime import datetime
from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class UserRepository:
    """사용자 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_user(
        self, slack_user_id: str, slack_channel_id: str, settings: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """새 사용자 생성

        Args:
            slack_user_id: Slack 사용자 ID
            slack_channel_id: DM 채널 ID
            settings: 사용자 설정 (선택)

        Returns:
            생성된 사용자

        Raises:
            ShadowAPIError: 생성 실패 시
        """
        try:
            response = (
                self.db.table("users")
                .insert(
                    {
                        "slack_user_id": slack_user_id,
                        "slack_channel_id": slack_channel_id,
                        "settings": settings or {},
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="사용자 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="사용자 생성 중 오류 발생",
                details=str(e),
            )

    def get_user(self, user_id: str) -> dict[str, Any]:
        """사용자 조회 (ID로)

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 정보

        Raises:
            ShadowAPIError: 사용자 없음 또는 조회 실패
        """
        try:
            response = self.db.table("users").select("*").eq("id", user_id).execute()

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"사용자를 찾을 수 없습니다: {user_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="사용자 조회 중 오류 발생",
                details=str(e),
            )

    def get_user_by_slack_id(self, slack_user_id: str) -> dict[str, Any] | None:
        """사용자 조회 (Slack ID로)

        Args:
            slack_user_id: Slack 사용자 ID

        Returns:
            사용자 정보 (없으면 None)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("users")
                .select("*")
                .eq("slack_user_id", slack_user_id)
                .execute()
            )

            return response.data[0] if response.data else None
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="사용자 조회 중 오류 발생",
                details=str(e),
            )

    def update_user_settings(self, user_id: str, settings: dict[str, Any]) -> dict[str, Any]:
        """사용자 설정 업데이트

        Args:
            user_id: 사용자 ID
            settings: 업데이트할 설정

        Returns:
            업데이트된 사용자

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            response = (
                self.db.table("users")
                .update({"settings": settings})
                .eq("id", user_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"사용자를 찾을 수 없습니다: {user_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="사용자 설정 업데이트 중 오류 발생",
                details=str(e),
            )

    def update_slack_channel(self, user_id: str, slack_channel_id: str) -> dict[str, Any]:
        """Slack 채널 ID 업데이트

        Args:
            user_id: 사용자 ID
            slack_channel_id: 새 채널 ID

        Returns:
            업데이트된 사용자

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            response = (
                self.db.table("users")
                .update({"slack_channel_id": slack_channel_id})
                .eq("id", user_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"사용자를 찾을 수 없습니다: {user_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="Slack 채널 업데이트 중 오류 발생",
                details=str(e),
            )


class ConfigRepository:
    """설정 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_config(
        self,
        user_id: str,
        excluded_apps: list[str] | None = None,
        capture_interval_ms: int = 100,
        min_pattern_occurrences: int = 3,
        hitl_max_questions: int = 5,
    ) -> dict[str, Any]:
        """새 설정 생성

        Args:
            user_id: 사용자 ID
            excluded_apps: 제외할 앱 목록
            capture_interval_ms: 캡처 간격 (밀리초)
            min_pattern_occurrences: 패턴 최소 발생 횟수
            hitl_max_questions: 한 번에 최대 질문 수

        Returns:
            생성된 설정

        Raises:
            ShadowAPIError: 생성 실패 시
        """
        try:
            response = (
                self.db.table("configs")
                .insert(
                    {
                        "user_id": user_id,
                        "excluded_apps": excluded_apps or [],
                        "capture_interval_ms": capture_interval_ms,
                        "min_pattern_occurrences": min_pattern_occurrences,
                        "hitl_max_questions": hitl_max_questions,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="설정 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="설정 생성 중 오류 발생",
                details=str(e),
            )

    def get_config(self, user_id: str) -> dict[str, Any]:
        """사용자 설정 조회

        Args:
            user_id: 사용자 ID

        Returns:
            설정 정보

        Raises:
            ShadowAPIError: 설정 없음 또는 조회 실패
        """
        try:
            response = self.db.table("configs").select("*").eq("user_id", user_id).execute()

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"설정을 찾을 수 없습니다: {user_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="설정 조회 중 오류 발생",
                details=str(e),
            )

    def update_config(self, user_id: str, **updates: Any) -> dict[str, Any]:
        """설정 업데이트

        Args:
            user_id: 사용자 ID
            **updates: 업데이트할 필드들
                - excluded_apps: 제외할 앱 목록
                - capture_interval_ms: 캡처 간격
                - min_pattern_occurrences: 패턴 최소 발생 횟수
                - hitl_max_questions: 최대 질문 수

        Returns:
            업데이트된 설정

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            update_data = {**updates, "updated_at": datetime.utcnow().isoformat()}

            response = (
                self.db.table("configs")
                .update(update_data)
                .eq("user_id", user_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"설정을 찾을 수 없습니다: {user_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="설정 업데이트 중 오류 발생",
                details=str(e),
            )

    def add_excluded_app(self, user_id: str, app_name: str) -> dict[str, Any]:
        """제외 앱 추가

        Args:
            user_id: 사용자 ID
            app_name: 추가할 앱 이름

        Returns:
            업데이트된 설정

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            config = self.get_config(user_id)
            excluded_apps = config.get("excluded_apps", [])

            if app_name not in excluded_apps:
                excluded_apps.append(app_name)
                return self.update_config(user_id, excluded_apps=excluded_apps)

            return config
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="제외 앱 추가 중 오류 발생",
                details=str(e),
            )

    def remove_excluded_app(self, user_id: str, app_name: str) -> dict[str, Any]:
        """제외 앱 제거

        Args:
            user_id: 사용자 ID
            app_name: 제거할 앱 이름

        Returns:
            업데이트된 설정

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            config = self.get_config(user_id)
            excluded_apps = config.get("excluded_apps", [])

            if app_name in excluded_apps:
                excluded_apps.remove(app_name)
                return self.update_config(user_id, excluded_apps=excluded_apps)

            return config
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="제외 앱 제거 중 오류 발생",
                details=str(e),
            )
