"""명세서 빌더 및 저장소

패턴과 HITL 응답을 기반으로 명세서를 구축하고 저장합니다.
"""

import json
import uuid
from pathlib import Path
from typing import Any

from shadow.hitl.models import Question, Response
from shadow.patterns.models import DetectedPattern
from shadow.spec.models import DecisionRule, Spec, SpecMeta, WorkflowStep


class SpecBuilder:
    """명세서 빌더

    패턴과 HITL 응답을 수집하여 명세서를 구축합니다.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Args:
            name: 명세서 이름
            description: 명세서 설명
        """
        self._name = name
        self._description = description
        self._patterns: list[DetectedPattern] = []
        self._responses: list[tuple[Question, Response]] = []
        self._workflow_steps: list[WorkflowStep] = []
        self._decision_rules: list[DecisionRule] = []
        self._source_sessions: list[str] = []

    def add_pattern(self, pattern: DetectedPattern) -> "SpecBuilder":
        """패턴 추가

        Args:
            pattern: 추가할 패턴

        Returns:
            self (메서드 체이닝용)
        """
        self._patterns.append(pattern)
        return self

    def add_response(self, question: Question, response: Response) -> "SpecBuilder":
        """HITL 응답 추가

        Args:
            question: 질문
            response: 응답

        Returns:
            self (메서드 체이닝용)
        """
        self._responses.append((question, response))
        return self

    def add_session(self, session_id: str) -> "SpecBuilder":
        """소스 세션 추가

        Args:
            session_id: 세션 ID

        Returns:
            self (메서드 체이닝용)
        """
        self._source_sessions.append(session_id)
        return self

    def build(self) -> Spec:
        """명세서 빌드

        Returns:
            구축된 명세서
        """
        # 패턴에서 워크플로우 단계 생성
        self._build_workflow_from_patterns()

        # HITL 응답에서 의사결정 규칙 생성
        self._build_rules_from_responses()

        # 메타데이터 생성
        meta = SpecMeta(
            name=self._name,
            description=self._description,
            source_sessions=self._source_sessions,
        )

        # 원본 패턴 데이터
        raw_patterns = [self._pattern_to_dict(p) for p in self._patterns]

        return Spec(
            meta=meta,
            workflow=self._workflow_steps,
            decisions=self._decision_rules,
            raw_patterns=raw_patterns,
        )

    def _build_workflow_from_patterns(self) -> None:
        """패턴에서 워크플로우 단계 생성"""
        self._workflow_steps = []
        order = 1

        for pattern in self._patterns:
            for action in pattern.actions:
                step = WorkflowStep(
                    order=order,
                    action=action.action,
                    target=action.target,
                    context=action.context,
                    description=action.description,
                )
                self._workflow_steps.append(step)
                order += 1

    def _build_rules_from_responses(self) -> None:
        """HITL 응답에서 의사결정 규칙 생성"""
        self._decision_rules = []

        for question, response in self._responses:
            rule = self._response_to_rule(question, response)
            if rule:
                self._decision_rules.append(rule)

    def _response_to_rule(self, question: Question, response: Response) -> DecisionRule | None:
        """응답을 의사결정 규칙으로 변환"""
        # 응답 값에서 규칙 추출
        value = response.selected_value

        # 확인 응답인 경우
        if value.get("confirmed") is True:
            return DecisionRule(
                id=str(uuid.uuid4()),
                condition="항상",
                action="패턴대로 실행",
                confirmed_by=question.id,
            )

        # 조건부 응답인 경우
        if "condition" in value:
            condition_type = value.get("condition", "unknown")
            return DecisionRule(
                id=str(uuid.uuid4()),
                condition=f"조건: {condition_type}",
                action="조건에 따라 실행",
                confirmed_by=question.id,
            )

        # 품질 기준 응답인 경우
        if "quality" in value:
            quality_type = value.get("quality", "unknown")
            return DecisionRule(
                id=str(uuid.uuid4()),
                condition=f"품질 기준: {quality_type}",
                action=f"{quality_type} 기준 적용",
                confirmed_by=question.id,
            )

        return None

    def _pattern_to_dict(self, pattern: DetectedPattern) -> dict[str, Any]:
        """패턴을 딕셔너리로 변환"""
        return {
            "pattern_id": pattern.pattern_id,
            "count": pattern.count,
            "confidence": pattern.confidence,
            "actions": [
                {
                    "action": a.action,
                    "target": a.target,
                    "context": a.context,
                    "description": a.description,
                }
                for a in pattern.actions
            ],
            "uncertainties": [u.to_dict() for u in pattern.uncertainties],
        }


class SpecStorage:
    """명세서 저장소

    명세서를 JSON 파일로 저장하고 로드합니다.
    """

    def __init__(self, base_dir: str | Path = "specs"):
        """
        Args:
            base_dir: 저장 기본 디렉토리
        """
        self._base_dir = Path(base_dir)

    def save(self, spec: Spec, filename: str = "spec.json") -> Path:
        """명세서 저장

        Args:
            spec: 저장할 명세서
            filename: 파일 이름 (기본: spec.json)

        Returns:
            저장된 파일 경로
        """
        self._base_dir.mkdir(parents=True, exist_ok=True)
        filepath = self._base_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(spec.to_dict(), f, indent=2, ensure_ascii=False)

        return filepath

    def load(self, filename: str = "spec.json") -> Spec:
        """명세서 로드

        Args:
            filename: 파일 이름

        Returns:
            로드된 명세서

        Raises:
            FileNotFoundError: 파일이 없는 경우
        """
        filepath = self._base_dir / filename

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        return Spec.from_dict(data)

    def list_specs(self) -> list[str]:
        """저장된 명세서 목록 반환

        Returns:
            명세서 파일명 목록
        """
        if not self._base_dir.exists():
            return []
        return [f.name for f in self._base_dir.glob("*.json")]

    def exists(self, filename: str = "spec.json") -> bool:
        """명세서 존재 여부 확인

        Args:
            filename: 파일 이름

        Returns:
            존재 여부
        """
        return (self._base_dir / filename).exists()
