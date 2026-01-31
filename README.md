# Shadow

화면 녹화 + 입력 이벤트 수집 → Vision AI 분석 → 반복 패턴 감지

## 개요

Shadow는 사용자의 반복적인 GUI 작업을 자동으로 감지하는 도구입니다. 화면을 녹화하고 마우스/키보드 입력을 수집한 후, Vision AI(Claude Opus 4.5 또는 Gemini)를 사용하여 각 동작을 분석하고, 반복 패턴을 감지합니다.

## 주요 기능

- **화면 캡처**: mss를 사용한 고성능 스크린샷 캡처 (10 FPS)
- **입력 이벤트 수집**: pynput으로 마우스 클릭/스크롤, 키보드 입력 캡처
- **키프레임 추출**: 마우스 클릭 시점의 스크린샷만 추출하여 분석 효율화
- **Vision AI 분석**:
  - Claude Opus 4.5 (기본) - 프롬프트 캐싱으로 90% 비용 절감
  - Gemini 2.0 Flash - 비디오 분석 지원
- **패턴 감지**: 연속 반복 및 시퀀스 패턴 자동 감지

## 설치

```bash
# uv 사용 (권장)
uv sync

# 또는 pip
pip install -e .
```

## 환경 설정

`.env.local` 파일을 생성하고 API 키를 설정하세요:

```bash
cp .env.example .env.local
```

```env
# Claude API (기본 백엔드)
ANTHROPIC_API_KEY=sk-ant-...

# Gemini API (선택)
GEMINI_API_KEY=...

# Supabase (shadow-web과 동일한 DB)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Slack Bot (shadow-web 연동)
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
SLACK_DEFAULT_CHANNEL=C07UZ1234AB  # 기본 전송 채널 ID
```

## 데이터베이스 마이그레이션

Shadow는 Supabase PostgreSQL 데이터베이스를 사용합니다.

### Supabase CLI 설치

```bash
# Homebrew (macOS)
brew install supabase/tap/supabase

# NPM
npm install -g supabase

# 설치 확인
supabase --version
```

### DB 관리 명령어 (Makefile)

```bash
# 로컬 환경 관리
make db-start          # Docker로 로컬 Supabase 시작
make db-stop           # 로컬 Supabase 중지
make db-status         # 연결 상태 및 URL 확인

# 마이그레이션 관리
make db-migration-new                        # 대화형으로 마이그레이션 생성
make db-migration-new NAME=add_users_table   # 인자로 마이그레이션 생성
make db-migration-list                       # 마이그레이션 목록 확인
make db-reset                                # 로컬 DB 초기화

# 프로덕션 배포
make db-push           # 프로덕션에 마이그레이션 배포
make db-pull           # 프로덕션 스키마 가져오기
make db-diff           # 로컬-프로덕션 차이 확인
```

자세한 내용은 [`docs/database/migration-guide.md`](docs/database/migration-guide.md)를 참조하세요.

## 사용법

### REST API 서버

#### Makefile 명령어 (권장)

```bash
# 환경 변수 확인
make check-env

# FastAPI 서버만 실행
make server

# ngrok 터널링 (별도 터미널)
make ngrok

# 개발 환경 시작 (서버 + ngrok, tmux 사용)
make dev
```

#### 수동 실행

```bash
# FastAPI 서버 시작
uv run uvicorn main:app --reload

# 서버 주소: http://127.0.0.1:8000
# API 문서: http://127.0.0.1:8000/docs
```

#### ngrok으로 외부 노출 (Slack 연동 시)

Slack 이벤트를 수신하려면 ngrok으로 로컬 서버를 외부에 노출해야 합니다.

**자세한 가이드**: [`NGROK_GUIDE.md`](NGROK_GUIDE.md) 참조

**빠른 시작**:
```bash
# tmux를 사용하여 서버와 ngrok을 동시에 실행
make dev
```

#### API 엔드포인트

**Agent ↔ Server API** (`/api/v1/`)
- `POST /api/v1/observations` - 관찰 데이터 전송
- `GET /api/v1/status` - 시스템 상태 조회
- `POST /api/v1/control` - 제어 명령 (start/stop/pause/resume)

**HITL API** (`/api/hitl/`)
- `POST /api/hitl/response` - HITL 응답 수신 (shadow-web 연동)
- `GET /api/hitl/questions` - 대기 중인 질문 목록

**Spec API** (`/api/specs/`)
- `GET /api/specs` - 명세서 목록
- `GET /api/specs/{spec_id}` - 명세서 상세
- `POST /api/specs` - 명세서 생성
- `PUT /api/specs/{spec_id}` - 명세서 업데이트

자세한 API 테스트는 `test_main.http` 파일 참조

### CLI 데모

```bash
# Claude로 5초 녹화 및 분석
python demo.py --record 5

# Gemini로 10초 녹화 및 분석
python demo.py --record 10 --backend gemini

# API 없이 패턴 감지 테스트 (더미 데이터)
python demo.py --test
```

### macOS 권한 설정

입력 이벤트를 캡처하려면 다음 권한이 필요합니다:

1. **시스템 설정 > 개인정보 보호 및 보안 > 입력 모니터링**
   - 터미널 앱 추가

2. **시스템 설정 > 개인정보 보호 및 보안 > 화면 및 시스템 오디오 녹화**
   - 터미널 앱 추가

### 활성 윈도우 정보 수집

Shadow는 PyObjC를 통해 활성 애플리케이션 이름을 자동으로 수집합니다:

- 각 입력 이벤트에 `window_info` 필드 포함
- `event.window_info.app_name`으로 애플리케이션 이름 접근
- `bundle_id`, `process_id` 등 메타데이터 포함
- PyObjC 미설치 시에도 이벤트 수집은 계속 진행 (graceful degradation)

## 프로젝트 구조

```
shadow/
├── capture/           # 화면 캡처 및 입력 이벤트
│   ├── screen.py      # mss 기반 스크린샷 캡처
│   ├── input_events.py # pynput 기반 입력 이벤트 수집
│   ├── recorder.py    # 통합 녹화기
│   ├── window.py      # 활성 윈도우 감지
│   └── models.py      # 데이터 모델
├── preprocessing/     # 전처리
│   └── keyframe.py    # 키프레임 추출기
├── analysis/          # Vision AI 분석
│   ├── base.py        # 분석기 베이스 클래스
│   ├── claude.py      # Claude Opus 4.5 분석기
│   ├── gemini.py      # Gemini 분석기
│   ├── prompts.py     # 프롬프트 템플릿
│   └── models.py      # LabeledAction, SessionSequence
├── patterns/          # 패턴 감지
│   ├── detector.py    # 패턴 감지기
│   ├── similarity.py  # 유사도 계산
│   ├── uncertainties.py # Uncertainty (dataclass)
│   └── models.py      # DetectedPattern, ActionTemplate, Variation
├── hitl/              # Human-in-the-Loop
│   └── models.py      # HITLQuestion, HITLAnswer, InterpretedAnswer
├── spec/              # 자동화 명세서
│   └── models.py      # AgentSpec, SpecHistory
├── api/               # REST API
│   ├── routers/       # API 라우터
│   │   ├── agent.py   # Agent ↔ Server API
│   │   ├── hitl.py    # HITL API
│   │   └── specs.py   # Spec API
│   ├── repositories/  # 데이터 접근 레이어
│   │   ├── sessions.py
│   │   ├── observations.py
│   │   ├── hitl.py
│   │   └── specs.py
│   ├── models.py      # API 요청/응답 모델
│   └── errors.py      # 에러 코드 및 핸들러
├── core/              # 시스템 레이어
│   ├── models.py      # Session, User, Config
│   └── database.py    # Supabase 연결
└── config.py          # 설정 관리
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

| Layer | 모델 | 설명 |
|-------|------|------|
| Raw Data | `Screenshot`, `InputEventRecord`, `RawObservation` | 화면 캡처 + 입력 이벤트 |
| Analysis | `LabeledAction`, `SessionSequence` | VLM 분석 결과 |
| Pattern | `DetectedPattern`, `Uncertainty`, `ActionTemplate` | 반복 패턴 |
| HITL | `Question`, `Response` | 사용자 확인 |
| Spec | `Spec`, `AgentSpec`, `SpecHistory` | 자동화 명세서 |
| System | `Session`, `User`, `Config` | 시스템 설정 |

## 비용 최적화

### Claude Opus 4.5

- **프롬프트 캐싱**: 시스템 프롬프트 캐싱으로 90% 비용 절감
- **이미지 리사이즈**: 1024px로 리사이즈하여 토큰 절약
- **배치 분석**: 여러 이미지를 한 번의 API 호출로 분석

### 예상 비용

- 이미지당 약 900 토큰
- 캐싱 적용 시 이미지당 약 $0.007

## 기술 스택

- Python 3.13+
- FastAPI (REST API)
- Supabase (PostgreSQL database)
- mss (화면 캡처)
- pynput (입력 이벤트)
- Anthropic SDK (Claude API)
- Google GenAI SDK (Gemini API)
- Pillow (이미지 처리)
- NumPy (패턴 분석)
- python-Levenshtein (문자열 유사도)

## 시스템 아키텍처

Shadow는 2개의 서비스로 구성됩니다:

- **shadow-py** (Python): 화면 캡처, VLM 분석, 패턴 감지, API 서버
- **shadow-web** (TypeScript): Slack 이벤트 수신, HITL 응답 저장

두 서비스는 동일한 Supabase DB를 공유하며, HTTP API로 통신합니다.

## 라이선스

MIT
