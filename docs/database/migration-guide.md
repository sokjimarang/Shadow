# Shadow - Database Migration Guide

이 가이드는 Supabase 데이터베이스 스키마를 관리하고 마이그레이션하는 방법을 설명합니다.

## 목차

1. [환경 설정](#환경-설정)
2. [현재 DB 스키마](#현재-db-스키마)
3. [마이그레이션 명령어](#마이그레이션-명령어)
4. [새로운 마이그레이션 만들기](#새로운-마이그레이션-만들기)
5. [프로덕션 배포 워크플로우](#프로덕션-배포-워크플로우)
6. [트러블슈팅](#트러블슈팅)

---

## 환경 설정

### 1. Supabase CLI 설치

```bash
# Homebrew (macOS)
brew install supabase/tap/supabase

# NPM
npm install -g supabase

# 설치 확인
supabase --version
```

### 2. 환경변수 설정

`.env.local` 파일 생성 (`.env.example` 참조):

```bash
cp .env.example .env.local
```

`.env.local`에 실제 값 입력:

```bash
# Supabase Configuration
SUPABASE_URL=https://ddntzfdetgcobzohimvm.supabase.co
SUPABASE_KEY=your_actual_supabase_anon_key_here

# Slack Bot Configuration
SLACK_BOT_TOKEN=your_actual_bot_token_here
SLACK_SIGNING_SECRET=your_actual_signing_secret_here
SLACK_APP_TOKEN=your_actual_app_token_here
```

**주의**: `.env.local`은 gitignore되어 있으므로 안전하게 실제 값을 저장할 수 있습니다.

---

## 현재 DB 스키마

Shadow는 다음 4개의 주요 테이블을 사용합니다:

### 1. `sessions` - 녹화 세션 정보

```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT,
  duration NUMERIC NOT NULL DEFAULT 0,
  frame_count INTEGER NOT NULL DEFAULT 0,
  event_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**용도**: shadow-py에서 녹화한 세션의 메타데이터 저장

### 2. `analysis_results` - AI 분석 결과

```sql
CREATE TABLE analysis_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  action_type TEXT NOT NULL,
  target TEXT NOT NULL,
  context TEXT,
  description TEXT,
  confidence NUMERIC,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**용도**: Claude/Gemini가 분석한 사용자 행동 저장

### 3. `patterns` - 감지된 패턴

```sql
CREATE TABLE patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  pattern_type TEXT NOT NULL DEFAULT 'sequence',
  count INTEGER NOT NULL DEFAULT 0,
  actions JSONB NOT NULL DEFAULT '[]'::jsonb,
  similarity_score NUMERIC,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**용도**: 반복 패턴 감지 결과 저장

### 4. `slack_events` - Slack 이벤트 로그

```sql
CREATE TABLE slack_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  user_id TEXT,
  channel_id TEXT,
  payload JSONB NOT NULL,
  processed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**용도**: Slack Bot 이벤트 및 명령 로그

---

## 마이그레이션 명령어

프로젝트의 `Makefile`에 다음 명령어가 정의되어 있습니다:

### 기본 명령어

```bash
# 로컬 Supabase 시작 (Docker 필요)
make db-start

# 로컬 Supabase 중지
make db-stop

# Supabase 상태 확인 (URL, API Keys 등)
make db-status
```

### 마이그레이션 관리

```bash
# 새로운 마이그레이션 파일 생성
make db-migration-new
# 프롬프트에서 마이그레이션 이름 입력

# 또는 인자로 직접 전달
make db-migration-new NAME=add_users_table

# 마이그레이션 목록 확인 (로컬 vs 리모트)
make db-migration-list

# 로컬 DB 초기화 (모든 마이그레이션 재실행)
make db-reset
```

### 배포 명령어

```bash
# 프로덕션 DB에 마이그레이션 배포
make db-push

# 프로덕션 DB 스키마 가져오기 (역방향)
make db-pull

# 로컬-프로덕션 차이 확인
make db-diff
```

---

## 새로운 마이그레이션 만들기

### 1. 마이그레이션 파일 생성

```bash
make db-migration-new
# Enter migration name: add_user_preferences
```

생성된 파일: `supabase/migrations/YYYYMMDDHHMMSS_add_user_preferences.sql`

### 2. SQL 작성

**⚠️ 중요 - UTF-8 인코딩 이슈 방지**:
- **주석은 반드시 영문만 사용** (한글 주석 금지)
- Migration 파일 작성 시 `cat > file.sql << 'EOF'` 방식 권장 (Claude Write 도구 대신)
- 파일 인코딩: UTF-8 without BOM

```sql
-- Add user_preferences table
CREATE TABLE user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index
CREATE INDEX user_preferences_user_id_idx ON user_preferences(user_id);

-- Enable RLS
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- RLS Policy
CREATE POLICY "Users can manage their own preferences"
  ON user_preferences
  FOR ALL
  USING (auth.uid()::text = user_id);
```

### 3. 로컬에서 테스트 (선택사항)

```bash
# 로컬 Supabase 시작
make db-start

# .env.local을 로컬로 변경
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=<로컬 anon key>

# 마이그레이션 적용
make db-reset

# Python 앱 실행 및 테스트
uv run python demo.py
```

### 4. 프로덕션 배포

```bash
# .env.local을 프로덕션으로 변경
SUPABASE_URL=https://ddntzfdetgcobzohimvm.supabase.co
SUPABASE_KEY=<프로덕션 anon key>

# 프로덕션에 배포
make db-push
```

---

## 프로덕션 배포 워크플로우

### 권장 워크플로우 (안전)

```bash
# 1. 새 기능 브랜치 생성
git checkout -b feat/add-user-preferences

# 2. 마이그레이션 파일 생성 및 작성
make db-migration-new
# supabase/migrations/xxx_add_user_preferences.sql 편집

# 3. 로컬 테스트 (선택)
make db-start
make db-reset
uv run python demo.py

# 4. 프로덕션 배포
make db-push

# 5. Git 커밋
git add supabase/migrations/
git commit -m "feat: add user preferences table"
git push origin feat/add-user-preferences
```

### 빠른 배포 (현재 설정)

프로덕션 Supabase를 직접 사용하는 경우:

```bash
# 1. 마이그레이션 생성
make db-migration-new

# 2. SQL 작성
vim supabase/migrations/xxx_add_feature.sql

# 3. 바로 프로덕션 배포
make db-push

# 4. Git 커밋
git add . && git commit -m "feat: add feature"
```

---

## 트러블슈팅

### 마이그레이션 실패 시

```bash
# 오류 확인
make db-push

# 로컬-프로덕션 차이 확인
make db-diff

# 프로덕션 스키마 가져오기
make db-pull
```

### 마이그레이션 히스토리 불일치

```bash
# 수동으로 마이그레이션 상태 수정
supabase migration repair --status applied <migration_id>
```

### UUID 함수 오류

**잘못된 예시** (구버전):
```sql
DEFAULT uuid_generate_v4()  -- ❌ 오류 발생
```

**올바른 예시** (PostgreSQL 13+):
```sql
DEFAULT gen_random_uuid()  -- ✅ 정상 작동
```

### 연결 실패

```bash
# Supabase 프로젝트 재연결
supabase link --project-ref ddntzfdetgcobzohimvm

# 상태 확인
make db-status
```

### UTF-8 인코딩 오류

**문제**: Migration 파일에 한글 주석이 있을 때 인코딩 오류 발생

```bash
# ❌ 오류 예시
-- LabeledAction 테이블 생성  # 한글 주석으로 인한 UTF-8 오류
```

**해결책**:

```bash
# 1. 영문 주석으로 변경
-- LabeledAction table (Analysis Layer)

# 2. Bash heredoc으로 파일 작성 (Write 도구 대신)
cat > supabase/migrations/YYYYMMDDHHMMSS_add_table.sql << 'EOF'
-- English comments only
CREATE TABLE example (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);
EOF

# 3. 파일 인코딩 확인
file -I supabase/migrations/*.sql
# 출력: text/plain; charset=utf-8
```

---

## 참고 자료

- [Supabase Migration 공식 문서](https://supabase.com/docs/guides/cli/local-development#database-migrations)
- [PostgreSQL 데이터 타입](https://www.postgresql.org/docs/current/datatype.html)
- [RLS (Row Level Security) 가이드](https://supabase.com/docs/guides/auth/row-level-security)

---

## 현재 환경 정보

- **프로젝트 ID**: `ddntzfdetgcobzohimvm`
- **프로덕션 URL**: `https://ddntzfdetgcobzohimvm.supabase.co`
- **연결 상태**: ✅ 연결됨 (`supabase link` 완료)
- **마이그레이션 상태**: ✅ 초기 스키마 배포 완료

```bash
# 현재 마이그레이션 확인
make db-migration-list
```

출력 예시:
```
  Local          | Remote         | Time (UTC)
  ----------------|----------------|---------------------
   20260131073844 | 20260131073844 | 2026-01-31 07:38:44
```
