"""세션 시퀀스 Repository

session_sequences 테이블과 상호작용
"""

from datetime import datetime
from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class SessionSequenceRepository:
    """세션 시퀀스 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_sequence(
        self,
        session_id: str,
        start_time: datetime,
        action_ids: list[str] | None = None,
        apps_used: list[str] | None = None,
    ) -> dict[str, Any]:
        """새 세션 시퀀스 생성

        Args:
            session_id: 세션 ID
            start_time: 시작 시각
            action_ids: 행동 ID 목록 (선택)
            apps_used: 사용된 앱 목록 (선택)

        Returns:
            생성된 시퀀스

        Raises:
            ShadowAPIError: 생성 실패 시
        """
        try:
            action_ids = action_ids or []
            apps_used = apps_used or []

            response = (
                self.db.table("session_sequences")
                .insert(
                    {
                        "session_id": session_id,
                        "start_time": start_time.isoformat(),
                        "action_ids": action_ids,
                        "apps_used": apps_used,
                        "action_count": len(action_ids),
                        "status": "recording",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="시퀀스 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="시퀀스 생성 중 오류 발생",
                details=str(e),
            )

    def get_sequence(self, sequence_id: str) -> dict[str, Any]:
        """시퀀스 조회

        Args:
            sequence_id: 시퀀스 ID

        Returns:
            시퀀스 정보

        Raises:
            ShadowAPIError: 시퀀스 없음 또는 조회 실패
        """
        try:
            response = (
                self.db.table("session_sequences").select("*").eq("id", sequence_id).execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"시퀀스를 찾을 수 없습니다: {sequence_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="시퀀스 조회 중 오류 발생",
                details=str(e),
            )

    def get_sequences_by_session(self, session_id: str) -> list[dict[str, Any]]:
        """세션의 모든 시퀀스 조회

        Args:
            session_id: 세션 ID

        Returns:
            시퀀스 목록 (시작 시간순)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("session_sequences")
                .select("*")
                .eq("session_id", session_id)
                .order("start_time", desc=False)
                .execute()
            )

            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="세션 시퀀스 조회 중 오류 발생",
                details=str(e),
            )

    def get_active_sequence(self, session_id: str) -> dict[str, Any] | None:
        """세션의 활성 시퀀스 조회

        Args:
            session_id: 세션 ID

        Returns:
            활성 시퀀스 (없으면 None)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("session_sequences")
                .select("*")
                .eq("session_id", session_id)
                .eq("status", "recording")
                .order("start_time", desc=True)
                .limit(1)
                .execute()
            )

            return response.data[0] if response.data else None
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="활성 시퀀스 조회 중 오류 발생",
                details=str(e),
            )

    def add_action(self, sequence_id: str, action_id: str, app: str) -> dict[str, Any]:
        """시퀀스에 행동 추가

        Args:
            sequence_id: 시퀀스 ID
            action_id: 추가할 행동 ID
            app: 앱 이름

        Returns:
            업데이트된 시퀀스

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            sequence = self.get_sequence(sequence_id)
            action_ids = sequence.get("action_ids", [])
            apps_used = sequence.get("apps_used", [])

            action_ids.append(action_id)
            if app not in apps_used:
                apps_used.append(app)

            return self._update_sequence(
                sequence_id,
                action_ids=action_ids,
                apps_used=apps_used,
                action_count=len(action_ids),
            )
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="행동 추가 중 오류 발생",
                details=str(e),
            )

    def complete_sequence(
        self, sequence_id: str, end_time: datetime | None = None
    ) -> dict[str, Any]:
        """시퀀스 완료

        Args:
            sequence_id: 시퀀스 ID
            end_time: 종료 시각 (선택)

        Returns:
            업데이트된 시퀀스

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            return self._update_sequence(
                sequence_id,
                end_time=(end_time or datetime.utcnow()).isoformat(),
                status="completed",
            )
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="시퀀스 완료 중 오류 발생",
                details=str(e),
            )

    def mark_analyzed(self, sequence_id: str) -> dict[str, Any]:
        """시퀀스 분석 완료 표시

        Args:
            sequence_id: 시퀀스 ID

        Returns:
            업데이트된 시퀀스

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            return self._update_sequence(sequence_id, status="analyzed")
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="분석 완료 표시 중 오류 발생",
                details=str(e),
            )

    def get_sequences_by_status(
        self, status: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """상태별 시퀀스 조회

        Args:
            status: 상태 (recording/completed/analyzed)
            limit: 최대 개수 (기본: 100)

        Returns:
            시퀀스 목록 (최신순)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("session_sequences")
                .select("*")
                .eq("status", status)
                .order("start_time", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="상태별 시퀀스 조회 중 오류 발생",
                details=str(e),
            )

    def delete_sequence(self, sequence_id: str) -> None:
        """시퀀스 삭제

        Args:
            sequence_id: 시퀀스 ID

        Raises:
            ShadowAPIError: 삭제 실패
        """
        try:
            response = (
                self.db.table("session_sequences").delete().eq("id", sequence_id).execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"시퀀스를 찾을 수 없습니다: {sequence_id}",
                    status_code=400,
                )
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="시퀀스 삭제 중 오류 발생",
                details=str(e),
            )

    def _update_sequence(self, sequence_id: str, **updates: Any) -> dict[str, Any]:
        """시퀀스 업데이트 (내부 메서드)

        Args:
            sequence_id: 시퀀스 ID
            **updates: 업데이트할 필드들

        Returns:
            업데이트된 시퀀스

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            update_data = {**updates, "updated_at": datetime.utcnow().isoformat()}

            response = (
                self.db.table("session_sequences")
                .update(update_data)
                .eq("id", sequence_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"시퀀스를 찾을 수 없습니다: {sequence_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="시퀀스 업데이트 중 오류 발생",
                details=str(e),
            )
