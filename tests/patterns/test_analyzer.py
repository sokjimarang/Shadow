"""LLM 패턴 분석기 테스트

테스트 케이스:
- 패턴 감지 확인
- 불확실성 포함 확인
- 액션 포맷팅 검증
- JSON 파싱 검증
- 파싱 실패 시 빈 리스트 반환
"""

import pytest

from shadow.analysis.models import LabeledAction
from shadow.patterns.analyzer.base import BasePatternAnalyzer, PatternAnalyzerBackend
from shadow.patterns.analyzer.claude import ClaudePatternAnalyzer
from shadow.patterns.models import DetectedPattern, Uncertainty, UncertaintyType


class TestClaudePatternAnalyzerFormatting:
    """액션 포맷팅 테스트"""

    def test_format_actions_basic(self):
        """기본 액션 포맷팅"""
        # Given
        analyzer = _create_mock_analyzer()
        actions = [
            LabeledAction(
                action="click",
                target="저장 버튼",
                context="Chrome/Gmail",
                description="파일 저장",
            ),
            LabeledAction(
                action="type",
                target="검색창",
                context="Chrome/Google",
                description="검색어 입력",
            ),
        ]

        # When
        result = analyzer._format_actions(actions)

        # Then
        assert "[0] click: 저장 버튼 @ Chrome/Gmail - 파일 저장" in result
        assert "[1] type: 검색창 @ Chrome/Google - 검색어 입력" in result

    def test_format_actions_with_state_change(self):
        """상태 변화가 있는 액션 포맷팅"""
        # Given
        analyzer = _create_mock_analyzer()
        actions = [
            LabeledAction(
                action="click",
                target="메뉴 버튼",
                context="App",
                description="메뉴 열기",
                state_change="메뉴가 열림",
            ),
        ]

        # When
        result = analyzer._format_actions(actions)

        # Then
        assert "(변화: 메뉴가 열림)" in result


class TestClaudePatternAnalyzerParsing:
    """응답 파싱 테스트"""

    def test_parse_response_valid_json(self):
        """유효한 JSON 응답 파싱"""
        # Given
        analyzer = _create_mock_analyzer()
        actions = _create_sample_actions(6)
        response = """{
            "patterns": [
                {
                    "name": "저장 패턴",
                    "description": "파일 저장 작업",
                    "action_indices": [0, 2, 4],
                    "actions_per_occurrence": 2,
                    "confidence": 0.9,
                    "uncertainties": [
                        {
                            "type": "CONDITION",
                            "description": "저장 조건",
                            "hypothesis": "특정 조건에서만 저장하나요?",
                            "related_action_indices": [0]
                        }
                    ]
                }
            ],
            "analysis_summary": "1개 패턴 감지"
        }"""

        # When
        result = analyzer._parse_response(response, actions)

        # Then
        assert len(result) == 1
        assert result[0].name == "저장 패턴"
        assert result[0].confidence == 0.9
        assert len(result[0].uncertainties) == 1
        assert result[0].uncertainties[0].type == UncertaintyType.CONDITION

    def test_parse_response_with_markdown_code_block(self):
        """마크다운 코드 블록으로 감싸진 응답 파싱"""
        # Given
        analyzer = _create_mock_analyzer()
        actions = _create_sample_actions(6)
        response = """```json
{
    "patterns": [
        {
            "name": "테스트 패턴",
            "action_indices": [0, 2, 4],
            "actions_per_occurrence": 1,
            "confidence": 0.8,
            "uncertainties": []
        }
    ],
    "analysis_summary": "테스트"
}
```"""

        # When
        result = analyzer._parse_response(response, actions)

        # Then
        assert len(result) == 1
        assert result[0].name == "테스트 패턴"

    def test_parse_response_invalid_json(self):
        """유효하지 않은 JSON 응답 처리"""
        # Given
        analyzer = _create_mock_analyzer()
        actions = _create_sample_actions(3)
        response = "이것은 JSON이 아닙니다."

        # When
        result = analyzer._parse_response(response, actions)

        # Then
        assert result == []

    def test_parse_response_empty_patterns(self):
        """빈 패턴 배열 응답 처리"""
        # Given
        analyzer = _create_mock_analyzer()
        actions = _create_sample_actions(3)
        response = '{"patterns": [], "analysis_summary": "패턴 없음"}'

        # When
        result = analyzer._parse_response(response, actions)

        # Then
        assert result == []

    def test_parse_response_filters_low_confidence(self):
        """낮은 신뢰도 패턴 필터링"""
        # Given
        analyzer = _create_mock_analyzer(min_confidence=0.5)
        actions = _create_sample_actions(6)
        response = """{
            "patterns": [
                {
                    "name": "높은 신뢰도",
                    "action_indices": [0],
                    "actions_per_occurrence": 1,
                    "confidence": 0.8,
                    "uncertainties": []
                },
                {
                    "name": "낮은 신뢰도",
                    "action_indices": [1],
                    "actions_per_occurrence": 1,
                    "confidence": 0.3,
                    "uncertainties": []
                }
            ]
        }"""

        # When
        result = analyzer._parse_response(response, actions)

        # Then
        assert len(result) == 1
        assert result[0].name == "높은 신뢰도"


class TestClaudePatternAnalyzerUncertaintyTypes:
    """불확실성 타입 파싱 테스트"""

    @pytest.mark.parametrize(
        "type_str,expected",
        [
            ("CONDITION", UncertaintyType.CONDITION),
            ("EXCEPTION", UncertaintyType.EXCEPTION),
            ("QUALITY", UncertaintyType.QUALITY),
            ("ALTERNATIVE", UncertaintyType.ALTERNATIVE),
            ("VARIANT", UncertaintyType.VARIANT),
            ("SEQUENCE", UncertaintyType.SEQUENCE),
            ("OPTIONAL", UncertaintyType.OPTIONAL),
            ("unknown", UncertaintyType.VARIANT),  # 기본값
        ],
    )
    def test_parse_uncertainty_type(self, type_str: str, expected: UncertaintyType):
        """불확실성 타입 파싱 검증"""
        # Given
        analyzer = _create_mock_analyzer()

        # When
        result = analyzer._parse_uncertainty_type(type_str)

        # Then
        assert result == expected


class TestPatternAnalyzerBackend:
    """패턴 분석기 백엔드 테스트"""

    def test_backend_property(self):
        """백엔드 속성 확인"""
        # Given
        analyzer = _create_mock_analyzer()

        # When/Then
        assert analyzer.backend == PatternAnalyzerBackend.CLAUDE

    def test_model_name_property(self):
        """모델 이름 속성 확인"""
        # Given
        analyzer = _create_mock_analyzer(model="claude-3-5-sonnet-20241022")

        # When/Then
        assert analyzer.model_name == "claude-3-5-sonnet-20241022"


class TestCreatePatternAnalyzer:
    """팩토리 함수 테스트"""

    def test_create_claude_analyzer(self, monkeypatch):
        """Claude 분석기 생성"""
        # Given
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # When
        from shadow.patterns import create_pattern_analyzer

        analyzer = create_pattern_analyzer("claude", api_key="test-key")

        # Then
        assert isinstance(analyzer, ClaudePatternAnalyzer)
        assert analyzer.backend == PatternAnalyzerBackend.CLAUDE

    def test_create_invalid_backend_raises(self):
        """지원하지 않는 백엔드 에러"""
        # When/Then
        from shadow.patterns import create_pattern_analyzer

        with pytest.raises(ValueError, match="지원하지 않는 백엔드"):
            create_pattern_analyzer("invalid")


# 헬퍼 함수들
def _create_mock_analyzer(
    model: str = "claude-opus-4-5-20251101",
    min_confidence: float = 0.3,
) -> ClaudePatternAnalyzer:
    """테스트용 분석기 생성 (API 호출 없음)"""
    return ClaudePatternAnalyzer(
        api_key="test-key",
        model=model,
        use_cache=False,
        min_confidence=min_confidence,
    )


def _create_sample_actions(count: int) -> list[LabeledAction]:
    """테스트용 샘플 액션 생성"""
    base_actions = [
        LabeledAction(
            action="click",
            target="저장 버튼",
            context="App",
            description="파일 저장",
        ),
        LabeledAction(
            action="click",
            target="확인 버튼",
            context="App",
            description="확인",
        ),
    ]

    actions = []
    for i in range(count):
        base = base_actions[i % len(base_actions)]
        actions.append(
            LabeledAction(
                action=base.action,
                target=base.target,
                context=base.context,
                description=base.description,
            )
        )
    return actions
