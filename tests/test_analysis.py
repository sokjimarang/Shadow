"""Analysis 모듈 테스트

- 단위 테스트: Mock 사용, API 호출 없음
- 통합 테스트: 실제 Claude API 호출 (pytest -m integration)
"""

import numpy as np
import pytest

from shadow.analysis import ClaudeAnalyzer, LabeledAction, create_analyzer
from shadow.capture.models import Frame, InputEvent, InputEventType, KeyframePair


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_labeled_action():
    """테스트용 LabeledAction"""
    return LabeledAction(
        action="click",
        target="Submit 버튼",
        context="Chrome/로그인 페이지",
        description="로그인 버튼을 클릭하여 인증 시도",
        before_state="로그인 폼이 표시됨",
        after_state="로딩 스피너가 나타남",
        state_change="로그인 처리 시작",
    )


@pytest.fixture
def sample_keyframe_pair():
    """테스트용 KeyframePair 생성"""
    # 100x100 빨간색 이미지 (Before)
    before_image = np.zeros((100, 100, 3), dtype=np.uint8)
    before_image[:, :, 0] = 255  # Red

    # 100x100 초록색 이미지 (After)
    after_image = np.zeros((100, 100, 3), dtype=np.uint8)
    after_image[:, :, 1] = 255  # Green

    before_frame = Frame(timestamp=1000.0, image=before_image)
    after_frame = Frame(timestamp=1000.3, image=after_image)

    trigger_event = InputEvent(
        timestamp=1000.0,
        event_type=InputEventType.MOUSE_CLICK,
        x=50,
        y=50,
        button="left",
        app_name="TestApp",
        window_title="Test Window",
    )

    return KeyframePair(
        before_frame=before_frame,
        after_frame=after_frame,
        trigger_event=trigger_event,
    )


# =============================================================================
# 단위 테스트 (Mock, API 호출 없음)
# =============================================================================


class TestLabeledAction:
    """LabeledAction 모델 테스트"""

    def test_semantic_label_computed_field(self, sample_labeled_action):
        """semantic_label은 description의 별칭"""
        action = sample_labeled_action
        assert action.semantic_label == action.description
        assert action.semantic_label == "로그인 버튼을 클릭하여 인증 시도"

    def test_target_element_computed_field(self, sample_labeled_action):
        """target_element는 target의 별칭"""
        action = sample_labeled_action
        assert action.target_element == action.target
        assert action.target_element == "Submit 버튼"

    def test_app_from_context(self, sample_labeled_action):
        """context에서 앱 이름 추출"""
        action = sample_labeled_action
        assert action.app == "Chrome"
        assert action.app_context == "로그인 페이지"

    def test_app_without_slash(self):
        """context에 /가 없는 경우"""
        action = LabeledAction(
            action="click",
            target="버튼",
            context="Slack",
            description="테스트",
        )
        assert action.app == "Slack"
        assert action.app_context is None


class TestClaudeAnalyzerParseResponse:
    """ClaudeAnalyzer._parse_pair_response 테스트"""

    @pytest.fixture
    def analyzer(self, monkeypatch):
        """Mock API 키로 analyzer 생성"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        return ClaudeAnalyzer(api_key="test-key")

    def test_parse_batch_response_valid(self, analyzer):
        """유효한 배치 JSON 배열 파싱"""
        response = """[
            {"pair": 1, "action": "click", "target": "버튼1", "context": "App1", "description": "설명1", "state_change": "변화1"},
            {"pair": 2, "action": "scroll", "target": "페이지", "context": "App2", "description": "설명2", "state_change": "변화2"}
        ]"""

        results = analyzer._parse_batch_response(response, expected_count=2)

        assert len(results) == 2
        assert results[0].action == "click"
        assert results[0].target == "버튼1"
        assert results[1].action == "scroll"
        assert results[1].target == "페이지"

    def test_parse_batch_response_fills_missing(self, analyzer):
        """결과가 부족하면 unknown으로 채움"""
        response = """[
            {"pair": 1, "action": "click", "target": "버튼", "context": "App", "description": "설명"}
        ]"""

        results = analyzer._parse_batch_response(response, expected_count=3)

        assert len(results) == 3
        assert results[0].action == "click"
        assert results[1].action == "unknown"
        assert results[2].action == "unknown"

    def test_parse_batch_response_invalid_json(self, analyzer):
        """잘못된 JSON은 모두 unknown 반환"""
        response = "이것은 JSON이 아닙니다"

        results = analyzer._parse_batch_response(response, expected_count=2)

        assert len(results) == 2
        assert results[0].action == "unknown"
        assert results[1].action == "unknown"

    def test_parse_valid_json(self, analyzer):
        """유효한 JSON 응답 파싱"""
        response = """{
            "action": "click",
            "target": "검색 버튼",
            "context": "Chrome/Google",
            "description": "구글 검색 실행",
            "before_state": "검색어 입력됨",
            "after_state": "검색 결과 표시",
            "state_change": "검색 결과 페이지로 이동"
        }"""

        result = analyzer._parse_pair_response(response)

        assert result.action == "click"
        assert result.target == "검색 버튼"
        assert result.context == "Chrome/Google"
        assert result.state_change == "검색 결과 페이지로 이동"

    def test_parse_json_with_markdown(self, analyzer):
        """마크다운 코드 블록으로 감싼 JSON 파싱"""
        response = """```json
{
    "action": "scroll",
    "target": "페이지",
    "context": "VSCode",
    "description": "코드 스크롤"
}
```"""

        result = analyzer._parse_pair_response(response)

        assert result.action == "scroll"
        assert result.target == "페이지"

    def test_parse_invalid_json_fallback(self, analyzer):
        """잘못된 JSON은 unknown으로 폴백"""
        response = "이것은 JSON이 아닙니다"

        result = analyzer._parse_pair_response(response)

        assert result.action == "unknown"
        assert result.target == "unknown"
        assert result.description == response[:200]


class TestCreateAnalyzer:
    """create_analyzer 팩토리 함수 테스트"""

    def test_create_claude_analyzer(self, monkeypatch):
        """Claude analyzer 생성"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        analyzer = create_analyzer("claude")
        assert isinstance(analyzer, ClaudeAnalyzer)

    def test_create_invalid_backend(self):
        """존재하지 않는 백엔드 에러"""
        with pytest.raises(ValueError, match="not a valid AnalyzerBackend"):
            create_analyzer("invalid")


# =============================================================================
# 통합 테스트 (실제 API 호출)
# =============================================================================


@pytest.mark.integration
class TestClaudeAnalyzerIntegration:
    """실제 Claude API 호출 테스트

    실행: uv run pytest tests/test_analysis.py -v -s -m integration
    """

    @pytest.mark.asyncio
    async def test_claude_analyzer_e2e(self, sample_keyframe_pair):
        """실제 API 호출 후 결과 출력

        이 테스트는 실제 semantic_label 결과를 터미널에서 확인하기 위한 것입니다.
        """
        analyzer = ClaudeAnalyzer()
        result = await analyzer.analyze_keyframe_pair(sample_keyframe_pair)

        # 결과 출력 (눈으로 확인)
        print("\n" + "=" * 50)
        print("VLM 분석 결과")
        print("=" * 50)
        print(f"action: {result.action}")
        print(f"target: {result.target}")
        print(f"context: {result.context}")
        print(f"semantic_label: {result.semantic_label}")
        print(f"before_state: {result.before_state}")
        print(f"after_state: {result.after_state}")
        print(f"state_change: {result.state_change}")
        print("=" * 50)

        # 기본 검증
        assert result.action, "action이 비어있음"
        assert result.target, "target이 비어있음"
        assert result.semantic_label, "semantic_label이 비어있음"

    @pytest.mark.asyncio
    async def test_claude_analyzer_batch(self, sample_keyframe_pair):
        """배치 분석 테스트

        여러 키프레임 쌍을 한 번에 분석합니다.
        """
        analyzer = ClaudeAnalyzer()

        # 같은 쌍을 3개로 복제해서 테스트
        pairs = [sample_keyframe_pair, sample_keyframe_pair, sample_keyframe_pair]

        results = await analyzer.analyze_batch(pairs, batch_size=3)

        # 결과 출력
        print("\n" + "=" * 50)
        print("배치 분석 결과 (3개 쌍)")
        print("=" * 50)
        for i, result in enumerate(results):
            print(f"\n[{i+1}] action: {result.action}")
            print(f"    target: {result.target}")
            print(f"    state_change: {result.state_change}")
        print("=" * 50)

        # 기본 검증
        assert len(results) == 3, f"결과 수가 3이어야 함, 실제: {len(results)}"
        for i, result in enumerate(results):
            assert result.action, f"결과 {i+1}: action이 비어있음"
