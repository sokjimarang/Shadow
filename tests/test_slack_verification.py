"""Slack 요청 검증 로직 테스트"""

import hashlib
import hmac
import time

import pytest

from shadow.slack.verification import is_request_expired, verify_slack_signature


class TestVerifySlackSignature:
    """Slack signature 검증 테스트"""

    def test_valid_signature(self):
        """올바른 signature는 검증 통과"""
        signing_secret = "test_secret_key_12345"
        timestamp = "1234567890"
        body = b'{"type":"url_verification","challenge":"test_challenge"}'

        # 올바른 signature 생성
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        valid_signature = (
            "v0="
            + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        result = verify_slack_signature(body, timestamp, valid_signature, signing_secret)
        assert result is True

    def test_invalid_signature(self):
        """잘못된 signature는 검증 실패"""
        signing_secret = "test_secret_key_12345"
        timestamp = "1234567890"
        body = b'{"type":"url_verification"}'
        invalid_signature = "v0=wrong_signature_hash"

        result = verify_slack_signature(body, timestamp, invalid_signature, signing_secret)
        assert result is False

    def test_wrong_signing_secret(self):
        """다른 signing secret으로 생성된 signature는 실패"""
        correct_secret = "correct_secret"
        wrong_secret = "wrong_secret"
        timestamp = "1234567890"
        body = b'{"type":"event"}'

        # 잘못된 secret으로 signature 생성
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        signature = (
            "v0="
            + hmac.new(
                wrong_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        result = verify_slack_signature(body, timestamp, signature, correct_secret)
        assert result is False

    def test_modified_body(self):
        """body가 변조된 경우 검증 실패"""
        signing_secret = "test_secret"
        timestamp = "1234567890"
        original_body = b'{"type":"event","value":"original"}'
        modified_body = b'{"type":"event","value":"modified"}'

        # 원본 body로 signature 생성
        sig_basestring = f"v0:{timestamp}:{original_body.decode('utf-8')}"
        signature = (
            "v0="
            + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        # 변조된 body로 검증 시도
        result = verify_slack_signature(modified_body, timestamp, signature, signing_secret)
        assert result is False

    def test_missing_v0_prefix(self):
        """v0= prefix가 없는 signature는 실패"""
        signing_secret = "test_secret"
        timestamp = "1234567890"
        body = b'{"type":"event"}'
        signature_without_prefix = "abc123def456"  # v0= 없음

        result = verify_slack_signature(body, timestamp, signature_without_prefix, signing_secret)
        assert result is False

    def test_empty_parameters(self):
        """빈 파라미터는 검증 실패"""
        assert verify_slack_signature(b"", "123", "v0=sig", "secret") is False
        assert verify_slack_signature(b"body", "", "v0=sig", "secret") is False
        assert verify_slack_signature(b"body", "123", "", "secret") is False
        assert verify_slack_signature(b"body", "123", "v0=sig", "") is False


class TestIsRequestExpired:
    """Timestamp 검증 테스트"""

    def test_recent_timestamp_not_expired(self):
        """최근 timestamp는 만료되지 않음"""
        current_time = int(time.time())
        recent_timestamp = str(current_time - 60)  # 1분 전

        result = is_request_expired(recent_timestamp, max_age=300)
        assert result is False

    def test_old_timestamp_expired(self):
        """오래된 timestamp는 만료됨"""
        current_time = int(time.time())
        old_timestamp = str(current_time - 600)  # 10분 전

        result = is_request_expired(old_timestamp, max_age=300)
        assert result is True

    def test_future_timestamp_expired(self):
        """미래 timestamp도 만료 처리 (시간 차이가 max_age 초과)"""
        current_time = int(time.time())
        future_timestamp = str(current_time + 600)  # 10분 후

        result = is_request_expired(future_timestamp, max_age=300)
        assert result is True

    def test_exact_max_age_not_expired(self):
        """정확히 max_age와 같은 시간 차이는 만료되지 않음"""
        current_time = int(time.time())
        timestamp = str(current_time - 300)  # 정확히 300초 전

        result = is_request_expired(timestamp, max_age=300)
        assert result is False

    def test_invalid_timestamp_format(self):
        """잘못된 timestamp 형식은 만료로 간주"""
        assert is_request_expired("not_a_number") is True
        assert is_request_expired("12.34") is True  # float는 거부
        assert is_request_expired("") is True

    def test_custom_max_age(self):
        """커스텀 max_age 설정 테스트"""
        current_time = int(time.time())
        timestamp = str(current_time - 100)  # 100초 전

        # 60초 max_age → 만료됨
        assert is_request_expired(timestamp, max_age=60) is True

        # 120초 max_age → 만료 안됨
        assert is_request_expired(timestamp, max_age=120) is False
