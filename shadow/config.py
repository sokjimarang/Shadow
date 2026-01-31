"""설정 관리 모듈"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Gemini API
    gemini_api_key: str = ""

    # Claude API
    anthropic_api_key: str = ""

    # Supabase (shadow-web과 동일한 DB)
    supabase_url: str = ""
    supabase_key: str = ""

    # 화면 캡처 설정
    capture_fps: int = 10  # 초당 프레임 수
    capture_monitor: int = 1  # 캡처할 모니터 번호 (1-based)

    # Gemini 분석 설정
    gemini_model: str = "gemini-2.0-flash"  # 사용할 모델
    gemini_media_resolution: str = "medium"  # low/medium/high

    # Claude 분석 설정
    claude_model: str = "claude-opus-4-5-20251101"  # Claude Opus 4.5
    claude_max_image_size: int = 1024  # 이미지 최대 크기 (토큰 절약)
    claude_use_cache: bool = True  # 프롬프트 캐싱 사용

    # 패턴 감지 설정
    pattern_min_length: int = 2  # 최소 패턴 길이
    pattern_similarity_threshold: float = 0.8  # 유사도 임계값

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# 싱글톤 설정 인스턴스
settings = Settings()
