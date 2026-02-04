"""Slack 클라이언트

HITL 질문을 Slack Block Kit UI로 전송합니다.
"""

import json
from typing import Any

from shadow.config import settings
from shadow.hitl.models import Question
from shadow.slack.models import SlackMessage


class SlackClient:
    """Slack API 클라이언트

    Bot Token을 사용하여 메시지를 전송합니다.
    """

    def __init__(self, bot_token: str | None = None):
        """
        Args:
            bot_token: Slack Bot Token (None이면 설정에서 가져옴)
        """
        self._bot_token = bot_token or settings.slack_bot_token
        self._client = None

        if self._bot_token:
            from slack_sdk import WebClient

            self._client = WebClient(token=self._bot_token)

    @property
    def is_configured(self) -> bool:
        """Slack이 설정되어 있는지 확인"""
        return self._client is not None

    def send_question(self, channel: str, question: Question) -> SlackMessage:
        """HITL 질문을 Slack Block Kit UI로 전송

        Args:
            channel: 전송할 채널 ID
            question: 전송할 질문

        Returns:
            전송된 메시지 정보

        Raises:
            RuntimeError: Slack이 설정되지 않은 경우
            slack_sdk.errors.SlackApiError: API 호출 실패
        """
        if not self._client:
            raise RuntimeError("Slack Bot Token이 설정되지 않았습니다.")

        blocks = self._build_question_blocks(question)

        response = self._client.chat_postMessage(
            channel=channel,
            text=question.text,  # Fallback text
            blocks=blocks,
        )

        return SlackMessage(
            channel=channel,
            ts=response["ts"],
            text=question.text,
            blocks=blocks,
            question_id=question.id,
        )

    def _build_question_blocks(self, question: Question) -> list[dict[str, Any]]:
        """질문을 Block Kit 블록으로 변환"""
        blocks = []

        # 헤더
        question_type = question.type.value if hasattr(question.type, 'value') else question.type
        blocks.append(
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤔 {question_type.upper()} 질문",
                    "emoji": True,
                },
            }
        )

        # 질문 텍스트
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": question.text,
                },
            }
        )

        # 구분선
        blocks.append({"type": "divider"})

        # 버튼 옵션들
        button_elements = []
        for option in question.options:
            button_elements.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": option.text,
                        "emoji": True,
                    },
                    "value": json.dumps(
                        {
                            "question_id": question.id,
                            "option_id": option.id,
                            "option_value": option.value,
                        }
                    ),
                    "action_id": f"hitl_answer_{option.id}",
                }
            )

        # 버튼 그룹 (최대 5개씩)
        for i in range(0, len(button_elements), 5):
            blocks.append(
                {
                    "type": "actions",
                    "elements": button_elements[i : i + 5],
                }
            )

        # 컨텍스트 (메타데이터)
        if question.source_pattern_id:
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"패턴 ID: `{question.source_pattern_id}`",
                        }
                    ],
                }
            )

        return blocks

    def send_message(self, channel: str, text: str) -> SlackMessage:
        """일반 텍스트 메시지 전송

        Args:
            channel: 전송할 채널 ID
            text: 메시지 텍스트

        Returns:
            전송된 메시지 정보
        """
        if not self._client:
            raise RuntimeError("Slack Bot Token이 설정되지 않았습니다.")

        response = self._client.chat_postMessage(
            channel=channel,
            text=text,
        )

        return SlackMessage(
            channel=channel,
            ts=response["ts"],
            text=text,
        )

    def update_message(
        self, channel: str, ts: str, text: str, blocks: list[dict[str, Any]] | None = None
    ) -> None:
        """기존 메시지 업데이트

        Args:
            channel: 채널 ID
            ts: 메시지 타임스탬프
            text: 새 텍스트
            blocks: 새 블록 (None이면 텍스트만)
        """
        if not self._client:
            raise RuntimeError("Slack Bot Token이 설정되지 않았습니다.")

        kwargs = {
            "channel": channel,
            "ts": ts,
            "text": text,
        }
        if blocks:
            kwargs["blocks"] = blocks

        self._client.chat_update(**kwargs)
