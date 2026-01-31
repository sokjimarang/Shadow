"""Slack 요청 검증 유틸리티

Slack에서 오는 요청의 진위를 검증합니다.
- Signature 검증 (HMAC-SHA256)
- Timestamp 검증 (Replay attack 방지)
"""

import hashlib
import hmac
import time


def verify_slack_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    signing_secret: str,
) -> bool:
    """Slack request signature 검증

    Slack은 요청에 X-Slack-Signature 헤더를 포함하여 전송합니다.
    이 시그니처는 HMAC-SHA256으로 생성되며, 다음을 검증합니다:
    1. 요청이 Slack에서 왔는지
    2. 요청 내용이 변조되지 않았는지

    Args:
        body: 요청 바디 (bytes)
        timestamp: X-Slack-Request-Timestamp 헤더
        signature: X-Slack-Signature 헤더
        signing_secret: Slack App의 Signing Secret

    Returns:
        검증 통과 여부

    References:
        https://api.slack.com/authentication/verifying-requests-from-slack
    """
    if not all([body, timestamp, signature, signing_secret]):
        return False

    # Slack signature format: v0=<hash>
    if not signature.startswith("v0="):
        return False

    # 베이스 문자열 생성: "v0:{timestamp}:{body}"
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"

    # HMAC-SHA256 해시 계산
    my_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256,
        ).hexdigest()
    )

    # Timing attack 방지를 위한 constant-time 비교
    return hmac.compare_digest(my_signature, signature)


def is_request_expired(timestamp: str, max_age: int = 300) -> bool:
    """요청 timestamp 검증 (Replay attack 방지)

    Slack 요청의 timestamp가 현재 시각과 너무 차이 나면 거부합니다.
    기본값은 5분 (300초)입니다.

    Args:
        timestamp: X-Slack-Request-Timestamp 헤더 (Unix timestamp 문자열)
        max_age: 최대 허용 시간 차이 (초, 기본 300초)

    Returns:
        만료 여부 (True이면 만료됨)
    """
    try:
        request_time = int(timestamp)
    except (ValueError, TypeError):
        return True  # 잘못된 timestamp는 만료로 간주

    current_time = int(time.time())
    time_diff = abs(current_time - request_time)

    return time_diff > max_age
