"""HITL Repository

hitl_questions, hitl_answers 테이블과 상호작용
"""

from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class HITLRepository:
    """HITL 질문/응답 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_question(
        self,
        question_id: str,
        pattern_id: str,
        question_type: str,
        question_text: str,
        options: list[dict[str, Any]],
        allows_freetext: bool = False,
        priority: int = 3,
    ) -> dict[str, Any]:
        """HITL 질문 생성

        Args:
            question_id: 질문 ID
            pattern_id: 관련 패턴 ID
            question_type: 질문 타입 (anomaly/alternative/hypothesis/quality)
            question_text: 질문 내용
            options: 질문 옵션 목록
            allows_freetext: 자유 텍스트 허용 여부
            priority: 우선순위 (1-5)

        Returns:
            생성된 질문

        Raises:
            ShadowAPIError: 생성 실패
        """
        try:
            response = (
                self.db.table("hitl_questions")
                .insert(
                    {
                        "id": question_id,
                        "pattern_id": pattern_id,
                        "type": question_type,
                        "question_text": question_text,
                        "options": options,
                        "allows_freetext": allows_freetext,
                        "priority": priority,
                        "status": "pending",
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="HITL 질문 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="HITL 질문 생성 중 오류 발생",
                details=str(e),
            )

    def get_question(self, question_id: str) -> dict[str, Any]:
        """질문 조회

        Args:
            question_id: 질문 ID

        Returns:
            질문 정보

        Raises:
            ShadowAPIError: 질문 없음 또는 조회 실패
        """
        try:
            response = (
                self.db.table("hitl_questions").select("*").eq("id", question_id).execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E203,
                    message=f"질문을 찾을 수 없습니다: {question_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="질문 조회 중 오류 발생",
                details=str(e),
            )

    def get_pending_questions(self, limit: int = 10) -> list[dict[str, Any]]:
        """대기 중인 질문 목록 조회

        Args:
            limit: 최대 개수

        Returns:
            질문 목록

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("hitl_questions")
                .select("*")
                .eq("status", "pending")
                .order("priority", desc=True)
                .order("created_at")
                .limit(limit)
                .execute()
            )

            return response.data or []
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="질문 목록 조회 중 오류 발생",
                details=str(e),
            )

    def update_question_status(
        self, question_id: str, status: str, slack_message_ts: str | None = None
    ) -> dict[str, Any]:
        """질문 상태 업데이트

        Args:
            question_id: 질문 ID
            status: 새 상태 (pending/sent/answered/expired)
            slack_message_ts: Slack 메시지 타임스탬프 (sent 시 필요)

        Returns:
            업데이트된 질문

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            update_data: dict[str, Any] = {"status": status}

            if status == "sent" and slack_message_ts:
                update_data["slack_message_ts"] = slack_message_ts
                update_data["sent_at"] = "now()"
            elif status == "answered":
                update_data["answered_at"] = "now()"

            response = (
                self.db.table("hitl_questions")
                .update(update_data)
                .eq("id", question_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E203,
                    message=f"질문을 찾을 수 없습니다: {question_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="질문 상태 업데이트 중 오류 발생",
                details=str(e),
            )

    def create_answer(
        self,
        answer_id: str,
        question_id: str,
        user_id: str,
        response_type: str,
        selected_option_id: str | None,
        freetext: str | None,
    ) -> dict[str, Any]:
        """HITL 응답 저장

        Args:
            answer_id: 응답 ID
            question_id: 질문 ID
            user_id: 사용자 ID
            response_type: 응답 타입 (button/freetext)
            selected_option_id: 선택된 옵션 ID
            freetext: 자유 텍스트 응답

        Returns:
            생성된 응답

        Raises:
            ShadowAPIError: 생성 실패
        """
        try:
            response = (
                self.db.table("hitl_answers")
                .insert(
                    {
                        "id": answer_id,
                        "question_id": question_id,
                        "user_id": user_id,
                        "response_type": response_type,
                        "selected_option_id": selected_option_id,
                        "freetext": freetext,
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="HITL 응답 저장 실패",
                )

            # 질문 상태를 answered로 업데이트
            self.update_question_status(question_id, "answered")

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="HITL 응답 저장 중 오류 발생",
                details=str(e),
            )
