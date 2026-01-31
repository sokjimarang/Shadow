"""Slack 메시지 모델"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SlackMessage:
    """Slack 메시지 정보

    Attributes:
        channel: 채널 ID
        ts: 메시지 타임스탬프 (메시지 고유 ID)
        text: 메시지 텍스트
        blocks: Block Kit 블록 목록
        question_id: 연결된 HITL 질문 ID
        sent_at: 전송 시각
    """

    channel: str
    ts: str
    text: str = ""
    blocks: list[dict[str, Any]] = field(default_factory=list)
    question_id: str | None = None
    sent_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "ts": self.ts,
            "text": self.text,
            "blocks": self.blocks,
            "question_id": self.question_id,
            "sent_at": self.sent_at.isoformat(),
        }
