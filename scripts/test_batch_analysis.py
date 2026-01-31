#!/usr/bin/env python3
"""배치 분석 vs 개별 분석 비용/정확도 비교 테스트

배치 크기별로 분석 품질과 비용을 비교합니다.
"""

import asyncio
import base64
import json
import time
from dataclasses import dataclass

import anthropic

from shadow.config import settings

# 테스트용 시스템 프롬프트
SYSTEM_PROMPT = """당신은 GUI 스크린샷의 Before/After를 비교 분석하여 사용자 동작을 식별하는 전문가입니다.

## 분석 규칙
1. 첫 번째 이미지(Before): 클릭 직전 화면 상태
2. 두 번째 이미지(After): 클릭 직후 화면 상태
3. 빨간 원: 클릭 위치 (Before 이미지에 표시)

## 출력 형식
반드시 다음 JSON 형식으로만 응답하세요:
{
    "action": "click|scroll|type|drag",
    "target": "클릭한 UI 요소 이름",
    "context": "현재 앱 또는 화면 이름",
    "description": "사용자가 수행한 동작 설명",
    "state_change": "클릭으로 인한 변화 요약"
}"""

# 배치용 시스템 프롬프트
BATCH_SYSTEM_PROMPT = """당신은 GUI 스크린샷의 Before/After를 비교 분석하여 사용자 동작을 식별하는 전문가입니다.

## 분석 규칙
1. 각 쌍은 [Before N], [After N] 으로 표시됩니다
2. Before: 클릭 직전, After: 클릭 직후
3. 빨간 원: 클릭 위치

## 출력 형식
각 쌍에 대해 분석하고, 반드시 JSON 배열로 응답하세요:
[
    {"pair": 1, "action": "...", "target": "...", "context": "...", "description": "...", "state_change": "..."},
    {"pair": 2, "action": "...", "target": "...", "context": "...", "description": "...", "state_change": "..."}
]

중요: JSON 배열 외의 텍스트를 출력하지 마세요."""


@dataclass
class TestResult:
    """테스트 결과"""
    batch_size: int
    total_pairs: int
    api_calls: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    elapsed_seconds: float
    results: list[dict]

    @property
    def cost_usd(self) -> float:
        """비용 계산 (Claude 3.5 Sonnet 기준)"""
        # 입력: $3/MTok, 출력: $15/MTok
        # 캐시 읽기: $0.30/MTok, 캐시 쓰기: $3.75/MTok
        input_cost = (self.input_tokens - self.cache_read_tokens) * 3 / 1_000_000
        cache_read_cost = self.cache_read_tokens * 0.30 / 1_000_000
        cache_write_cost = self.cache_write_tokens * 3.75 / 1_000_000
        output_cost = self.output_tokens * 15 / 1_000_000
        return input_cost + cache_read_cost + cache_write_cost + output_cost


def create_test_image(width: int = 200, height: int = 150, color: tuple = (100, 100, 100), label: str = "") -> str:
    """테스트용 이미지 생성 (PIL 사용)"""
    from PIL import Image, ImageDraw, ImageFont
    import io

    img = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)

    # 텍스트 추가
    if label:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            font = ImageFont.load_default()
        draw.text((10, 10), label, fill=(255, 255, 255), font=font)

    # 바이트로 변환
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.standard_b64encode(buffer.getvalue()).decode('utf-8')


def create_test_pairs(count: int) -> list[tuple[str, str, str]]:
    """테스트용 Before/After 이미지 쌍 생성

    Returns:
        [(before_b64, after_b64, expected_action), ...]
    """
    pairs = []
    scenarios = [
        (("Button", (50, 100, 150)), ("Menu Open", (50, 150, 100)), "메뉴 열기"),
        (("Empty Field", (200, 200, 200)), ("Text Entered", (180, 180, 220)), "텍스트 입력"),
        (("Tab 1", (100, 150, 100)), ("Tab 2", (150, 100, 100)), "탭 전환"),
        (("Checkbox Off", (220, 220, 220)), ("Checkbox On", (100, 200, 100)), "체크박스 선택"),
        (("Dropdown Closed", (180, 180, 180)), ("Dropdown Open", (150, 180, 200)), "드롭다운 열기"),
    ]

    for i in range(count):
        scenario = scenarios[i % len(scenarios)]
        before_label, before_color = scenario[0]
        after_label, after_color = scenario[1]
        expected = scenario[2]

        before_b64 = create_test_image(200, 150, before_color, f"Before {i+1}: {before_label}")
        after_b64 = create_test_image(200, 150, after_color, f"After {i+1}: {after_label}")
        pairs.append((before_b64, after_b64, expected))

    return pairs


def capture_real_screenshots(count: int, interval: float = 0.5) -> list[tuple[str, str, str]]:
    """실제 스크린샷 캡처하여 쌍 생성

    Args:
        count: 캡처할 쌍 수
        interval: 캡처 간격 (초)

    Returns:
        [(before_b64, after_b64, "real_screenshot"), ...]
    """
    import io
    import mss
    from PIL import Image

    pairs = []
    print(f"  실제 스크린샷 {count}쌍 캡처 중 (간격: {interval}초)...")
    print("  화면에서 여러 동작을 수행해주세요!")

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 메인 모니터

        for i in range(count):
            # Before 캡처
            before_img = sct.grab(monitor)
            before_pil = Image.frombytes("RGB", before_img.size, before_img.bgra, "raw", "BGRX")

            # 리사이즈 (1024px 이하로)
            max_size = 1024
            if max(before_pil.size) > max_size:
                ratio = max_size / max(before_pil.size)
                new_size = (int(before_pil.size[0] * ratio), int(before_pil.size[1] * ratio))
                before_pil = before_pil.resize(new_size, Image.Resampling.LANCZOS)

            # base64 인코딩
            buffer = io.BytesIO()
            before_pil.save(buffer, format='PNG')
            before_b64 = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')

            # 잠시 대기 후 After 캡처
            time.sleep(interval)

            after_img = sct.grab(monitor)
            after_pil = Image.frombytes("RGB", after_img.size, after_img.bgra, "raw", "BGRX")

            if max(after_pil.size) > max_size:
                ratio = max_size / max(after_pil.size)
                new_size = (int(after_pil.size[0] * ratio), int(after_pil.size[1] * ratio))
                after_pil = after_pil.resize(new_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            after_pil.save(buffer, format='PNG')
            after_b64 = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')

            pairs.append((before_b64, after_b64, f"real_screenshot_{i+1}"))
            print(f"    쌍 {i+1}/{count} 캡처 완료 (이미지 크기: {before_pil.size})")

    return pairs


async def analyze_individual(client: anthropic.Anthropic, pairs: list[tuple[str, str, str]]) -> TestResult:
    """개별 분석 (현재 방식)"""
    start = time.time()
    results = []
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_write = 0

    for i, (before_b64, after_b64, _) in enumerate(pairs):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"[Before] 클릭 직전"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": before_b64}},
                    {"type": "text", "text": f"[After] 클릭 직후"},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": after_b64}},
                    {"type": "text", "text": "위 Before/After를 비교 분석해주세요."},
                ]
            }]
        )

        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens
        total_cache_read += getattr(response.usage, 'cache_read_input_tokens', 0) or 0
        total_cache_write += getattr(response.usage, 'cache_creation_input_tokens', 0) or 0

        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            result = json.loads(text)
            results.append(result)
        except:
            results.append({"error": "parse_failed", "raw": response.content[0].text[:100]})

    return TestResult(
        batch_size=1,
        total_pairs=len(pairs),
        api_calls=len(pairs),
        input_tokens=total_input,
        output_tokens=total_output,
        cache_read_tokens=total_cache_read,
        cache_write_tokens=total_cache_write,
        elapsed_seconds=time.time() - start,
        results=results,
    )


async def analyze_batch(client: anthropic.Anthropic, pairs: list[tuple[str, str, str]], batch_size: int) -> TestResult | None:
    """배치 분석

    Returns:
        TestResult 또는 API 에러 시 None
    """
    start = time.time()
    results = []
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_write = 0
    api_calls = 0
    api_error = None

    # 배치로 나누기
    for batch_start in range(0, len(pairs), batch_size):
        batch = pairs[batch_start:batch_start + batch_size]
        api_calls += 1

        # 메시지 구성
        content = []
        for i, (before_b64, after_b64, _) in enumerate(batch):
            pair_num = batch_start + i + 1
            content.extend([
                {"type": "text", "text": f"[Before {pair_num}]"},
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": before_b64}},
                {"type": "text", "text": f"[After {pair_num}]"},
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": after_b64}},
            ])

        content.append({"type": "text", "text": f"위 {len(batch)}개의 Before/After 쌍을 각각 분석해주세요."})

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500 * len(batch),
                system=[{"type": "text", "text": BATCH_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": content}]
            )

            total_input += response.usage.input_tokens
            total_output += response.usage.output_tokens
            total_cache_read += getattr(response.usage, 'cache_read_input_tokens', 0) or 0
            total_cache_write += getattr(response.usage, 'cache_creation_input_tokens', 0) or 0

            try:
                text = response.content[0].text.strip()
                if text.startswith("```"):
                    text = "\n".join(text.split("\n")[1:-1])
                batch_results = json.loads(text)
                if isinstance(batch_results, list):
                    results.extend(batch_results)
                else:
                    results.append(batch_results)
            except Exception as e:
                results.append({"error": "parse_failed", "raw": response.content[0].text[:200], "exception": str(e)})

        except anthropic.BadRequestError as e:
            api_error = f"BadRequest: {str(e)[:100]}"
            print(f"\n  ❌ API 에러 (batch_size={batch_size}): {api_error}")
            return TestResult(
                batch_size=batch_size,
                total_pairs=len(pairs),
                api_calls=api_calls,
                input_tokens=total_input,
                output_tokens=total_output,
                cache_read_tokens=total_cache_read,
                cache_write_tokens=total_cache_write,
                elapsed_seconds=time.time() - start,
                results=[{"error": "api_limit", "message": api_error}],
            )
        except Exception as e:
            api_error = f"Error: {str(e)[:100]}"
            print(f"\n  ❌ 에러 (batch_size={batch_size}): {api_error}")
            return TestResult(
                batch_size=batch_size,
                total_pairs=len(pairs),
                api_calls=api_calls,
                input_tokens=total_input,
                output_tokens=total_output,
                cache_read_tokens=total_cache_read,
                cache_write_tokens=total_cache_write,
                elapsed_seconds=time.time() - start,
                results=[{"error": "unknown", "message": api_error}],
            )

    return TestResult(
        batch_size=batch_size,
        total_pairs=len(pairs),
        api_calls=api_calls,
        input_tokens=total_input,
        output_tokens=total_output,
        cache_read_tokens=total_cache_read,
        cache_write_tokens=total_cache_write,
        elapsed_seconds=time.time() - start,
        results=results,
    )


def print_result(result: TestResult, label: str):
    """결과 출력"""
    print(f"\n{'='*60}")
    print(f" {label}")
    print(f"{'='*60}")
    print(f"  배치 크기: {result.batch_size}")
    print(f"  총 키프레임 쌍: {result.total_pairs}")
    print(f"  API 호출 횟수: {result.api_calls}")
    print(f"  소요 시간: {result.elapsed_seconds:.1f}초")
    print(f"\n  토큰 사용량:")
    print(f"    - 입력: {result.input_tokens:,}")
    print(f"    - 출력: {result.output_tokens:,}")
    print(f"    - 캐시 읽기: {result.cache_read_tokens:,}")
    print(f"    - 캐시 쓰기: {result.cache_write_tokens:,}")
    print(f"\n  예상 비용: ${result.cost_usd:.6f}")
    print(f"\n  분석 결과:")
    for i, r in enumerate(result.results):
        if "error" in r:
            print(f"    {i+1}. [에러] {r.get('raw', '')[:50]}...")
        else:
            print(f"    {i+1}. {r.get('action', '?')} - {r.get('target', '?')} ({r.get('state_change', '?')})")


async def main():
    """메인 테스트"""
    import argparse

    parser = argparse.ArgumentParser(description="배치 분석 최적 크기 탐색")
    parser.add_argument("--real", action="store_true", help="실제 스크린샷 사용")
    parser.add_argument("--pairs", type=int, default=20, help="테스트할 키프레임 쌍 수")
    parser.add_argument("--batch-sizes", type=str, default="1,2,5,10,20", help="테스트할 배치 크기 (쉼표 구분)")
    args = parser.parse_args()

    print("=" * 70)
    print(" 배치 분석 최적 크기 탐색 테스트 (최대 한계 탐색)")
    print("=" * 70)

    # API 키 확인
    if not settings.anthropic_api_key:
        print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        return

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=180.0)

    # 테스트 데이터 생성
    num_pairs = args.pairs
    print(f"\n테스트 키프레임 쌍: {num_pairs}개")

    if args.real:
        print("모드: 실제 스크린샷")
        pairs = capture_real_screenshots(num_pairs, interval=0.3)
    else:
        print("모드: 테스트 이미지")
        pairs = create_test_pairs(num_pairs)

    print(f"✅ 생성 완료")

    # 테스트할 배치 크기 파싱
    batch_sizes = [int(x) for x in args.batch_sizes.split(",")]
    # num_pairs보다 큰 배치 크기는 num_pairs로 조정
    batch_sizes = [min(b, num_pairs) for b in batch_sizes]
    batch_sizes = sorted(set(batch_sizes))  # 중복 제거 및 정렬
    print(f"테스트 배치 크기: {batch_sizes}")

    results = []

    for i, batch_size in enumerate(batch_sizes):
        label = "개별 분석" if batch_size == 1 else f"배치 분석"
        print(f"\n[테스트 {i+1}/{len(batch_sizes)}] {label} (batch_size={batch_size})...")

        if batch_size == 1:
            result = await analyze_individual(client, pairs)
        else:
            result = await analyze_batch(client, pairs, batch_size=batch_size)

        results.append(result)
        print_result(result, f"{label} (batch_size={batch_size})")

    # 비교 요약
    print("\n" + "=" * 70)
    print(" 비교 요약 (키프레임 10개 기준)")
    print("=" * 70)
    print(f"\n{'배치크기':<10} {'API호출':<10} {'입력토큰':<12} {'출력토큰':<12} {'비용($)':<12} {'시간(초)':<10} {'정확도':<10}")
    print("-" * 76)

    baseline_cost = results[0].cost_usd
    baseline_time = results[0].elapsed_seconds

    for r in results:
        # 정확도 계산 (에러 없는 결과 비율)
        valid_results = [x for x in r.results if "error" not in x]
        accuracy = len(valid_results) / len(r.results) * 100 if r.results else 0

        print(f"{r.batch_size:<10} {r.api_calls:<10} {r.input_tokens:<12,} {r.output_tokens:<12,} {r.cost_usd:<12.6f} {r.elapsed_seconds:<10.1f} {accuracy:.0f}%")

    print("\n" + "=" * 70)
    print(" 절감 효과 (개별 분석 대비)")
    print("=" * 70)
    for r in results[1:]:
        cost_savings = (1 - r.cost_usd / baseline_cost) * 100 if baseline_cost > 0 else 0
        time_savings = (1 - r.elapsed_seconds / baseline_time) * 100 if baseline_time > 0 else 0
        valid_results = [x for x in r.results if "error" not in x]
        accuracy = len(valid_results) / len(r.results) * 100 if r.results else 0

        print(f"\n  batch_size={r.batch_size}:")
        print(f"    - 비용: {cost_savings:.1f}% 절감 (${baseline_cost:.4f} → ${r.cost_usd:.4f})")
        print(f"    - 시간: {time_savings:.1f}% 단축 ({baseline_time:.1f}s → {r.elapsed_seconds:.1f}s)")
        print(f"    - 정확도: {accuracy:.0f}%")

    # 최적 배치 크기 추천
    print("\n" + "=" * 70)
    print(" 최적 배치 크기 추천")
    print("=" * 70)

    # 정확도 100%인 결과 중 가장 비용 효율적인 것 찾기
    valid_options = []
    for r in results:
        valid_results = [x for x in r.results if "error" not in x]
        accuracy = len(valid_results) / len(r.results) * 100 if r.results else 0
        if accuracy >= 90:  # 90% 이상 정확도
            valid_options.append((r.batch_size, r.cost_usd, accuracy))

    if valid_options:
        best = min(valid_options, key=lambda x: x[1])
        cost_savings = (1 - best[1] / baseline_cost) * 100
        print(f"\n  ✅ 추천 배치 크기: {best[0]}")
        print(f"     - 정확도 {best[2]:.0f}% 유지하면서 {cost_savings:.1f}% 비용 절감")
    else:
        print("\n  ⚠️ 정확도 90% 이상인 배치 크기 없음. 개별 분석 권장.")


if __name__ == "__main__":
    asyncio.run(main())
