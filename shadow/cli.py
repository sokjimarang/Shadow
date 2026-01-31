"""Shadow CLI

사용법:
    shadow start [--duration SECONDS]   녹화 시작
    shadow stop                         녹화 중지
    shadow analyze [SESSION_DIR]        세션 분석
    shadow test-slack                   Slack 연동 테스트
    shadow mock-e2e                     모킹 E2E 테스트
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


def cmd_mock_e2e_legacy(args):
    """[레거시] 기존 하드코딩 방식의 E2E 테스트

    Pipeline 클래스 도입 이전 코드. 비교 테스트용으로 유지.
    """
    print("=== Shadow v0.1 모킹 E2E 테스트 (레거시) ===\n")

    # 1. 더미 데이터 생성
    print("[1/6] 더미 데이터 생성...")
    from shadow.analysis.models import LabeledAction
    from shadow.capture.models import Frame, InputEvent, InputEventType, KeyframePair
    from shadow.patterns.models import DetectedPattern, Uncertainty, UncertaintyType

    # 더미 프레임
    dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
    frames = [
        Frame(timestamp=i * 0.1, image=dummy_image)
        for i in range(10)
    ]

    # 더미 이벤트
    events = [
        InputEvent(
            timestamp=i * 0.5,
            event_type=InputEventType.MOUSE_CLICK,
            x=100 + i * 10,
            y=200 + i * 10,
            button="left",
            app_name="TestApp",
            window_title="Test Window",
        )
        for i in range(3)
    ]

    # 더미 키프레임 쌍
    pairs = [
        KeyframePair(
            before_frame=frames[i],
            after_frame=frames[i + 1] if i + 1 < len(frames) else frames[i],
            trigger_event=events[i] if i < len(events) else events[0],
        )
        for i in range(min(3, len(events)))
    ]
    print(f"  - 프레임: {len(frames)}개")
    print(f"  - 이벤트: {len(events)}개")
    print(f"  - 키프레임 쌍: {len(pairs)}개")

    # 2. 더미 액션 라벨 생성 (PRD: 3회 반복 필요)
    print("\n[2/6] 액션 라벨 생성 (VLM 모킹)...")
    actions = [
        # 1회차
        LabeledAction(
            action="click",
            target="저장 버튼",
            context="TestApp",
            description="파일 저장 버튼 클릭",
            before_state="저장되지 않은 상태",
            after_state="저장 완료",
            state_change="파일이 저장됨",
        ),
        LabeledAction(
            action="click",
            target="확인 버튼",
            context="TestApp - 다이얼로그",
            description="확인 다이얼로그에서 확인 클릭",
        ),
        # 2회차
        LabeledAction(
            action="click",
            target="저장 버튼",
            context="TestApp",
            description="파일 저장 버튼 클릭",
        ),
        LabeledAction(
            action="click",
            target="확인 버튼",
            context="TestApp - 다이얼로그",
            description="확인 다이얼로그에서 확인 클릭",
        ),
        # 3회차
        LabeledAction(
            action="click",
            target="저장 버튼",
            context="TestApp",
            description="파일 저장 버튼 클릭",
        ),
        LabeledAction(
            action="click",
            target="확인 버튼",
            context="TestApp - 다이얼로그",
            description="확인 다이얼로그에서 확인 클릭",
        ),
    ]
    for a in actions:
        print(f"  - {a}")

    # 3. 패턴 감지
    print("\n[3/6] 패턴 감지...")
    from shadow.patterns.detector import PatternDetector

    detector = PatternDetector(min_length=1, min_occurrences=3)  # PRD: 3회 관찰 필요
    patterns = detector.detect(actions)

    # 패턴에 불확실성 추가 (테스트용)
    if patterns:
        patterns[0].uncertainties.append(
            Uncertainty(
                type=UncertaintyType.CONDITION,
                description="이 저장 작업은 항상 수행하나요, 아니면 특정 조건에서만 수행하나요?",
                confidence=0.7,
            )
        )
        patterns[0].uncertainties.append(
            Uncertainty(
                type=UncertaintyType.QUALITY,
                description="저장 결과물의 품질 기준이 있나요?",
                confidence=0.6,
            )
        )

    print(f"  - 감지된 패턴: {len(patterns)}개")
    for p in patterns:
        print(f"    {p}")
        print(f"    불확실성: {len(p.uncertainties)}개")

    # 4. HITL 질문 생성
    print("\n[4/6] HITL 질문 생성...")
    from shadow.hitl.generator import QuestionGenerator

    generator = QuestionGenerator()
    questions = generator.generate_from_patterns(patterns)
    print(f"  - 생성된 질문: {len(questions)}개")
    for q in questions:
        print(f"    [{q.type}] {q.text[:50]}...")

    # 5. 더미 응답 생성 (Slack 모킹)
    print("\n[5/6] HITL 응답 시뮬레이션...")
    from shadow.hitl.models import Response

    responses = []
    for q in questions:
        # 첫 번째 옵션을 선택한 것으로 시뮬레이션
        response = Response(
            question_id=q.id,
            selected_option_id=q.options[0].id,
            selected_value=q.options[0].value,
            user_id="mock_user",
        )
        responses.append((q, response))
        print(f"  - 질문 {q.id[:8]}... → 응답: {q.options[0].text}")

    # 6. 명세서 생성
    print("\n[6/6] 명세서 생성...")
    from shadow.spec.builder import SpecBuilder, SpecStorage

    builder = SpecBuilder(name="TestWorkflow", description="E2E 테스트 명세서")

    for pattern in patterns:
        builder.add_pattern(pattern)

    for question, response in responses:
        builder.add_response(question, response)

    builder.add_session("mock_session_001")

    spec = builder.build()

    # 저장
    storage = SpecStorage(base_dir="outputs")
    spec_path = storage.save(spec, filename="mock_e2e_spec.json")

    print(f"\n=== E2E 테스트 완료 ===")
    print(f"명세서 저장됨: {spec_path}")
    print(f"\n명세서 내용:")
    print(f"  - 이름: {spec.meta.name}")
    print(f"  - 워크플로우 단계: {len(spec.workflow)}개")
    print(f"  - 의사결정 규칙: {len(spec.decisions)}개")
    print(f"  - 원본 패턴: {len(spec.raw_patterns)}개")

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

    # mock-e2e-legacy 명령 (비교용)
    legacy_parser = subparsers.add_parser("mock-e2e-legacy", help="[레거시] 기존 방식 E2E 테스트")

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
    elif args.command == "mock-e2e-legacy":
        cmd_mock_e2e_legacy(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
