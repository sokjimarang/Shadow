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
> **참고**: 이 문서에 명시되지 않은 기본 작성규칙(코드 작성 원칙, 플랜 수립, 에이전트 활용, 문제 해결 등)은 전역 CLAUDE.md (`~/.claude/CLAUDE.md`)를 참조하세요.

## 개발 규칙

### Database 스키마 참조

Database 관련 참조가 필요할 때는 [shadow-web 레포지토리](https://github.com/sokjimarang/shadow-web)의 스키마 migration 파일을 참조합니다.

### 문서 폴더 구조

```
docs/
├── direction/     # 기획 메인 파일 (PRD, Service Plan 등)
├── plan/          # Claude plan mode로 생성된 계획안
└── report/        # 구현 상태, 문제 상황 등 리포트
```

> **규칙**: 새 문서 생성 시 위 분류에 맞는 폴더에 저장할 것

<!-- DOCS_LIST_START -->
### 문서 목록

#### direction (기획)
- `docs/direction/agent_specification_shcema.md`
- `docs/direction/api_specifcation.md`
- `docs/direction/data_schema.md`
- `docs/direction/main_service-plan-v1.2.md`
- `docs/direction/prd.md`

#### plan (계획안)
- `docs/plan/plan-nemotron-vl.md`

#### report (리포트)
- `docs/report/implementation_status.md`
- `docs/report/p0_gap_report.md`
<!-- DOCS_LIST_END -->

### 기능 구현 시 참조 문서

기능 구현 시 다음 문서를 참조하여 스펙이 맞는지 확인하고 구현합니다:

- **PRD 문서**: `docs/direction/prd.md` - 제품 요구사항 및 기능 정의
- **Service Plan 문서**: `docs/direction/main_service-plan-v1.2.md` - 서비스 아키텍처 및 구현 계획

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
- 새로운 모듈/클래스 추가 시 CLAUDE.md 업데이트
- **작업 완료 시 `docs/report/implementation_status.md` 업데이트 필수** (PRD 기반 구현 현황 추적)

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
## 구현된 기능 (PRD 기준)

- [x] F-01: 화면 캡처 (mss)
- [x] F-02: 마우스 이벤트 캡처 (pynput)
- [x] F-03: 활성 윈도우 정보 (PyObjC + AppKit)
- [ ] F-04: 행동 라벨링 (VLM)
- [ ] F-05: 패턴 감지 (LLM)
- [ ] F-06: HITL 질문 생성
- [ ] F-07: Slack 메시지 송신
- [ ] F-08: Slack 응답 수신
- [ ] F-09: 명세서 생성
- [ ] F-10: CLI 시작/중지

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
