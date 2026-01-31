"""감지된 패턴 Repository

detected_patterns 테이블과 상호작용
"""

from datetime import datetime
from typing import Any

from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.core.database import get_db


class DetectedPatternRepository:
    """감지된 패턴 CRUD"""

    def __init__(self, db: Client | None = None):
        self.db = db or get_db()

    def create_pattern(
        self,
        core_sequence: list[dict[str, Any]],
        apps_involved: list[str],
        occurrences: int = 1,
        pattern_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        session_ids: list[str] | None = None,
        variations: list[dict[str, Any]] | None = None,
        uncertainties: list[dict[str, Any]] | None = None,
        confidence: float = 1.0,
    ) -> dict[str, Any]:
        """새 패턴 생성

        Args:
            core_sequence: 핵심 행동 시퀀스
            apps_involved: 사용된 앱 목록
            occurrences: 발생 횟수
            pattern_id: 패턴 ID (선택)
            name: 패턴 이름 (선택)
            description: 패턴 설명 (선택)
            session_ids: 세션 ID 목록 (선택)
            variations: 변형 목록 (선택)
            uncertainties: 불확실성 목록 (선택)
            confidence: 확신도 (0.0~1.0)

        Returns:
            생성된 패턴

        Raises:
            ShadowAPIError: 생성 실패 시
        """
        try:
            now = datetime.utcnow().isoformat()

            response = (
                self.db.table("detected_patterns")
                .insert(
                    {
                        "pattern_id": pattern_id,
                        "name": name,
                        "description": description,
                        "core_sequence": core_sequence,
                        "apps_involved": apps_involved,
                        "occurrences": occurrences,
                        "first_seen": now,
                        "last_seen": now,
                        "session_ids": session_ids or [],
                        "variations": variations or [],
                        "uncertainties": uncertainties or [],
                        "status": "detected",
                        "confidence": confidence,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E001,
                    message="패턴 생성 실패",
                )

            return response.data[0]
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="패턴 생성 중 오류 발생",
                details=str(e),
            )

    def get_pattern(self, pattern_db_id: str) -> dict[str, Any]:
        """패턴 조회 (DB ID로)

        Args:
            pattern_db_id: 패턴 DB ID

        Returns:
            패턴 정보

        Raises:
            ShadowAPIError: 패턴 없음 또는 조회 실패
        """
        try:
            response = (
                self.db.table("detected_patterns")
                .select("*")
                .eq("id", pattern_db_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"패턴을 찾을 수 없습니다: {pattern_db_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="패턴 조회 중 오류 발생",
                details=str(e),
            )

    def get_pattern_by_pattern_id(self, pattern_id: str) -> dict[str, Any] | None:
        """패턴 조회 (pattern_id로)

        Args:
            pattern_id: 패턴 ID

        Returns:
            패턴 정보 (없으면 None)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("detected_patterns")
                .select("*")
                .eq("pattern_id", pattern_id)
                .execute()
            )

            return response.data[0] if response.data else None
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="패턴 조회 중 오류 발생",
                details=str(e),
            )

    def get_patterns_by_status(
        self, status: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """상태별 패턴 조회

        Args:
            status: 상태 (detected/confirming/confirmed/rejected)
            limit: 최대 개수 (기본: 100)

        Returns:
            패턴 목록 (최신순)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("detected_patterns")
                .select("*")
                .eq("status", status)
                .order("first_seen", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="상태별 패턴 조회 중 오류 발생",
                details=str(e),
            )

    def get_patterns_by_app(self, app: str, limit: int = 100) -> list[dict[str, Any]]:
        """앱별 패턴 조회

        Args:
            app: 앱 이름
            limit: 최대 개수 (기본: 100)

        Returns:
            패턴 목록 (발생 횟수순)

        Raises:
            ShadowAPIError: 조회 실패
        """
        try:
            response = (
                self.db.table("detected_patterns")
                .select("*")
                .contains("apps_involved", [app])
                .order("occurrences", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="앱별 패턴 조회 중 오류 발생",
                details=str(e),
            )

    def increment_occurrence(
        self, pattern_db_id: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """발생 횟수 증가

        Args:
            pattern_db_id: 패턴 DB ID
            session_id: 세션 ID (선택)

        Returns:
            업데이트된 패턴

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            pattern = self.get_pattern(pattern_db_id)
            new_occurrences = pattern.get("occurrences", 0) + 1
            session_ids = pattern.get("session_ids", [])

            if session_id and session_id not in session_ids:
                session_ids.append(session_id)

            return self._update_pattern(
                pattern_db_id,
                occurrences=new_occurrences,
                session_ids=session_ids,
                last_seen=datetime.utcnow().isoformat(),
            )
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="발생 횟수 증가 중 오류 발생",
                details=str(e),
            )

    def add_variation(
        self, pattern_db_id: str, variation: dict[str, Any]
    ) -> dict[str, Any]:
        """변형 추가

        Args:
            pattern_db_id: 패턴 DB ID
            variation: 변형 정보

        Returns:
            업데이트된 패턴

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            pattern = self.get_pattern(pattern_db_id)
            variations = pattern.get("variations", [])
            variations.append(variation)

            return self._update_pattern(pattern_db_id, variations=variations)
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="변형 추가 중 오류 발생",
                details=str(e),
            )

    def add_uncertainty(
        self, pattern_db_id: str, uncertainty: dict[str, Any]
    ) -> dict[str, Any]:
        """불확실성 추가

        Args:
            pattern_db_id: 패턴 DB ID
            uncertainty: 불확실성 정보

        Returns:
            업데이트된 패턴

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            pattern = self.get_pattern(pattern_db_id)
            uncertainties = pattern.get("uncertainties", [])
            uncertainties.append(uncertainty)

            return self._update_pattern(pattern_db_id, uncertainties=uncertainties)
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="불확실성 추가 중 오류 발생",
                details=str(e),
            )

    def update_status(self, pattern_db_id: str, status: str) -> dict[str, Any]:
        """상태 업데이트

        Args:
            pattern_db_id: 패턴 DB ID
            status: 새 상태 (detected/confirming/confirmed/rejected)

        Returns:
            업데이트된 패턴

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            return self._update_pattern(pattern_db_id, status=status)
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="상태 업데이트 중 오류 발생",
                details=str(e),
            )

    def update_metadata(
        self,
        pattern_db_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """메타데이터 업데이트

        Args:
            pattern_db_id: 패턴 DB ID
            name: 패턴 이름 (선택)
            description: 패턴 설명 (선택)

        Returns:
            업데이트된 패턴

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            updates = {}
            if name is not None:
                updates["name"] = name
            if description is not None:
                updates["description"] = description

            return self._update_pattern(pattern_db_id, **updates)
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="메타데이터 업데이트 중 오류 발생",
                details=str(e),
            )

    def link_spec(self, pattern_db_id: str, spec_id: str) -> dict[str, Any]:
        """명세서 연결

        Args:
            pattern_db_id: 패턴 DB ID
            spec_id: 명세서 ID

        Returns:
            업데이트된 패턴

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            return self._update_pattern(pattern_db_id, spec_id=spec_id)
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="명세서 연결 중 오류 발생",
                details=str(e),
            )

    def delete_pattern(self, pattern_db_id: str) -> None:
        """패턴 삭제

        Args:
            pattern_db_id: 패턴 DB ID

        Raises:
            ShadowAPIError: 삭제 실패
        """
        try:
            response = (
                self.db.table("detected_patterns")
                .delete()
                .eq("id", pattern_db_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"패턴을 찾을 수 없습니다: {pattern_db_id}",
                    status_code=400,
                )
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="패턴 삭제 중 오류 발생",
                details=str(e),
            )

    def _update_pattern(self, pattern_db_id: str, **updates: Any) -> dict[str, Any]:
        """패턴 업데이트 (내부 메서드)

        Args:
            pattern_db_id: 패턴 DB ID
            **updates: 업데이트할 필드들

        Returns:
            업데이트된 패턴

        Raises:
            ShadowAPIError: 업데이트 실패
        """
        try:
            update_data = {**updates, "updated_at": datetime.utcnow().isoformat()}

            response = (
                self.db.table("detected_patterns")
                .update(update_data)
                .eq("id", pattern_db_id)
                .execute()
            )

            if not response.data:
                raise ShadowAPIError(
                    error_code=ErrorCode.E201,
                    message=f"패턴을 찾을 수 없습니다: {pattern_db_id}",
                    status_code=400,
                )

            return response.data[0]
        except ShadowAPIError:
            raise
        except Exception as e:
            raise ShadowAPIError(
                error_code=ErrorCode.E001,
                message="패턴 업데이트 중 오류 발생",
                details=str(e),
            )
