"""HITL 질문 생성기

패턴의 불확실성(Uncertainty)에서 사용자 질문을 생성합니다.
"""

import uuid
from typing import Any

from shadow.hitl.models import Question, QuestionOption, QuestionType
from shadow.patterns.models import DetectedPattern, Uncertainty, UncertaintyType


class QuestionGenerator:
    """패턴의 불확실성에서 HITL 질문 생성

    P0: 가설검증(hypothesis), 품질확인(quality) 질문만 생성
    """

    def generate(self, pattern: DetectedPattern) -> list[Question]:
        """패턴에서 HITL 질문 목록 생성 (최소 2개 보장)

        Args:
            pattern: 분석된 패턴

        Returns:
            생성된 질문 목록 (최소 2개)
        """
        questions = []

        # 기본 가설 검증 질문은 항상 생성
        questions.append(self._create_default_hypothesis_question(pattern))

        # 불확실성 기반 질문 추가
        if pattern.uncertainties:
            for i, uncertainty in enumerate(pattern.uncertainties):
                question = self._create_question_from_uncertainty(pattern, uncertainty, i)
                if question:
                    questions.append(question)

        # 최소 2개 보장: 불확실성 질문이 없으면 조건 질문 추가
        if len(questions) < 2:
            questions.append(self._create_default_condition_question(pattern))

        return questions

    def _create_default_hypothesis_question(self, pattern: DetectedPattern) -> Question:
        """기본 가설 검증 질문 생성"""
        # 패턴 설명 구성
        action_descriptions = [
            f"{i+1}. {a.action} - {a.target}" for i, a in enumerate(pattern.actions)
        ]
        pattern_desc = "\n".join(action_descriptions)

        return Question(
            id=str(uuid.uuid4()),
            type=QuestionType.HYPOTHESIS,
            text=f"다음 작업 패턴이 올바르게 감지되었나요?\n\n{pattern_desc}",
            options=[
                QuestionOption(
                    id="yes",
                    text="예, 맞습니다",
                    value={"confirmed": True},
                ),
                QuestionOption(
                    id="partial",
                    text="부분적으로 맞습니다",
                    value={"confirmed": "partial", "needs_review": True},
                ),
                QuestionOption(
                    id="no",
                    text="아니오, 잘못되었습니다",
                    value={"confirmed": False, "needs_review": True},
                ),
            ],
            source_pattern_id=pattern.pattern_id,
            source_uncertainty_index=None,
        )

    def _create_default_condition_question(self, pattern: DetectedPattern) -> Question:
        """기본 조건 질문 생성 (최소 2개 질문 보장용)"""
        action_descriptions = [
            f"{i+1}. {a.action} - {a.target}" for i, a in enumerate(pattern.actions)
        ]
        pattern_desc = "\n".join(action_descriptions)

        return Question(
            id=str(uuid.uuid4()),
            type=QuestionType.CONDITION,
            text=f"이 작업은 어떤 조건에서 수행하나요?\n\n{pattern_desc}",
            options=[
                QuestionOption(
                    id="always",
                    text="항상 수행합니다",
                    value={"condition": "always"},
                ),
                QuestionOption(
                    id="specific",
                    text="특정 조건에서만 수행합니다",
                    value={"condition": "specific", "needs_detail": True},
                ),
                QuestionOption(
                    id="depends",
                    text="상황에 따라 다릅니다",
                    value={"condition": "variable"},
                ),
            ],
            source_pattern_id=pattern.pattern_id,
            source_uncertainty_index=None,
        )

    def _create_question_from_uncertainty(
        self, pattern: DetectedPattern, uncertainty: Uncertainty, index: int
    ) -> Question | None:
        """불확실성에서 질문 생성"""
        if uncertainty.type == UncertaintyType.CONDITION:
            return self._create_condition_question(pattern, uncertainty, index)
        elif uncertainty.type == UncertaintyType.QUALITY:
            return self._create_quality_question(pattern, uncertainty, index)
        elif uncertainty.type == UncertaintyType.VARIANT:
            return self._create_variant_question(pattern, uncertainty, index)
        elif uncertainty.type == UncertaintyType.SEQUENCE:
            return self._create_sequence_question(pattern, uncertainty, index)
        elif uncertainty.type == UncertaintyType.OPTIONAL:
            return self._create_optional_question(pattern, uncertainty, index)
        return None

    def _create_condition_question(
        self, pattern: DetectedPattern, uncertainty: Uncertainty, index: int
    ) -> Question:
        """조건 불확실성에서 질문 생성"""
        return Question(
            id=str(uuid.uuid4()),
            type=QuestionType.CONDITION,
            text=f"이 작업은 어떤 조건에서 수행하나요?\n\n{uncertainty.description}",
            options=[
                QuestionOption(
                    id="always",
                    text="항상 수행합니다",
                    value={"condition": "always"},
                ),
                QuestionOption(
                    id="specific",
                    text="특정 조건에서만 수행합니다",
                    value={"condition": "specific", "needs_detail": True},
                ),
                QuestionOption(
                    id="depends",
                    text="상황에 따라 다릅니다",
                    value={"condition": "variable"},
                ),
            ],
            source_pattern_id=pattern.pattern_id,
            source_uncertainty_index=index,
            metadata={"uncertainty": uncertainty.to_dict()},
        )

    def _create_quality_question(
        self, pattern: DetectedPattern, uncertainty: Uncertainty, index: int
    ) -> Question:
        """품질 불확실성에서 질문 생성"""
        return Question(
            id=str(uuid.uuid4()),
            type=QuestionType.QUALITY,
            text=f"이 작업의 결과물 품질 기준은 무엇인가요?\n\n{uncertainty.description}",
            options=[
                QuestionOption(
                    id="exact",
                    text="정확히 일치해야 합니다",
                    value={"quality": "exact"},
                ),
                QuestionOption(
                    id="similar",
                    text="유사하면 됩니다",
                    value={"quality": "similar"},
                ),
                QuestionOption(
                    id="flexible",
                    text="기본 요구사항만 충족하면 됩니다",
                    value={"quality": "flexible"},
                ),
            ],
            source_pattern_id=pattern.pattern_id,
            source_uncertainty_index=index,
            metadata={"uncertainty": uncertainty.to_dict()},
        )

    def _create_variant_question(
        self, pattern: DetectedPattern, uncertainty: Uncertainty, index: int
    ) -> Question:
        """변형 불확실성에서 질문 생성"""
        return Question(
            id=str(uuid.uuid4()),
            type=QuestionType.VARIANT,
            text=f"이 작업에 다른 방법도 있나요?\n\n{uncertainty.description}",
            options=[
                QuestionOption(
                    id="only",
                    text="이 방법만 사용합니다",
                    value={"variant": "single"},
                ),
                QuestionOption(
                    id="multiple",
                    text="다른 방법도 있습니다",
                    value={"variant": "multiple", "needs_detail": True},
                ),
                QuestionOption(
                    id="preferred",
                    text="이 방법이 선호되지만 다른 방법도 허용됩니다",
                    value={"variant": "preferred"},
                ),
            ],
            source_pattern_id=pattern.pattern_id,
            source_uncertainty_index=index,
            metadata={"uncertainty": uncertainty.to_dict()},
        )

    def _create_sequence_question(
        self, pattern: DetectedPattern, uncertainty: Uncertainty, index: int
    ) -> Question:
        """순서 불확실성에서 질문 생성"""
        return Question(
            id=str(uuid.uuid4()),
            type=QuestionType.HYPOTHESIS,
            text=f"이 작업들의 순서가 중요한가요?\n\n{uncertainty.description}",
            options=[
                QuestionOption(
                    id="strict",
                    text="순서를 반드시 지켜야 합니다",
                    value={"sequence": "strict"},
                ),
                QuestionOption(
                    id="flexible",
                    text="순서가 바뀌어도 됩니다",
                    value={"sequence": "flexible"},
                ),
                QuestionOption(
                    id="partial",
                    text="일부만 순서가 중요합니다",
                    value={"sequence": "partial", "needs_detail": True},
                ),
            ],
            source_pattern_id=pattern.pattern_id,
            source_uncertainty_index=index,
            metadata={"uncertainty": uncertainty.to_dict()},
        )

    def _create_optional_question(
        self, pattern: DetectedPattern, uncertainty: Uncertainty, index: int
    ) -> Question:
        """선택적 단계 불확실성에서 질문 생성"""
        return Question(
            id=str(uuid.uuid4()),
            type=QuestionType.HYPOTHESIS,
            text=f"이 단계는 필수인가요?\n\n{uncertainty.description}",
            options=[
                QuestionOption(
                    id="required",
                    text="필수 단계입니다",
                    value={"optional": False},
                ),
                QuestionOption(
                    id="optional",
                    text="선택적 단계입니다",
                    value={"optional": True},
                ),
                QuestionOption(
                    id="conditional",
                    text="조건부로 필요합니다",
                    value={"optional": "conditional", "needs_detail": True},
                ),
            ],
            source_pattern_id=pattern.pattern_id,
            source_uncertainty_index=index,
            metadata={"uncertainty": uncertainty.to_dict()},
        )

    def generate_from_patterns(self, patterns: list[DetectedPattern]) -> list[Question]:
        """여러 패턴에서 질문 목록 생성

        Args:
            patterns: 분석된 패턴 목록

        Returns:
            생성된 모든 질문 목록
        """
        all_questions = []
        for pattern in patterns:
            all_questions.extend(self.generate(pattern))
        return all_questions
