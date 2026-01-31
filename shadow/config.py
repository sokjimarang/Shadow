"""설정 관리 모듈"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # Claude API
    anthropic_api_key: str = ""

    # Supabase (shadow-web과 동일한 DB)
    supabase_url: str = ""
    supabase_key: str = ""

    # Slack API
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_app_token: str = ""

    # 화면 캡처 설정
    capture_fps: int = 10  # 초당 프레임 수
    capture_monitor: int = 1  # 캡처할 모니터 번호 (1-based)

    # Claude 분석 설정
    claude_model: str = "claude-opus-4-5-20251101"  # Claude Opus 4.5
    claude_max_image_size: int = 1024  # 이미지 최대 크기 (토큰 절약)
    claude_use_cache: bool = True  # 프롬프트 캐싱 사용

    # 패턴 분석 설정 (LLM 기반)
    pattern_analyzer_backend: str = "claude"  # 패턴 분석기 백엔드
    pattern_max_patterns: int = 5  # 최대 감지 패턴 수
    pattern_max_uncertainties: int = 5  # 패턴당 최대 불확실성 수
    pattern_min_confidence: float = 0.3  # 최소 신뢰도

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# 싱글톤 설정 인스턴스
settings = Settings()
