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

Database 관련 참조가 필요할 때는 다음 파일을 참조합니다:

- **Data Schema**: `docs/direction/data_schema.md` - 엔티티 정의 및 관계도
- **Migration 파일**: `supabase/migrations/*.sql` - 실제 DB 스키마 정의
- **Migration 가이드**: `docs/database/migration-guide.md` - 마이그레이션 관리 방법
- **DB 관리 명령어**: `Makefile` - db-start, db-push 등 명령어 정의

### Database Migration 규칙 (필수 준수)

> ⚠️ **중요**: 신규 테이블 생성 또는 스키마 업데이트 시 반드시 아래 절차를 따를 것

#### 1. Migration 파일 생성

```bash
# Makefile 명령어로 마이그레이션 생성
make db-migration-new
# 프롬프트에서 마이그레이션 이름 입력 (예: add_labeled_actions_table)
```

생성 위치: `supabase/migrations/YYYYMMDDHHMMSS_<name>.sql`

#### 2. SQL 스키마 작성

- **data_schema.md를 기준으로 작성** - 엔티티 정의와 일치해야 함
- **UUID 함수**: `gen_random_uuid()` 사용 (PostgreSQL 13+)
- **Timestamp**: `TIMESTAMPTZ` 타입 사용
- **JSON 필드**: `JSONB` 타입 사용 (검색 가능)
- **인덱스**: 자주 조회하는 컬럼에 생성
- **⚠️ 인코딩 규칙**:
  - **주석은 영문만 사용** (한글 주석 금지 - UTF-8 인코딩 이슈 방지)
  - Migration 파일 작성 시 `cat > file.sql << 'EOF'` 방식 권장 (Write 도구 대신)
  - 파일 인코딩: UTF-8 without BOM

예시:
```sql
-- LabeledAction 테이블 생성
CREATE TABLE labeled_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_id UUID REFERENCES observations(id) ON DELETE CASCADE,
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  timestamp TIMESTAMPTZ NOT NULL,
  action_type TEXT NOT NULL,
  target_element TEXT NOT NULL,
  app TEXT NOT NULL,
  app_context TEXT,
  semantic_label TEXT NOT NULL,
  intent_guess TEXT,
  confidence NUMERIC NOT NULL DEFAULT 1.0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX labeled_actions_session_id_idx ON labeled_actions(session_id);
CREATE INDEX labeled_actions_timestamp_idx ON labeled_actions(timestamp);
```

#### 3. 프로덕션 배포

```bash
# 프로덕션 DB에 마이그레이션 적용
make db-push
```

#### 4. Git 커밋

```bash
# 마이그레이션 파일을 git에 커밋
git add supabase/migrations/
git commit -m "feat: add labeled_actions table migration"
```

#### 5. Repository 레이어 구현

마이그레이션 배포 후 해당 테이블의 Repository 클래스 구현:
- 위치: `shadow/api/repositories/<entity_name>.py`
- 기존 패턴 참조: `shadow/api/repositories/sessions.py`
- 에러 핸들링: `ShadowAPIError` + `ErrorCode` 사용

#### Migration 체크리스트

- [ ] `make db-migration-new`로 마이그레이션 파일 생성
- [ ] `data_schema.md` 기준으로 SQL 작성
- [ ] `gen_random_uuid()` 사용 (UUID 필드)
- [ ] 필요한 인덱스 생성
- [ ] `make db-push`로 프로덕션 배포
- [ ] Migration 파일 git 커밋
- [ ] Repository 클래스 구현
- [ ] 통합 테스트 작성 (`tests/test_supabase_integration.py`)

#### 트러블슈팅

```bash
# 마이그레이션 상태 확인
make db-migration-list

# 로컬-프로덕션 차이 확인
make db-diff

# 프로덕션 스키마 가져오기
make db-pull
```

자세한 내용: `docs/database/migration-guide.md`

### 문서 폴더 구조

```
docs/
├── direction/     # 기획 메인 파일 (PRD, Service Plan 등)
├── scenario/      # 유저 시나리오 (구체화된 사용 사례)
├── plan/          # Claude plan mode로 생성된 계획안
├── report/        # 구현 상태, 문제 상황 등 리포트
└── database/      # 데이터베이스 관련 문서
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

#### scenario (유저 시나리오)
- `docs/scenario/scenario-01-pm-slack-response.md`
- `docs/scenario/scenario-02-hr-form-management.md`
- `docs/scenario/scenario-03-marketer-ads-automation.md`

#### plan (계획안)
- `docs/plan/plan-nemotron-vl.md`

#### report (리포트)
- `docs/report/implementation_status.md`
- `docs/report/p0_gap_report.md`

#### database (데이터베이스)
- `docs/database/migration-guide.md`
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
# AI API Keys
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Supabase (shadow-web과 동일한 DB 사용)
SUPABASE_URL=https://ddntzfdetgcobzohimvm.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Slack Bot (shadow-web 연동)
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
```

**DB 관리 명령어** (Makefile 사용):
- `make db-start` - 로컬 Supabase 시작
- `make db-migration-new` - 새 마이그레이션 생성
- `make db-push` - 프로덕션에 배포

자세한 내용: `docs/database/migration-guide.md`
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
