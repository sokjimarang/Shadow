"""라벨링된 행동 Repository

labeled_actions 테이블과 상호작용
"""

from datetime import datetime
from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class LabeledActionRepository:
    """라벨링된 행동 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_action(
        self,
        observation_id: str,
        session_id: str,
        timestamp: datetime,
        action_type: str,
        target_element: str,
        app: str,
        semantic_label: str,
        app_context: str | None = None,
        intent_guess: str | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """새 라벨링된 행동 생성

        Args:
            observation_id: 원본 관찰 ID
            session_id: 세션 ID
            timestamp: 행동 발생 시각
            action_type: 행동 타입 (click, type 등)
            target_element: 대상 UI 요소
            app: 앱 이름
            semantic_label: 행동 설명
            app_context: 앱 내 컨텍스트 (선택)
            intent_guess: 의도 추측 (선택)
            confidence: 확신도 (0.0~1.0)

        Returns:
            생성된 행동

        Raises:
            ShadowAPIError: 생성 실패 시
        """
        try:
            response = (
                self.db.table("labeled_actions")
                .insert(
                    {
                        "observation_id": observation_id,
                        "session_id": session_id,
                        "timestamp": timestamp.isoformat(),
                        "action_type": action_type,
                        "target_element": target_element,
                        "app": app,
                        "app_context": app_context,
                        "semantic_label": semantic_label,
                        "intent_guess": intent_guess,
                        "confidence": confidence,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="행동 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="행동 생성 중 오류 발생",
                details=str(e),
            )

    def get_action(self, action_id: str) -> dict[str, Any]:
        """행동 조회

        Args:
            action_id: 행동 ID

        Returns:
            행동 정보

        Raises:
            ShadowAPIError: 행동 없음 또는 조회 실패
        """
        try:
            response = (
                self.db.table("labeled_actions").select("*").eq("id", action_id).execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"행동을 찾을 수 없습니다: {action_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="행동 조회 중 오류 발생",
                details=str(e),
            )

    def get_actions_by_session(
        self, session_id: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """세션의 모든 행동 조회

        Args:
            session_id: 세션 ID
            limit: 최대 개수 (선택)

        Returns:
            행동 목록 (시간순 정렬)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            query = (
                self.db.table("labeled_actions")
                .select("*")
                .eq("session_id", session_id)
                .order("timestamp", desc=False)
            )

            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="세션 행동 조회 중 오류 발생",
                details=str(e),
            )

    def get_actions_by_observation(self, observation_id: str) -> dict[str, Any] | None:
        """관찰의 행동 조회

        Args:
            observation_id: 관찰 ID

        Returns:
            행동 정보 (없으면 None)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("labeled_actions")
                .select("*")
                .eq("observation_id", observation_id)
                .execute()
            )

            return response.data[0] if response.data else None
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="관찰 행동 조회 중 오류 발생",
                details=str(e),
            )

    def get_actions_by_app(self, app: str, limit: int = 100) -> list[dict[str, Any]]:
        """앱별 행동 조회

        Args:
            app: 앱 이름
            limit: 최대 개수 (기본: 100)

        Returns:
            행동 목록 (최신순)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("labeled_actions")
                .select("*")
                .eq("app", app)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="앱 행동 조회 중 오류 발생",
                details=str(e),
            )

    def get_actions_by_type(
        self, action_type: str, session_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """행동 타입별 조회

        Args:
            action_type: 행동 타입 (click, type 등)
            session_id: 세션 ID (선택)
            limit: 최대 개수 (기본: 100)

        Returns:
            행동 목록 (최신순)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            query = (
                self.db.table("labeled_actions")
                .select("*")
                .eq("action_type", action_type)
                .order("timestamp", desc=True)
                .limit(limit)
            )

            if session_id:
                query = query.eq("session_id", session_id)

            response = query.execute()
            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="행동 타입 조회 중 오류 발생",
                details=str(e),
            )

    def update_confidence(self, action_id: str, confidence: float) -> dict[str, Any]:
        """확신도 업데이트

        Args:
            action_id: 행동 ID
            confidence: 새 확신도 (0.0~1.0)

        Returns:
            업데이트된 행동

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            response = (
                self.db.table("labeled_actions")
                .update({"confidence": confidence})
                .eq("id", action_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"행동을 찾을 수 없습니다: {action_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="확신도 업데이트 중 오류 발생",
                details=str(e),
            )

    def update_intent(self, action_id: str, intent_guess: str) -> dict[str, Any]:
        """의도 추측 업데이트

        Args:
            action_id: 행동 ID
            intent_guess: 새 의도 추측

        Returns:
            업데이트된 행동

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            response = (
                self.db.table("labeled_actions")
                .update({"intent_guess": intent_guess})
                .eq("id", action_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"행동을 찾을 수 없습니다: {action_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="의도 업데이트 중 오류 발생",
                details=str(e),
            )

    def delete_action(self, action_id: str) -> None:
        """행동 삭제

        Args:
            action_id: 행동 ID

        Raises:
            ShadowAPIError: 삭제 실패
        """
        try:
            response = self.db.table("labeled_actions").delete().eq("id", action_id).execute()

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"행동을 찾을 수 없습니다: {action_id}",
                    status_code=400,
                )
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="행동 삭제 중 오류 발생",
                details=str(e),
            )
