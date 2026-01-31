# Shadow 구현 현황

**마지막 업데이트: 2026-02-01**

이 문서는 PRD(docs/prd.md) 기반으로 현재 구현 상황을 추적합니다.

---

## 요약

| 구분 | 완료 | 부분 | 미완료 | 비율 |
|------|------|------|--------|------|
| P0 기능 (10개) | 8 | 0 | 2 | 80% |
| 테스트케이스 (9개) | 6 | 1 | 2 | 67% |

---

## P0 기능 구현 현황

| ID | 기능 | 상태 | 파일 | 비고 |
|----|------|------|------|------|
| F-01 | 화면 캡처 | ✅ 완료 | `shadow/capture/screen.py`, `recorder.py` | MSS 기반 Before/After 캡처 |
| F-02 | 마우스 이벤트 캡처 | ✅ 완료 | `shadow/capture/input_events.py` | pynput 기반, 클릭/스크롤 수집 |
| F-03 | 활성 윈도우 정보 | ✅ 완료 | `shadow/capture/window.py` | macOS PyObjC 사용 (macOS 전용) |
| F-04 | 행동 라벨링 (VLM) | ✅ 완료 | `shadow/analysis/claude.py` | Before/After 비교 분석, 테스트 완료 |
| F-05 | 패턴 감지 (LLM) | ✅ 완료 | `shadow/patterns/analyzer/claude.py` | LLM 기반 패턴+불확실성 감지 |
| F-06 | HITL 질문 생성 | ✅ 완료 | `shadow/hitl/generator.py` | 가설검증/품질확인 질문 |
| F-07 | Slack 메시지 송신 | ✅ 완료 | `shadow/slack/client.py` | Block Kit UI 전송 |
| F-08 | Slack 응답 수신 | ❌ 미구현 | - | 버튼 클릭 이벤트 핸들러 필요 |
| F-09 | 명세서 생성 | ✅ 완료 | `shadow/spec/builder.py` | spec.json 저장 |
| F-10 | CLI 시작/중지 | ✅ 완료 | `shadow/cli.py` | start, stop, mock-e2e 명령 |

---

## 테스트케이스 현황

| ID | 테스트 항목 | 상태 | Pass 조건 | 비고 |
|----|------------|------|----------|------|
| TC-01 | 화면 캡처 | ✅ Pass | Before/After 스크린샷 저장 | |
| TC-02 | 행동 라벨링 | ✅ Pass | semantic_label 생성 | Claude 지원, E2E 테스트 완료 |
| TC-03 | 패턴 감지 | ✅ Pass | 패턴 후보 생성 + 불확실성 포함 | LLM 기반 구현 완료 |
| TC-04 | 질문 생성 | ✅ Pass | 2개 이상 질문 생성 | |
| TC-05 | Slack 전송 | ✅ Pass | 메시지 ts 반환 | |
| TC-06 | Slack 응답 | ❌ Fail | selected_option_id 획득 | 응답 수신 미구현 |
| TC-07 | 명세서 생성 | ✅ Pass | spec.json 생성 | |
| TC-08 | E2E 플로우 | ⚠️ 부분 | 전체 사이클 완료 | mock-e2e만 가능, 실제 Slack 연동 미완료 |
| TC-09 | 재질문 방지 | ❌ Fail | 동일 질문 미발생 | P1 기능, 미구현 |

---

## 모듈별 구현 상세

### capture/ (화면 캡처)
- `screen.py`: MSS 기반 화면 캡처 ✅
- `input_events.py`: pynput 마우스/키보드 이벤트 ✅
- `window.py`: macOS 활성 윈도우 정보 ✅ (macOS 전용)
- `recorder.py`: 캡처 + 이벤트 동기화 ✅
- `storage.py`: 세션 저장 ✅
- `models.py`: Frame, InputEvent, KeyframePair ✅

### preprocessing/ (키프레임 추출)
- `keyframe.py`: 클릭 전후 키프레임 쌍 추출 ✅

### analysis/ (VLM 분석)
- `claude.py`: Claude 분석기 ✅ (**배치 모드 추가**, 22~28% 비용 절감, 57~67% 시간 단축)
- `base.py`: 분석기 추상 베이스 ✅
- `models.py`: LabeledAction, SessionSequence ✅
- `tests/test_analysis.py`: 단위/통합 테스트 ✅ (배치 파싱 테스트 포함)

### patterns/ (패턴 감지)
- `models.py`: DetectedPattern, Uncertainty ✅
- `analyzer/base.py`: 패턴 분석기 추상 베이스 ✅
- `analyzer/claude.py`: Claude 기반 패턴+불확실성 분석 ✅
- `tests/patterns/test_analyzer.py`: 단위 테스트 ✅ (22개 테스트)

### hitl/ (Human-in-the-Loop)
- `generator.py`: 질문 생성기 ✅
- `models.py`: Question, Response ✅
- **미구현**: 응답 처리 및 학습 로직 ❌

### slack/ (Slack 연동)
- `client.py`: Block Kit 메시지 전송 ✅
- `models.py`: SlackMessage ✅
- **미구현**: Interactive 응답 핸들러 ❌

### spec/ (명세서)
- `builder.py`: 패턴→명세서 변환 ✅
- `models.py`: Spec, DecisionRule ✅

---

## 남은 작업

### 우선순위 높음 (E2E 필수)
1. **F-08 Slack 응답 수신**: Slack Interactive Components 핸들러 구현

### 우선순위 중간
2. TC-08 실제 E2E 테스트 검증
3. 에러 처리 및 재시도 로직

### 우선순위 낮음 (P1)
4. TC-09 재질문 방지 로직
5. CLI status 명령

---

## 인프라 구축 현황

### 데이터베이스 Migration 시스템
- ✅ **Supabase CLI 환경 구축** (2026-01-31)
  - shadow-web에서 shadow-py로 migration 파일 이동 완료
  - `supabase/migrations/` 폴더에 **9개 migration 파일** 관리
    - 기존 3개 (sessions, hitl_questions/answers, agent_specs/histories)
    - 신규 6개 (raw data, analysis, pattern, hitl interpreted, system layers)
  - `Makefile`로 DB 관리 명령어 구축 (db-start, db-push, db-migration-new 등)
  - `docs/database/migration-guide.md` 작성 (Python 환경 가이드)
  - Supabase 프로덕션 DB 연결 완료 (project-ref: ddntzfdetgcobzohimvm)

### Repository 레이어 구현
- ✅ **데이터 접근 레이어 완성** (2026-01-31)
  - **System Layer**: UserRepository, ConfigRepository ✅
  - **Raw Data Layer**: ObservationRepository (기존) ✅
  - **Analysis Layer**: LabeledActionRepository, SessionSequenceRepository ✅
  - **Pattern Layer**: DetectedPatternRepository ✅
  - **HITL Layer**: HITLRepository (기존), InterpretedAnswerRepository ✅
  - **Spec Layer**: SpecRepository (기존) ✅
  - 통합 테스트 작성 완료 (`tests/test_supabase_integration.py`)
  - 총 9개 테이블에 대한 Repository 구현 완료

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-31 | 초기 구현 현황 문서 작성 |
| 2026-01-31 | DB migration 시스템 구축 완료 (shadow-web → shadow-py 이동) |
| 2026-01-31 | Repository 레이어 완성 (6개 신규 migration + 5개 신규 Repository 구현) |
| 2026-01-31 | F-04 완성: Claude 타임아웃/로깅 추가, 테스트 작성 |
| 2026-02-01 | F-05 완성: LLM 기반 패턴 분석기 구현 (ClaudePatternAnalyzer) |
| 2026-02-01 | F-04 최적화: 배치 분석 모드 추가 (비용 28% 절감, 시간 67% 단축) |
