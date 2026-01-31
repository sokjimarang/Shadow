#!/usr/bin/env python3
"""Shadow CLI 데모 스크립트

사용법:
    python demo.py --record 10    # 10초 녹화 (Claude 사용)
"""

import argparse
import asyncio
import sys

from shadow.analysis import AnalyzerBackend, ClaudeAnalyzer, LabeledAction, create_analyzer
from shadow.capture import InputEventType, Recorder
from shadow.patterns import DetectedPattern, create_pattern_analyzer
from shadow.preprocessing import KeyframeExtractor


def print_header(text: str) -> None:
    """섹션 헤더 출력"""
    print(f"\n{'=' * 50}")
    print(f" {text}")
    print("=" * 50)


def print_patterns(patterns: list[DetectedPattern]) -> None:
    """감지된 패턴 출력"""
    if not patterns:
        print("감지된 패턴 없음")
        return

    for i, pattern in enumerate(patterns, 1):
        print(f"\n패턴 #{i}:")
        print(f"  반복 횟수: {pattern.count}회")
        print(f"  구성 액션:")
        for action in pattern.actions:
            print(f"    - {action}")


async def record_and_analyze(duration: float, backend: str) -> None:
    """녹화 후 분석 수행"""
    print_header("녹화 시작")
    print(f"{duration}초 동안 화면과 입력을 녹화합니다...")
    print("녹화 중 반복 작업을 수행해보세요 (예: 같은 버튼 여러 번 클릭)")

    # 녹화
    recorder = Recorder()
    session = recorder.record(duration)

    print(f"\n녹화 완료!")
    print(f"  - 캡처된 프레임: {len(session.frames)}개")
    print(f"  - 수집된 이벤트: {len(session.events)}개")
    print(f"  - 녹화 시간: {session.duration:.1f}초")

    # 키프레임 추출
    print_header("키프레임 추출")

    # 마우스 클릭 우선, 없으면 키 입력 사용
    extractor = KeyframeExtractor()
    keyframes = extractor.extract(session)

    if not keyframes:
        # 키보드 이벤트로 폴백
        extractor = KeyframeExtractor(trigger_events={InputEventType.KEY_PRESS})
        keyframes = extractor.extract(session)
        if keyframes:
            print(f"(마우스 클릭 없음 - 키 입력 {len(keyframes)}개로 대체)")

    print(f"추출된 키프레임: {len(keyframes)}개")

    if not keyframes:
        print("분석할 이벤트가 없습니다.")
        return

    # AI 분석
    print_header("AI 분석")
    try:
        analyzer = create_analyzer(backend)
        print(f"백엔드: {analyzer.backend.value}")
        print(f"모델: {analyzer.model_name}")

        # Claude의 경우 예상 비용 표시
        if isinstance(analyzer, ClaudeAnalyzer):
            cost_info = analyzer.estimate_cost(keyframes)
            print(f"\n예상 비용:")
            print(f"  - 이미지 토큰: {cost_info['image_tokens']:,}")
            print(f"  - 프롬프트 캐싱: {cost_info['cache_savings']}")
            print(f"  - 예상 비용: ${cost_info['total_cost_usd']:.4f}")

        print(f"\n{len(keyframes)}개 키프레임 분석 중...")

        # 배치 분석
        actions = await analyzer.analyze_batch(keyframes)

        print("\n분석된 액션:")
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action}")

    except ValueError as e:
        print(f"API 키 오류: {e}")
        print("ANTHROPIC_API_KEY를 .env 파일에 설정하세요.")
        return
    except Exception as e:
        print(f"분석 오류: {e}")
        return

    # 패턴 감지 (LLM 기반)
    print_header("패턴 감지 (LLM)")
    try:
        pattern_analyzer = create_pattern_analyzer("claude")
        patterns = await pattern_analyzer.detect_patterns(actions)

        if patterns:
            print_patterns(patterns)
            # 불확실성 출력
            for pattern in patterns:
                if pattern.uncertainties:
                    print(f"\n  불확실 지점 ({len(pattern.uncertainties)}개):")
                    for u in pattern.uncertainties:
                        type_str = u.type.value if hasattr(u.type, "value") else u.type
                        print(f"    - [{type_str}] {u.hypothesis or u.description}")
        else:
            print("반복 패턴이 감지되지 않았습니다.")
            print("같은 동작을 3회 이상 반복해보세요.")
    except Exception as e:
        print(f"패턴 감지 오류: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Shadow: 화면 녹화 + 입력 분석 → 반복 패턴 감지"
    )
    parser.add_argument(
        "--record",
        type=float,
        metavar="SECONDS",
        help="녹화 시간 (초)",
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["claude", "nemotron"],
        default="claude",
        help="사용할 Vision AI 백엔드 (기본: claude)",
    )

    args = parser.parse_args()

    if args.record:
        asyncio.run(record_and_analyze(args.record, args.backend))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
