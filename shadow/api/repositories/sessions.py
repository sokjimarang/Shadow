"""세션 Repository

sessions 테이블과 상호작용
"""

from datetime import datetime
from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class SessionRepository:
    """세션 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_session(self, user_id: str) -> dict[str, Any]:
        """새 세션 생성

        Args:
            user_id: 사용자 ID

        Returns:
            생성된 세션

        Raises:
            ShadowAPIError: 생성 실패 시
        """
        try:
            response = (
                self.db.table("sessions")
                .insert(
                    {
                        "user_id": user_id,
                        "status": "active",
                        "start_time": datetime.utcnow().isoformat(),
                        "event_count": 0,
                        "observation_count": 0,
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="세션 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="세션 생성 중 오류 발생",
                details=str(e),
            )

    def get_session(self, session_id: str) -> dict[str, Any]:
        """세션 조회

        Args:
            session_id: 세션 ID

        Returns:
            세션 정보

        Raises:
            ShadowAPIError: 세션 없음 또는 조회 실패
        """
        try:
            response = self.db.table("sessions").select("*").eq("id", session_id).execute()

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"세션을 찾을 수 없습니다: {session_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="세션 조회 중 오류 발생",
                details=str(e),
            )

    def update_session_status(self, session_id: str, status: str) -> dict[str, Any]:
        """세션 상태 업데이트

        Args:
            session_id: 세션 ID
            status: 새 상태 (active/paused/completed)

        Returns:
            업데이트된 세션

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            update_data: dict[str, Any] = {"status": status}

            if status == "completed":
                update_data["end_time"] = datetime.utcnow().isoformat()

            response = (
                self.db.table("sessions")
                .update(update_data)
                .eq("id", session_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"세션을 찾을 수 없습니다: {session_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="세션 상태 업데이트 중 오류 발생",
                details=str(e),
            )

    def increment_counts(
        self, session_id: str, event_count: int = 0, observation_count: int = 0
    ) -> dict[str, Any]:
        """세션의 이벤트/관찰 카운트 증가

        Args:
            session_id: 세션 ID
            event_count: 증가할 이벤트 수
            observation_count: 증가할 관찰 수

        Returns:
            업데이트된 세션

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            # 현재 세션 조회
            session = self.get_session(session_id)

            # 카운트 증가
            new_event_count = session.get("event_count", 0) + event_count
            new_observation_count = session.get("observation_count", 0) + observation_count

            response = (
                self.db.table("sessions")
                .update(
                    {
                        "event_count": new_event_count,
                        "observation_count": new_observation_count,
                    }
                )
                .eq("id", session_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"세션을 찾을 수 없습니다: {session_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="세션 카운트 업데이트 중 오류 발생",
                details=str(e),
            )

    def get_active_session(self, user_id: str) -> dict[str, Any] | None:
        """사용자의 활성 세션 조회

        Args:
            user_id: 사용자 ID

        Returns:
            활성 세션 (없으면 None)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("sessions")
                .select("*")
                .eq("user_id", user_id)
                .eq("status", "active")
                .order("start_time", desc=True)
                .limit(1)
                .execute()
            )

            return response.data[0] if response.data else None
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="활성 세션 조회 중 오류 발생",
                details=str(e),
            )
