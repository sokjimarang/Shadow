"""반복 패턴 감지 엔진"""

from dataclasses import dataclass

from shadow.analysis.gemini import ActionLabel
from shadow.config import settings
from shadow.patterns.similarity import exact_sequence_match


@dataclass
class Pattern:
    """감지된 반복 패턴"""

    actions: list[ActionLabel]  # 패턴을 구성하는 액션들
    occurrences: list[int]  # 패턴이 시작되는 인덱스들
    count: int  # 반복 횟수

    def __str__(self) -> str:
        action_str = " → ".join(str(a) for a in self.actions)
        return f"[{action_str}] x {self.count}회"


class PatternDetector:
    """액션 시퀀스에서 반복 패턴 감지"""

    def __init__(
        self,
        min_length: int | None = None,
        min_occurrences: int = 2,
        similarity_threshold: float | None = None,
    ):
        """
        Args:
            min_length: 최소 패턴 길이 (None이면 설정 사용)
            min_occurrences: 최소 반복 횟수
            similarity_threshold: 유사도 임계값 (None이면 설정 사용)
        """
        self._min_length = min_length or settings.pattern_min_length
        self._min_occurrences = min_occurrences
        self._similarity_threshold = (
            similarity_threshold or settings.pattern_similarity_threshold
        )

    def detect(self, actions: list[ActionLabel]) -> list[Pattern]:
        """액션 시퀀스에서 반복 패턴 감지

        Args:
            actions: 분석할 액션 시퀀스

        Returns:
            감지된 패턴 목록 (긴 패턴 우선, 중복 제거)
        """
        if len(actions) < self._min_length * self._min_occurrences:
            return []

        patterns = []
        used_positions: set[int] = set()  # 이미 패턴에 포함된 위치
        n = len(actions)

        # 가능한 패턴 길이 (긴 것부터)
        max_pattern_length = n // self._min_occurrences

        for length in range(max_pattern_length, self._min_length - 1, -1):
            for start in range(n - length + 1):
                # 이미 사용된 위치면 스킵
                if start in used_positions:
                    continue

                candidate = actions[start : start + length]
                occurrences = self._find_occurrences(
                    actions, candidate, start, used_positions
                )

                if len(occurrences) >= self._min_occurrences:
                    # 이미 포함된 패턴인지 확인
                    if not self._is_subpattern(candidate, patterns):
                        patterns.append(
                            Pattern(
                                actions=candidate,
                                occurrences=occurrences,
                                count=len(occurrences),
                            )
                        )
                        # 사용된 위치 기록
                        for occ in occurrences:
                            for i in range(length):
                                used_positions.add(occ + i)

        return patterns

    def _find_occurrences(
        self,
        actions: list[ActionLabel],
        pattern: list[ActionLabel],
        start_from: int,
        used_positions: set[int] | None = None,
    ) -> list[int]:
        """패턴이 나타나는 모든 위치 찾기"""
        used_positions = used_positions or set()
        occurrences = [start_from]
        n = len(actions)
        length = len(pattern)

        # start_from 이후 위치에서 검색
        i = start_from + length
        while i <= n - length:
            # 이미 사용된 위치면 스킵
            if i in used_positions:
                i += 1
                continue

            candidate = actions[i : i + length]
            if exact_sequence_match(pattern, candidate):
                occurrences.append(i)
                i += length  # 겹치지 않게 다음 위치로
            else:
                i += 1

        return occurrences

    def _is_subpattern(
        self, candidate: list[ActionLabel], existing_patterns: list[Pattern]
    ) -> bool:
        """후보 패턴이 기존 패턴의 부분 패턴인지 확인"""
        for pattern in existing_patterns:
            if len(candidate) < len(pattern.actions):
                # candidate가 pattern의 부분인지 확인
                for i in range(len(pattern.actions) - len(candidate) + 1):
                    if exact_sequence_match(
                        candidate, pattern.actions[i : i + len(candidate)]
                    ):
                        return True
        return False

    def detect_simple(self, actions: list[ActionLabel]) -> list[Pattern]:
        """단순 연속 반복 패턴 감지 (같은 액션이 연속으로 반복)

        Args:
            actions: 분석할 액션 시퀀스

        Returns:
            감지된 연속 반복 패턴 목록
        """
        if not actions:
            return []

        patterns = []
        i = 0

        while i < len(actions):
            current = actions[i]
            count = 1
            start_idx = i

            # 연속으로 같은 액션 카운트
            while i + count < len(actions) and actions[i + count] == current:
                count += 1

            if count >= self._min_occurrences:
                patterns.append(
                    Pattern(
                        actions=[current],
                        occurrences=list(range(start_idx, start_idx + count)),
                        count=count,
                    )
                )

            i += count

        return patterns
