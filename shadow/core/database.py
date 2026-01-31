"""Supabase 데이터베이스 연결 모듈"""

from typing import Any

from supabase import Client, create_client

from shadow.config import settings


class Database:
    """Supabase 데이터베이스 클라이언트 래퍼"""

    _instance: Client | None = None

    @classmethod
    def get_client(cls) -> Client:
        """Supabase 클라이언트 인스턴스 반환 (싱글톤)

        Returns:
            Supabase 클라이언트

        Raises:
            RuntimeError: Supabase 설정이 없는 경우
        """
        if cls._instance is None:
            if not settings.supabase_url or not settings.supabase_key:
                raise RuntimeError(
                    "Supabase 설정이 필요합니다. SUPABASE_URL과 SUPABASE_KEY를 .env에 설정하세요."
                )

            cls._instance = create_client(settings.supabase_url, settings.supabase_key)

        return cls._instance

    @classmethod
    def is_configured(cls) -> bool:
        """Supabase가 설정되어 있는지 확인"""
        return bool(settings.supabase_url and settings.supabase_key)

    @classmethod
    async def test_connection(cls) -> dict[str, Any]:
        """데이터베이스 연결 테스트

        Returns:
            연결 상태 정보

        Raises:
            Exception: 연결 실패 시
        """
        if not cls.is_configured():
            return {
                "status": "not_configured",
                "message": "Supabase 설정이 없습니다",
            }

        try:
            client = cls.get_client()
            # 간단한 쿼리로 연결 테스트 (users 테이블이 있다고 가정)
            response = client.table("users").select("id").limit(1).execute()

            return {
                "status": "connected",
                "message": "Supabase 연결 성공",
                "url": settings.supabase_url,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Supabase 연결 실패: {str(e)}",
            }


# 편의 함수
def get_db() -> Client:
    """데이터베이스 클라이언트 가져오기 (의존성 주입용)"""
    return Database.get_client()
