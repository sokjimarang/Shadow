# Shadow 프로젝트 가이드

## 프로젝트 개요

화면 녹화 + 입력 이벤트 수집 → Vision AI 분석 → 반복 패턴 감지 → 자동화 명세서 생성

```
[녹화] → [키프레임 추출] → [Vision AI 분석] → [패턴 감지] → [HITL 질문] → [명세서]
```

## 모듈 구조

```
shadow/
├── capture/           # 화면 캡처 및 입력 이벤트
├── preprocessing/     # 키프레임 추출
├── analysis/          # Vision AI 분석 (Claude, Gemini)
├── patterns/          # 반복 패턴 감지
├── hitl/              # Human-in-the-Loop 질문 생성
├── spec/              # 자동화 명세서
├── slack/             # Slack 연동
├── core/              # 시스템 설정
└── config.py          # pydantic-settings 기반 설정
```

## 데이터 모델

모든 모델은 **Pydantic v2** 기반 (numpy array 처리용 dataclass 제외)

| Layer | 주요 모델 |
|-------|----------|
| Capture | `Screenshot`, `InputEventRecord`, `RawObservation` |
| Analysis | `LabeledAction`, `SessionSequence` |
| Pattern | `DetectedPattern`, `Uncertainty` |
| HITL | `Question`, `Response` |
| Spec | `Spec`, `AgentSpec` |

## 개발 규칙

- 주석은 한글로 작성
- 테스트는 구조화된 형태로 작성
- 임시 해결책보다 근본 원인 해결 우선
- 새로운 모듈/클래스 추가 시 CLAUDE.md 업데이트
- **작업 완료 시 `docs/implementation_status.md` 업데이트 필수** (PRD 기반 구현 현황 추적)

## 실행 방법

```bash
# 데모 실행
python demo.py --record 5              # Claude로 5초 녹화
python demo.py --record 5 --backend gemini  # Gemini 사용

# 테스트
uv run pytest
```

## 환경 변수

```env
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

---

## 코딩 가이드라인 (Karpathy)

### 1. 코딩 전 생각
- 가정을 명시하고, 불확실하면 질문
- 여러 해석이 가능하면 제시 (조용히 선택하지 말 것)
- 더 단순한 방법이 있으면 제안

### 2. 단순함 우선
- 요청받은 것만 구현, 추측성 기능 금지
- 단일 용도 코드에 추상화 금지
- 불가능한 시나리오에 에러 핸들링 금지

### 3. 최소 변경
- 인접 코드 "개선" 금지, 기존 스타일 유지
- 내 변경으로 생긴 미사용 코드만 삭제
- 모든 변경 라인은 요청에 직접 연결되어야 함

### 4. 목표 기반 실행
- 작업을 검증 가능한 목표로 변환
- 멀티스텝 작업은 계획 명시: `[Step] → verify: [check]`
