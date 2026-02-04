"""Slack 봇 질문 전송 테스트

HITL 질문을 Slack 채널에 전송하는 테스트 스크립트입니다.
"""

import asyncio

from shadow.config import settings
from shadow.hitl.models import Question, QuestionOption, QuestionType
from shadow.slack.client import SlackClient


async def main():
    """Slack 봇 테스트 실행"""
    # 환경 변수 강제 재로드
    import os
    from dotenv import load_dotenv
    load_dotenv(override=True)

    # Slack 클라이언트 생성
    client = SlackClient()

    if not client.is_configured:
        print("❌ Slack Bot Token이 설정되지 않았습니다.")
        print("   .env 파일에 SLACK_BOT_TOKEN을 설정해주세요.")
        return

    # 테스트 채널 ID (환경 변수 직접 읽기)
    channel = os.getenv("SLACK_DEFAULT_CHANNEL", settings.slack_default_channel)

    print(f"🔍 DEBUG: .env SLACK_DEFAULT_CHANNEL = {os.getenv('SLACK_DEFAULT_CHANNEL')}")
    print(f"🔍 DEBUG: settings.slack_default_channel = {settings.slack_default_channel}")

    print(f"📤 Slack 채널로 테스트 질문 전송 중...")
    print(f"   채널 ID: {channel}")
    print()

    # 시나리오 1 - 질문 1: Drive 검색 조건
    question = Question(
        type=QuestionType.HYPOTHESIS,
        text="JIRA 티켓에 상세 스펙이 없을 때 Google Drive를 추가로 검색하시는 것 같은데, 맞나요?",
        question_text="JIRA 티켓에 상세 스펙이 없을 때 Google Drive를 추가로 검색하시는 것 같은데, 맞나요?",
        options=[
            QuestionOption(
                id="opt_1",
                text="네, JIRA에 상세 내용이 없으면 Drive 검색합니다",
                label="네, JIRA에 상세 내용이 없으면 Drive 검색합니다",
                value={"action": "add_rule"},
                is_default=True,
            ),
            QuestionOption(
                id="opt_2",
                text="스펙 관련 질문은 항상 JIRA + Drive 둘 다 검색합니다",
                label="스펙 관련 질문은 항상 JIRA + Drive 둘 다 검색합니다",
                value={"action": "update_rule"},
            ),
            QuestionOption(
                id="opt_3",
                text="질문자가 개발자일 때만 Drive까지 검색합니다",
                label="질문자가 개발자일 때만 Drive까지 검색합니다",
                value={"action": "add_condition"},
            ),
        ],
        source_pattern_id="pattern_pm_001",
        context="최근 5건의 답변 중 3건에서 JIRA 검색 후 Drive를 추가 검색했습니다. 3건 모두 '상세', '구체적', '정확한 수치' 관련 질문이었습니다.",
        priority=3,
    )

    try:
        # 질문 전송
        message = client.send_question(channel=channel, question=question)

        print("✅ 질문 전송 성공!")
        print(f"   메시지 TS: {message.ts}")
        print(f"   채널: {message.channel}")
        print(f"   질문 ID: {message.question_id}")
        print()
        print("📱 Slack 앱을 확인해보세요!")

    except Exception as e:
        print(f"❌ 전송 실패: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
