"""시퀀스 유사도 계산 모듈"""

from Levenshtein import ratio as levenshtein_ratio

from shadow.analysis.gemini import ActionLabel


def action_sequence_similarity(
    seq1: list[ActionLabel], seq2: list[ActionLabel]
) -> float:
    """두 액션 시퀀스의 유사도 계산

    Levenshtein 거리 기반 유사도를 사용합니다.

    Args:
        seq1: 첫 번째 시퀀스
        seq2: 두 번째 시퀀스

    Returns:
        0.0 ~ 1.0 사이의 유사도 값
    """
    if not seq1 or not seq2:
        return 0.0

    # 액션을 문자열로 변환하여 비교
    str1 = "|".join(str(a) for a in seq1)
    str2 = "|".join(str(a) for a in seq2)

    return levenshtein_ratio(str1, str2)


def find_similar_subsequences(
    sequence: list[ActionLabel],
    min_length: int = 2,
    similarity_threshold: float = 0.8,
) -> list[tuple[int, int, int, int, float]]:
    """시퀀스 내에서 유사한 부분 시퀀스 쌍 찾기

    Args:
        sequence: 분석할 시퀀스
        min_length: 최소 부분 시퀀스 길이
        similarity_threshold: 유사도 임계값

    Returns:
        (start1, end1, start2, end2, similarity) 튜플 목록
    """
    n = len(sequence)
    similar_pairs = []

    # 슬라이딩 윈도우로 모든 부분 시퀀스 쌍 비교
    for length in range(min_length, n // 2 + 1):
        for i in range(n - length + 1):
            for j in range(i + length, n - length + 1):
                subseq1 = sequence[i : i + length]
                subseq2 = sequence[j : j + length]

                similarity = action_sequence_similarity(subseq1, subseq2)

                if similarity >= similarity_threshold:
                    similar_pairs.append((i, i + length, j, j + length, similarity))

    return similar_pairs


def exact_sequence_match(seq1: list[ActionLabel], seq2: list[ActionLabel]) -> bool:
    """두 시퀀스가 정확히 일치하는지 확인"""
    if len(seq1) != len(seq2):
        return False

    return all(a1 == a2 for a1, a2 in zip(seq1, seq2))
