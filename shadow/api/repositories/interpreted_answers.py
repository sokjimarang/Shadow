"""해석된 응답 Repository

interpreted_answers 테이블과 상호작용
"""

from datetime import datetime
from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class InterpretedAnswerRepository:
    """해석된 응답 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_answer(
        self,
        answer_id: str,
        action: str,
        spec_update: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """새 해석된 응답 생성

        Args:
            answer_id: 원본 응답 ID
            action: 행동 타입 (add_rule/add_exception/set_quality/reject/needs_clarification)
            spec_update: 명세서 업데이트 정보 (선택)
            confidence: 해석 확신도 (0.0~1.0)

        Returns:
            생성된 해석 결과

        Raises:
            ShadowAPIError: 생성 실패 시
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .insert(
                    {
                        "answer_id": answer_id,
                        "action": action,
                        "spec_update": spec_update,
                        "confidence": confidence,
                        "applied": False,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="해석된 응답 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="해석된 응답 생성 중 오류 발생",
                details=str(e),
            )

    def get_answer(self, interpreted_answer_id: str) -> dict[str, Any]:
        """해석된 응답 조회

        Args:
            interpreted_answer_id: 해석된 응답 ID

        Returns:
            해석된 응답 정보

        Raises:
            ShadowAPIError: 응답 없음 또는 조회 실패
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .select("*")
                .eq("id", interpreted_answer_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"해석된 응답을 찾을 수 없습니다: {interpreted_answer_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="해석된 응답 조회 중 오류 발생",
                details=str(e),
            )

    def get_answer_by_answer_id(self, answer_id: str) -> list[dict[str, Any]]:
        """원본 응답 ID로 조회

        Args:
            answer_id: 원본 응답 ID

        Returns:
            해석된 응답 목록

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .select("*")
                .eq("answer_id", answer_id)
                .order("created_at", desc=False)
                .execute()
            )

            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="원본 응답 ID로 조회 중 오류 발생",
                details=str(e),
            )

    def get_unapplied_answers(self, limit: int = 100) -> list[dict[str, Any]]:
        """미적용 응답 조회

        Args:
            limit: 최대 개수 (기본: 100)

        Returns:
            미적용 응답 목록 (생성순)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .select("*")
                .eq("applied", False)
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="미적용 응답 조회 중 오류 발생",
                details=str(e),
            )

    def get_answers_by_action(
        self, action: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """행동 타입별 조회

        Args:
            action: 행동 타입 (add_rule/add_exception/set_quality/reject/needs_clarification)
            limit: 최대 개수 (기본: 100)

        Returns:
            응답 목록 (최신순)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .select("*")
                .eq("action", action)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="행동 타입별 조회 중 오류 발생",
                details=str(e),
            )

    def mark_applied(self, interpreted_answer_id: str) -> dict[str, Any]:
        """명세서 반영 표시

        Args:
            interpreted_answer_id: 해석된 응답 ID

        Returns:
            업데이트된 응답

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .update(
                    {
                        "applied": True,
                        "applied_at": datetime.utcnow().isoformat(),
                    }
                )
                .eq("id", interpreted_answer_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"해석된 응답을 찾을 수 없습니다: {interpreted_answer_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="명세서 반영 표시 중 오류 발생",
                details=str(e),
            )

    def update_spec_update(
        self, interpreted_answer_id: str, spec_update: dict[str, Any]
    ) -> dict[str, Any]:
        """명세서 업데이트 정보 수정

        Args:
            interpreted_answer_id: 해석된 응답 ID
            spec_update: 새 명세서 업데이트 정보

        Returns:
            업데이트된 응답

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .update({"spec_update": spec_update})
                .eq("id", interpreted_answer_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"해석된 응답을 찾을 수 없습니다: {interpreted_answer_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="명세서 업데이트 정보 수정 중 오류 발생",
                details=str(e),
            )

    def update_confidence(
        self, interpreted_answer_id: str, confidence: float
    ) -> dict[str, Any]:
        """확신도 업데이트

        Args:
            interpreted_answer_id: 해석된 응답 ID
            confidence: 새 확신도 (0.0~1.0)

        Returns:
            업데이트된 응답

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .update({"confidence": confidence})
                .eq("id", interpreted_answer_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"해석된 응답을 찾을 수 없습니다: {interpreted_answer_id}",
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

    def delete_answer(self, interpreted_answer_id: str) -> None:
        """해석된 응답 삭제

        Args:
            interpreted_answer_id: 해석된 응답 ID

        Raises:
            ShadowAPIError: 삭제 실패
        """
        try:
            response = (
                self.db.table("interpreted_answers")
                .delete()
                .eq("id", interpreted_answer_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"해석된 응답을 찾을 수 없습니다: {interpreted_answer_id}",
                    status_code=400,
                )
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="해석된 응답 삭제 중 오류 발생",
                details=str(e),
            )
