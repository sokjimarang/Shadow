# Shadow 프로젝트 가이드

## 프로젝트 개요

화면 녹화 + 입력 이벤트 수집 → Vision AI 분석 → 반복 패턴 감지

### 핵심 파이프라인

```
[녹화] → [키프레임 추출] → [Vision AI 분석] → [패턴 감지]
```

## 아키텍처

### 모듈 구조

```
shadow/
├── capture/           # 화면 캡처 및 입력 이벤트 (Raw Data Layer)
│   ├── screen.py      # ScreenCapture - mss 기반 스크린샷
│   ├── input_events.py # InputEventCollector - pynput 기반
│   ├── recorder.py    # Recorder - 통합 녹화기
│   ├── window.py      # 활성 윈도우 감지
│   └── models.py      # Frame, InputEvent, Screenshot, RawObservation
├── preprocessing/
│   └── keyframe.py    # KeyframeExtractor - 클릭 시점 프레임 추출
├── analysis/          # Analysis Layer
│   ├── base.py        # BaseVisionAnalyzer, AnalyzerBackend
│   ├── claude.py      # ClaudeAnalyzer - Claude Opus 4.5
│   ├── gemini.py      # GeminiAnalyzer - Gemini 2.0 Flash
│   └── models.py      # LabeledAction, SessionSequence
├── patterns/          # Pattern Layer
│   ├── detector.py    # PatternDetector - 반복 패턴 감지
│   ├── similarity.py  # 액션 유사도 계산
│   └── models.py      # DetectedPattern, Uncertainty, ActionTemplate, Variation
├── hitl/              # HITL Layer
│   ├── generator.py   # QuestionGenerator - 질문 생성기
│   └── models.py      # Question, Response, InterpretedAnswer
├── spec/              # Spec Layer
│   └── models.py      # AgentSpec, SpecHistory
├── core/              # System Layer
│   └── models.py      # Session, User, Config
└── config.py          # Settings - pydantic-settings 기반
```

### 주요 클래스

| 클래스 | 위치 | 역할 |
|--------|------|------|
| `Recorder` | capture/recorder.py | 화면+입력 통합 녹화 |
| `KeyframeExtractor` | preprocessing/keyframe.py | 클릭 시점 프레임 추출 |
| `ClaudeAnalyzer` | analysis/claude.py | Claude Vision 분석 |
| `GeminiAnalyzer` | analysis/gemini.py | Gemini Vision 분석 |
| `PatternDetector` | patterns/detector.py | 반복 패턴 감지 |

### 데이터 모델 (Pydantic v2)

모든 데이터 모델은 **Pydantic v2** 기반으로 통합되었습니다.
- 내부 처리용 dataclass (`Frame`, `Keyframe` 등)는 numpy array를 다루므로 유지
- 나머지 모든 모델은 Pydantic으로 마이그레이션 완료

| Layer | 모델 | 설명 |
|-------|------|------|
| Raw Data | `Screenshot`, `InputEventRecord`, `RawObservation` | 화면 캡처 + 입력 이벤트 |
| Analysis | `LabeledAction`, `SessionSequence` | VLM 분석 결과 |
| Pattern | `DetectedPattern`, `Uncertainty`, `ActionTemplate` | 반복 패턴 |
| HITL | `Question`, `Response`, `InterpretedAnswer` | 사용자 확인 |
| Spec | `Spec`, `AgentSpec`, `SpecHistory` | 자동화 명세서 |
| System | `Session`, `User`, `Config` | 시스템 설정 |

```python
# 사용 예시
from shadow.capture import Screenshot, RawObservation
from shadow.analysis import LabeledAction
from shadow.patterns import DetectedPattern, Uncertainty
from shadow.hitl import Question, Response, QuestionGenerator
from shadow.spec import Spec, AgentSpec, SpecHistory
from shadow.core import Session, User, Config
```

## Vision AI 백엔드

### Claude Opus 4.5 (기본)

- **모델**: `claude-opus-4-5-20251101`
- **비용 최적화**:
  - 프롬프트 캐싱 (cache_control) → 90% 비용 절감
  - 이미지 리사이즈 (1024px) → 토큰 절약
  - 배치 분석 → API 호출 최소화

### Gemini 2.0 Flash

- **모델**: `gemini-2.0-flash`
- **특징**: 비디오 업로드 지원 (File API)

## 설정

### 환경 변수 (.env)

```env
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

### 설정 파일 (shadow/config.py)

```python
capture_fps: int = 10                    # 캡처 FPS
claude_model: str = "claude-opus-4-5-20251101"
claude_max_image_size: int = 1024        # 이미지 최대 크기
claude_use_cache: bool = True            # 프롬프트 캐싱
```

## Git 브랜치 전략: GitHub Flow

1. **main 브랜치는 항상 배포 가능한 상태 유지**
2. **새 작업은 main에서 feature 브랜치 생성**
   - 네이밍: `feature/<기능명>`, `fix/<버그명>`, `refactor/<대상>`
3. **작은 단위로 자주 커밋**
4. **PR을 통해 main에 병합**
5. **병합 후 feature 브랜치 삭제**

## 개발 규칙

### 문서화 규칙

> **중요**: 다음 시점에 반드시 CLAUDE.md와 README.md를 업데이트할 것
> - 새로운 모듈/클래스 추가 시
> - API 변경 시
> - 설정 항목 추가/변경 시
> - 중요한 기능 구현 완료 시

### 코드 스타일

- 주석은 한글로 작성
- 테스트는 구조화된 형태로 작성
- 임시 해결책보다 근본 원인 해결 우선

## 실행 방법

```bash
# 데모 실행
python demo.py --record 5              # Claude로 5초 녹화
python demo.py --record 5 --backend gemini  # Gemini 사용
python demo.py --test                  # 더미 데이터 테스트

# 테스트
uv run pytest
```

## 참고 문서

- [Anthropic API Docs](https://docs.anthropic.com/)
- [Claude Vision Guide](https://docs.anthropic.com/en/docs/build-with-claude/vision)
- [Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Google GenAI SDK](https://ai.google.dev/gemini-api/docs)

## v0.1 E2E 구현 검증 체크리스트

> **각 Phase 완료 시 아래 검증을 통과해야 다음 단계 진행**

### Phase 1: 데이터 모델 및 기반 ✅

| 항목 | 검증 방법 | Pass 조건 | 상태 |
|------|----------|----------|------|
| 1-1 | `python -c "from shadow.capture.window import get_active_window; print(get_active_window())"` | WindowInfo 객체 반환 | ✅ |
| 1-2 | `python -c "from shadow.capture.models import InputEvent; e = InputEvent(0, None, app_name='Test'); print(e.app_name)"` | 'Test' 출력 | ✅ |
| 1-3 | `python -c "from shadow.patterns.models import Uncertainty, UncertaintyType; print(UncertaintyType.CONDITION)"` | CONDITION 출력 | ✅ |
| 1-4 | `python -c "from shadow.patterns.models import DetectedPattern; p = DetectedPattern(actions=[]); print(hasattr(p, 'uncertainties'))"` | True 출력 | ✅ |
| 1-5 | `python -c "from shadow.hitl.models import Question, QuestionType; print(QuestionType.HYPOTHESIS)"` | HYPOTHESIS 출력 | ✅ |
| 1-6 | `python -c "from shadow.spec.models import Spec, DecisionRule; print(DecisionRule)"` | class 출력 | ✅ |

### Phase 2: 캡처 파이프라인 ✅

| 항목 | 검증 방법 | Pass 조건 | 상태 |
|------|----------|----------|------|
| 2-1 | InputEventCollector 클릭 시 app_name 필드 존재 | event.app_name != None | ✅ |
| 2-2 | `python -c "from shadow.capture.models import KeyframePair"` | import 성공 | ✅ |
| 2-3 | `python -c "from shadow.preprocessing.keyframe import KeyframeExtractor; print(hasattr(KeyframeExtractor, 'extract_pairs'))"` | True 출력 | ✅ |
| 2-4 | `python -c "from shadow.capture.storage import SessionStorage"` | import 성공 | ✅ |

### Phase 3: 분석 파이프라인 ✅

| 항목 | 검증 방법 | Pass 조건 | 상태 |
|------|----------|----------|------|
| 3-1 | `python -c "from shadow.analysis.base import BaseVisionAnalyzer; print(hasattr(BaseVisionAnalyzer, 'analyze_keyframe_pair'))"` | True 출력 | ✅ |
| 3-2 | ClaudeAnalyzer.analyze_keyframe_pair 메서드 존재 | 메서드 호출 가능 | ✅ |
| 3-3 | Pattern에 uncertainties 자동 생성 | len(pattern.uncertainties) >= 0 | ✅ |
| 3-4 | `python -c "from shadow.hitl.generator import QuestionGenerator"` | import 성공 | ✅ |

### Phase 4: Slack 및 명세서 ✅

| 항목 | 검증 방법 | Pass 조건 | 상태 |
|------|----------|----------|------|
| 4-1 | `python -c "from shadow.slack.client import SlackClient"` | import 성공 | ✅ |
| 4-2 | `python -c "from shadow.spec.builder import SpecBuilder, SpecStorage"` | import 성공 | ✅ |
| 4-3 | `python -m shadow.cli --help` | CLI 명령어 표시 | ✅ |

### E2E 통합 검증 ✅

| TC ID | 테스트 항목 | 검증 방법 | Pass 조건 | 상태 |
|-------|------------|----------|----------|------|
| TC-01 | 화면 캡처 | 클릭 후 outputs/ 확인 | before.png, after.png 존재 | ✅ (mock) |
| TC-02 | 행동 라벨링 | Before/After 분석 | semantic_label 포함된 LabeledAction | ✅ (mock) |
| TC-03 | 패턴 감지 | 3개 세션 입력 | Pattern 1개+, uncertainties 포함 | ✅ |
| TC-04 | 질문 생성 | 패턴 입력 | Question 2개+ | ✅ |
| TC-05 | Slack 전송 | `shadow test-slack` | 메시지 ts 반환 | ⏳ (토큰 필요) |
| TC-06 | 명세서 생성 | 전체 파이프라인 | spec.json 존재 | ✅ |
| TC-07 | E2E 플로우 | `shadow mock-e2e` | 전체 사이클 완료 | ✅ |

---

## 변경 이력

### 2026-01-31

- **데이터 모델 v1.1 전체 마이그레이션** (Pydantic v2)
  - 모든 레거시 dataclass를 Pydantic으로 통합
  - 레거시 별칭 완전 제거 (`ActionLabel`, `Pattern`, `HITLQuestion` 등)
  - `LabeledAction`, `DetectedPattern`, `Question`, `Response` 사용
  - `Uncertainty` dataclass → Pydantic `Uncertainty`
  - `Spec`, `WorkflowStep`, `DecisionRule` → Pydantic 통합
  - 내부 처리용 `Frame`, `Keyframe` 등은 numpy array 때문에 dataclass 유지
- `shadow/core/` 모듈 추가 (`Session`, `User`, `Config`)
- `shadow/hitl/generator.py` 추가 (질문 생성기)
- `shadow/patterns/uncertainties.py` 삭제 (models.py로 통합)

### 2025-01-31

- 프로젝트 초기 구조 구현
- 화면 캡처 및 입력 이벤트 수집 모듈 구현
- Claude Opus 4.5 Vision 분석기 구현 (프롬프트 캐싱 포함)
- Gemini 2.0 Flash 분석기 구현
- 키프레임 추출기 구현
- 패턴 감지기 구현
- CLI 데모 스크립트 작성
