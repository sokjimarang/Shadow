"""Core 모듈

데이터베이스 연결 등 핵심 기능을 제공합니다.
"""

from shadow.core.database import Database, get_db

__all__ = ["Database", "get_db"]
