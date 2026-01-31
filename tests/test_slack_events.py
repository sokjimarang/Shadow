"""Slack 이벤트 수신 엔드포인트 테스트"""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def signing_secret():
    """테스트용 Signing Secret"""
    return "test_signing_secret_12345"


@pytest.fixture
def slack_headers(signing_secret):
    """Slack 요청 헤더 생성 헬퍼"""

    def _create_headers(body: str | bytes) -> dict[str, str]:
        """Valid Slack headers 생성"""
        if isinstance(body, str):
            body = body.encode()

        timestamp = str(int(time.time()))

        # Signature 생성
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        signature = (
            "v0="
            + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        return {
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/json",
        }

    return _create_headers


@pytest.mark.asyncio
class TestSlackEvents:
    """Slack Events API 테스트"""

    async def test_url_verification(self, slack_headers, monkeypatch):
        """URL Verification 요청은 challenge를 반환"""
        # settings.slack_signing_secret 직접 설정
        from shadow.config import settings

        monkeypatch.setattr(settings, "slack_signing_secret", "test_signing_secret_12345")

        payload = {"type": "url_verification", "challenge": "test_challenge_string"}

        body = json.dumps(payload)
        headers = slack_headers(body)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/slack/events", content=body, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["challenge"] == "test_challenge_string"

    async def test_message_event(self, slack_headers, monkeypatch):
        """메시지 이벤트 수신 테스트"""
        from shadow.config import settings

        monkeypatch.setattr(settings, "slack_signing_secret", "test_signing_secret_12345")

        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "user": "U1234567890",
                "text": "현재 상태",
                "channel": "D1234567890",
                "ts": "1234567890.123456",
            },
        }

        body = json.dumps(payload)
        headers = slack_headers(body)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/slack/events", content=body, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    async def test_invalid_signature_rejected(self, monkeypatch):
        """잘못된 signature는 거부"""
        from shadow.config import settings

        monkeypatch.setattr(settings, "slack_signing_secret", "test_signing_secret_12345")

        payload = {"type": "event_callback", "event": {"type": "message"}}
        body = json.dumps(payload)

        # 잘못된 signature
        headers = {
            "X-Slack-Request-Timestamp": str(int(time.time())),
            "X-Slack-Signature": "v0=invalid_signature",
            "Content-Type": "application/json",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/slack/events", content=body, headers=headers)

        assert response.status_code == 401

    async def test_expired_timestamp_rejected(self, slack_headers, monkeypatch):
        """만료된 timestamp는 거부"""
        from shadow.config import settings

        monkeypatch.setattr(settings, "slack_signing_secret", "test_signing_secret_12345")

        payload = {"type": "event_callback"}
        body = json.dumps(payload)

        # 만료된 timestamp (10분 전)
        old_timestamp = str(int(time.time()) - 600)
        sig_basestring = f"v0:{old_timestamp}:{body}"
        signature = (
            "v0="
            + hmac.new(
                b"test_signing_secret_12345",
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        headers = {
            "X-Slack-Request-Timestamp": old_timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/json",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/slack/events", content=body, headers=headers)

        assert response.status_code == 401


@pytest.mark.asyncio
class TestSlackInteractivity:
    """Slack Interactive Components 테스트"""

    async def test_button_click_event(self, signing_secret, monkeypatch):
        """버튼 클릭 이벤트 파싱 테스트"""
        from shadow.config import settings

        monkeypatch.setattr(settings, "slack_signing_secret", signing_secret)

        # Slack Interactive payload
        payload = {
            "type": "block_actions",
            "user": {"id": "U1234567890"},
            "actions": [
                {
                    "action_id": "hitl_answer_yes",
                    "block_id": "question_001",
                    "value": json.dumps(
                        {
                            "question_id": "q123",
                            "option_id": "opt_yes",
                            "option_value": "confirm",
                        }
                    ),
                }
            ],
            "message": {"ts": "1234567890.123456"},
        }

        # Form-encoded payload (Slack이 보내는 형식)
        form_data = urlencode({"payload": json.dumps(payload)})
        body_bytes = form_data.encode()

        # Signature 생성
        timestamp = str(int(time.time()))
        sig_basestring = f"v0:{timestamp}:{form_data}"
        signature = (
            "v0="
            + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        headers = {
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/slack/interactivity", content=body_bytes, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True

    async def test_missing_payload_rejected(self, signing_secret, monkeypatch):
        """payload가 없는 요청은 거부"""
        from shadow.config import settings

        monkeypatch.setattr(settings, "slack_signing_secret", signing_secret)

        # payload 대신 다른 필드를 전송 (payload는 없음)
        form_data = urlencode({"other_field": "value"})
        body_bytes = form_data.encode()

        timestamp = str(int(time.time()))
        sig_basestring = f"v0:{timestamp}:{form_data}"
        signature = (
            "v0="
            + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        headers = {
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/slack/interactivity", content=body_bytes, headers=headers)

        assert response.status_code == 400
