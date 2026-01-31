"""Shadow CLI

사용법:
    shadow start [--min MINUTES | --sec SECONDS | --duration SECONDS]   녹화 시작
    shadow stop                                                          녹화 중지
    shadow analyze [SESSION_DIR]                                         세션 분석
    shadow test-slack                                                    Slack 연동 테스트
    shadow mock-e2e                                                      모킹 E2E 테스트
"""

import argparse
import asyncio
import sys
import time
import uuid
from pathlib import Path

import numpy as np


def cmd_start(args):
    """녹화 시작"""
    from shadow.capture.recorder import Recorder
    from shadow.capture.storage import SessionStorage
    from shadow.preprocessing.keyframe import KeyframeExtractor

    # 우선순위: --sec > --min > --duration
    if args.sec is not None:
        duration = args.sec
    elif args.min is not None:
        duration = args.min * 60
    else:
        duration = args.duration

    print(f"녹화 시작 ({duration}초)...")
    print("녹화 중... Ctrl+C로 중지")

    recorder = Recorder()
    try:
        recorder.start()
        time.sleep(duration)
    except KeyboardInterrupt:
        print("\n녹화 중단됨")
    finally:
        session = recorder.stop()

    print(f"프레임 수: {len(session.frames)}")
    print(f"이벤트 수: {len(session.events)}")

    # 키프레임 쌍 추출
    extractor = KeyframeExtractor()
    pairs = extractor.extract_pairs(session)
    print(f"키프레임 쌍: {len(pairs)}개")

    # 저장
    storage = SessionStorage()
    session_dir = storage.save_session(session, pairs)
    print(f"저장 완료: {session_dir}")

    return session_dir


def cmd_stop(args):
    """녹화 중지 (현재는 start 명령에서 처리)"""
    print("녹화 중지는 start 명령 실행 중 Ctrl+C로 수행합니다.")


def cmd_analyze(args):
    """세션 분석"""
    session_dir = args.session_dir
    if not session_dir:
        print("세션 디렉토리를 지정하세요.")
        return

    print(f"분석 중: {session_dir}")
    # TODO: 실제 분석 구현
    print("분석 기능은 아직 구현 중입니다.")


def cmd_test_slack(args):
    """Slack 연동 테스트"""
    from shadow.hitl.models import Question, QuestionOption, QuestionType
    from shadow.slack.client import SlackClient

    client = SlackClient()

    if not client.is_configured:
        print("Slack Bot Token이 설정되지 않았습니다.")
        print("SLACK_BOT_TOKEN 환경 변수를 설정하세요.")
        return

    # 테스트 질문 생성
    question = Question(
        id=str(uuid.uuid4()),
        type=QuestionType.HYPOTHESIS,
        text="이것은 Shadow의 Slack 연동 테스트 메시지입니다.\n\n정상적으로 수신되었나요?",
        options=[
            QuestionOption(id="yes", text="예, 잘 보입니다", value={"test": True}),
            QuestionOption(id="no", text="아니오, 문제가 있습니다", value={"test": False}),
        ],
    )

    channel = args.channel
    if not channel:
        print("채널을 지정하세요: shadow test-slack --channel C12345678")
        return

    try:
        message = client.send_question(channel, question)
        print(f"메시지 전송 성공!")
        print(f"  채널: {message.channel}")
        print(f"  타임스탬프: {message.ts}")
        print(f"  질문 ID: {message.question_id}")
    except Exception as e:
        print(f"전송 실패: {e}")


def cmd_mock_e2e(args):
    """모킹 E2E 테스트

    Pipeline 클래스를 사용하여 전체 파이프라인을 테스트합니다.
    Record → Analyze → Patterns → Questions → Slack → Response → Spec
    """
    from shadow.pipeline import create_mock_pipeline
    from shadow.spec.builder import SpecStorage

    print("=== Shadow v0.1 Mock E2E 파이프라인 테스트 ===")

    # Mock 파이프라인 생성 및 실행
    pipeline = create_mock_pipeline(name="MockWorkflow", verbose=True)
    result = pipeline.run_sync(duration=5.0)

    if not result.success:
        print(f"\n[실패] {result.error}")
        return None

    # 명세서 저장
    storage = SpecStorage(base_dir="outputs")
    spec_path = storage.save(result.spec, filename="mock_e2e_spec.json")

    # 결과 요약
    print("\n" + "=" * 50)
    print(" E2E 테스트 완료")
    print("=" * 50)
    print(f"명세서 저장됨: {spec_path}")
    print(f"\n실행 통계:")
    for key, value in result.stats.items():
        print(f"  - {key}: {value}")

    return spec_path


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(
        description="Shadow - 화면 녹화 기반 자동화 패턴 학습",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령")

    # start 명령
    start_parser = subparsers.add_parser("start", help="녹화 시작")
    start_parser.add_argument(
        "--duration", "-d", type=int, default=10, help="녹화 시간 (초, 기본: 10)"
    )
    start_parser.add_argument(
        "--min", type=int, help="녹화 시간 (분)"
    )
    start_parser.add_argument(
        "--sec", type=int, help="녹화 시간 (초)"
    )

    # stop 명령
    stop_parser = subparsers.add_parser("stop", help="녹화 중지")

    # analyze 명령
    analyze_parser = subparsers.add_parser("analyze", help="세션 분석")
    analyze_parser.add_argument("session_dir", nargs="?", help="분석할 세션 디렉토리")

    # test-slack 명령
    slack_parser = subparsers.add_parser("test-slack", help="Slack 연동 테스트")
    slack_parser.add_argument("--channel", "-c", help="테스트 채널 ID")

    # mock-e2e 명령
    mock_parser = subparsers.add_parser("mock-e2e", help="Mock E2E 파이프라인 테스트")

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "test-slack":
        cmd_test_slack(args)
    elif args.command == "mock-e2e":
        cmd_mock_e2e(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
