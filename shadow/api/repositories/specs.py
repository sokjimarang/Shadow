"""명세서 Repository

agent_specs, spec_history 테이블과 상호작용
"""

from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class SpecRepository:
    """명세서 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_spec(
        self, spec_id: str, pattern_id: str, version: str, content: dict[str, Any]
    ) -> dict[str, Any]:
        """명세서 생성

        Args:
            spec_id: 명세서 ID
            pattern_id: 원본 패턴 ID
            version: 버전 (semver)
            content: 명세서 내용

        Returns:
            생성된 명세서

        Raises:
            ShadowAPIError: 생성 실패
        """
        try:
            response = (
                self.db.table("agent_specs")
                .insert(
                    {
                        "id": spec_id,
                        "pattern_id": pattern_id,
                        "version": version,
                        "status": "draft",
                        "content": content,
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="명세서 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="명세서 생성 중 오류 발생",
                details=str(e),
            )

    def get_spec(self, spec_id: str) -> dict[str, Any]:
        """명세서 조회

        Args:
            spec_id: 명세서 ID

        Returns:
            명세서 정보

        Raises:
            ShadowAPIError: 명세서 없음 또는 조회 실패
        """
        try:
            response = self.db.table("agent_specs").select("*").eq("id", spec_id).execute()

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E202,
                    message=f"명세서를 찾을 수 없습니다: {spec_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="명세서 조회 중 오류 발생",
                details=str(e),
            )

    def list_specs(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """명세서 목록 조회

        Args:
            status: 상태 필터 (None이면 전체)
            limit: 최대 개수

        Returns:
            명세서 목록

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            query = self.db.table("agent_specs").select("*")

            if status:
                query = query.eq("status", status)

            response = query.order("updated_at", desc=True).limit(limit).execute()

            return response.data or []
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="명세서 목록 조회 중 오류 발생",
                details=str(e),
            )

    def update_spec(
        self,
        spec_id: str,
        content: dict[str, Any],
        version: str | None = None,
        change_summary: str | None = None,
    ) -> dict[str, Any]:
        """명세서 업데이트

        Args:
            spec_id: 명세서 ID
            content: 새 내용
            version: 새 버전 (None이면 유지)
            change_summary: 변경 요약

        Returns:
            업데이트된 명세서

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            # 현재 명세서 조회
            current_spec = self.get_spec(spec_id)

            update_data: dict[str, Any] = {"content": content}

            if version:
                update_data["version"] = version

            response = (
                self.db.table("agent_specs")
                .update(update_data)
                .eq("id", spec_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E202,
                    message=f"명세서를 찾을 수 없습니다: {spec_id}",
                    status_code=400,
                )

            # 변경 이력 기록 (선택)
            if change_summary:
                self._create_history(
                    spec_id=spec_id,
                    previous_version=current_spec.get("version"),
                    new_version=version or current_spec.get("version"),
                    change_summary=change_summary,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="명세서 업데이트 중 오류 발생",
                details=str(e),
            )

    def update_spec_status(self, spec_id: str, status: str) -> dict[str, Any]:
        """명세서 상태 업데이트

        Args:
            spec_id: 명세서 ID
            status: 새 상태 (draft/active/archived)

        Returns:
            업데이트된 명세서

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            response = (
                self.db.table("agent_specs")
                .update({"status": status})
                .eq("id", spec_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E202,
                    message=f"명세서를 찾을 수 없습니다: {spec_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="명세서 상태 업데이트 중 오류 발생",
                details=str(e),
            )

    def _create_history(
        self, spec_id: str, previous_version: str, new_version: str, change_summary: str
    ) -> None:
        """변경 이력 기록 (내부 메서드)"""
        try:
            self.db.table("spec_history").insert(
                {
                    "spec_id": spec_id,
                    "previous_version": previous_version,
                    "version": new_version,
                    "change_type": "update",
                    "change_summary": change_summary,
                    "source": "api",
                }
            ).execute()
        except Exception:
            # 이력 기록 실패는 무시 (주 기능 아님)
            pass
