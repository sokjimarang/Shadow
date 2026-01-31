"""Slack 연동 모듈

HITL 질문을 Slack으로 전송하고 응답을 처리합니다.
"""

from shadow.slack.client import SlackClient
from shadow.slack.models import SlackMessage

__all__ = ["SlackClient", "SlackMessage"]
