"""관찰 데이터 Repository

observations, screenshots, input_events 테이블과 상호작용
"""

from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class ObservationRepository:
    """관찰 데이터 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_observation(
        self,
        session_id: str,
        observation_id: str,
        timestamp: str,
        before_screenshot_id: str,
        after_screenshot_id: str,
        event_id: str,
    ) -> dict[str, Any]:
        """관찰 데이터 생성

        Args:
            session_id: 세션 ID
            observation_id: 관찰 ID
            timestamp: 관찰 시각
            before_screenshot_id: Before 스크린샷 ID
            after_screenshot_id: After 스크린샷 ID
            event_id: 이벤트 ID

        Returns:
            생성된 관찰 데이터

        Raises:
            ShadowAPIError: 생성 실패
        """
        try:
            response = (
                self.db.table("observations")
                .insert(
                    {
                        "id": observation_id,
                        "session_id": session_id,
                        "timestamp": timestamp,
                        "before_screenshot_id": before_screenshot_id,
                        "after_screenshot_id": after_screenshot_id,
                        "event_id": event_id,
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="관찰 데이터 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="관찰 데이터 생성 중 오류 발생",
                details=str(e),
            )

    def create_screenshot(
        self,
        screenshot_id: str,
        session_id: str,
        timestamp: str,
        screenshot_type: str,
        data: str,
        thumbnail: str,
        resolution: dict[str, int],
        trigger_event_id: str,
    ) -> dict[str, Any]:
        """스크린샷 저장

        Args:
            screenshot_id: 스크린샷 ID
            session_id: 세션 ID
            timestamp: 캡처 시각
            screenshot_type: "before" | "after"
            data: 원본 이미지 (base64)
            thumbnail: 썸네일 (base64)
            resolution: 해상도 {width, height}
            trigger_event_id: 트리거된 이벤트 ID

        Returns:
            생성된 스크린샷

        Raises:
            ShadowAPIError: 생성 실패
        """
        try:
            response = (
                self.db.table("screenshots")
                .insert(
                    {
                        "id": screenshot_id,
                        "session_id": session_id,
                        "timestamp": timestamp,
                        "type": screenshot_type,
                        "data": data,
                        "thumbnail": thumbnail,
                        "resolution": resolution,
                        "trigger_event_id": trigger_event_id,
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="스크린샷 저장 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="스크린샷 저장 중 오류 발생",
                details=str(e),
            )

    def create_input_event(
        self,
        event_id: str,
        session_id: str,
        timestamp: str,
        event_type: str,
        position: dict[str, int] | None,
        button: str | None,
        active_window: dict[str, str],
    ) -> dict[str, Any]:
        """입력 이벤트 저장

        Args:
            event_id: 이벤트 ID
            session_id: 세션 ID
            timestamp: 이벤트 시각
            event_type: 이벤트 타입
            position: 마우스 위치
            button: 마우스 버튼
            active_window: 활성 윈도우 정보

        Returns:
            생성된 이벤트

        Raises:
            ShadowAPIError: 생성 실패
        """
        try:
            response = (
                self.db.table("input_events")
                .insert(
                    {
                        "id": event_id,
                        "session_id": session_id,
                        "timestamp": timestamp,
                        "type": event_type,
                        "position": position,
                        "button": button,
                        "active_window": active_window,
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="입력 이벤트 저장 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="입력 이벤트 저장 중 오류 발생",
                details=str(e),
            )

    def get_session_observations(
        self, session_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """세션의 관찰 데이터 조회

        Args:
            session_id: 세션 ID
            limit: 최대 개수

        Returns:
            관찰 데이터 목록

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("observations")
                .select("*")
                .eq("session_id", session_id)
                .order("timestamp")
                .limit(limit)
                .execute()
            )

            return response.data or []
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="관찰 데이터 조회 중 오류 발생",
                details=str(e),
            )
