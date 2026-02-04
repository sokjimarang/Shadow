# Shadow 클라이언트-서버 분리 계획

**작성일: 2026-02-04**
**상태: 계획 수립 완료**

---

## 📋 현재 상태 분석

### 이미 구현된 것
- ✅ FastAPI 서버 (`main.py`)
- ✅ Supabase 연동 (DB)
- ✅ 모듈 구조 명확 (capture, analysis, patterns 등)
- ✅ REST API 엔드포인트 (녹화, 분석, 패턴)

### 분리가 필요한 이유
- **로컬 전용 모듈**: `capture/` (mss, pynput - OS 의존)
- **서버 가능 모듈**: `analysis/`, `patterns/`, `hitl/`, `spec/`, `slack/`
- **비용 최적화**: Vision AI 분석은 서버에서 집중 처리
- **배포 편의성**: CLI는 가볍게, 서버는 Vercel로 간단히 배포

---

## 🏗️ 아키텍처 설계

### 패키지 구조
```
shadow-py/
├── packages/
│   ├── client/                 # CLI 도구 (로컬 실행)
│   │   ├── shadow_client/
│   │   │   ├── capture/       # 화면 캡처 (기존)
│   │   │   ├── preprocessing/  # 키프레임 추출 (기존)
│   │   │   ├── uploader.py    # Supabase Storage 업로드 ⭐신규
│   │   │   ├── api_client.py  # 서버 API 클라이언트 ⭐신규
│   │   │   └── cli.py         # CLI 진입점 (수정)
│   │   └── pyproject.toml
│   │
│   └── server/                 # Vercel 배포
│       ├── shadow_server/
│       │   ├── analysis/      # Claude 분석 (기존)
│       │   ├── patterns/      # 패턴 감지 (기존)
│       │   ├── hitl/          # 질문 생성 (기존)
│       │   ├── spec/          # 명세서 (기존)
│       │   ├── slack/         # Slack 연동 (기존)
│       │   ├── api/           # API 라우터 (기존)
│       │   └── main.py        # FastAPI 앱 (기존)
│       ├── vercel.json        # Vercel 설정 ⭐신규
│       └── pyproject.toml
│
├── shared/                     # 공통 모듈
│   └── shadow_core/
│       ├── models.py          # Pydantic 모델 (공유)
│       ├── config.py          # 설정 (공유)
│       └── storage.py         # Supabase Storage 헬퍼 ⭐신규
│
└── README.md
```

---

## 🔄 데이터 흐름

### 1️⃣ 녹화 → 분석 플로우
```
[Client]
1. 화면 캡처 + 입력 이벤트 수집
2. 키프레임 추출 (클릭 전후)
3. 이미지 → Supabase Storage 업로드
   └─ before.png, after.png → URL 획득

4. POST /api/observations
   {
     "session_id": "xxx",
     "event": {...},
     "before_image_url": "https://...",
     "after_image_url": "https://..."
   }

[Server]
5. 이미지 URL로 다운로드
6. Claude Vision AI 분석
7. LabeledAction 생성 → DB 저장
8. Response 반환

[Client]
9. 분석 완료 확인
```

### 2️⃣ 패턴 감지 플로우
```
[Client]
1. POST /api/sessions/{id}/analyze

[Server]
2. 세션의 모든 LabeledAction 조회
3. 패턴 감지 (LLM)
4. HITL 질문 생성
5. Slack 전송 (선택적)
6. 명세서 생성
```

---

## 🛠️ 구현 상세

### A. 클라이언트 (shadow-client)

#### 신규 구현
1. **Supabase Storage 업로드** (`uploader.py`)
   ```python
   class StorageUploader:
       def upload_keyframe(session_id, observation_id, image):
           # shadow-recordings/{session_id}/{obs_id}_before.png
           url = supabase.storage.upload(...)
           return url
   ```

2. **서버 API 클라이언트** (`api_client.py`)
   ```python
   class ShadowAPIClient:
       def __init__(server_url):
           self.base_url = server_url

       def create_observation(session_id, event, before_url, after_url):
           # POST /api/observations

       def analyze_session(session_id):
           # POST /api/sessions/{id}/analyze
   ```

3. **CLI 수정** (`cli.py`)
   - 녹화 후 자동 업로드
   - 서버 URL 설정 추가

#### 의존성
```toml
[dependencies]
mss = ">=9.0.0"
pynput = ">=1.7.0"
pillow = ">=10.0.0"
pyobjc-framework-Cocoa = ">=10.3.1"  # macOS only
supabase = ">=2.0.0"  # Storage 업로드
httpx = ">=0.27.0"  # API 호출
```

---

### B. 서버 (shadow-server)

#### Vercel 배포 설정 (`vercel.json`)
```json
{
  "builds": [
    {
      "src": "shadow_server/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "shadow_server/main.py"
    }
  ],
  "env": {
    "ANTHROPIC_API_KEY": "@anthropic-api-key",
    "SUPABASE_URL": "@supabase-url",
    "SUPABASE_KEY": "@supabase-key",
    "SLACK_BOT_TOKEN": "@slack-bot-token"
  }
}
```

#### API 수정
- 기존: 로컬 파일 경로 기반
- 변경: 이미지 URL 기반 처리

```python
# Before
def analyze(keyframe: KeyframePair):
    image = keyframe.before.data

# After
def analyze(before_url: str, after_url: str):
    before_image = download_from_url(before_url)
    after_image = download_from_url(after_url)
```

#### 의존성
```toml
[dependencies]
fastapi = ">=0.128.0"
uvicorn = ">=0.40.0"
anthropic = ">=0.40.0"
supabase = ">=2.0.0"
slack-sdk = ">=3.39.0"
pydantic-settings = ">=2.0.0"
```

---

### C. 공유 모듈 (shadow-core)

#### 포함 내용
1. **Pydantic 모델**: LabeledAction, DetectedPattern, Question 등
2. **설정 클래스**: Settings (환경 변수)
3. **Storage 헬퍼**: Supabase Storage 공통 로직

#### 배포
- 로컬 패키지로 관리 (`pip install -e shared/`)
- 또는 PyPI 배포 후 의존성 추가

---

## 🗄️ Supabase Storage 구조

```
shadow-recordings/
  ├── session-abc123/
  │   ├── obs-001_before.png
  │   ├── obs-001_after.png
  │   ├── obs-002_before.png
  │   └── obs-002_after.png
  │
  └── session-def456/
      └── ...
```

**정책:**
- Public 읽기 (Signed URL 불필요)
- 분석 후 원본 이미지 삭제 (선택적)
- 썸네일만 DB에 저장

---

## 📝 구현 단계

### Phase 1: 공통 모듈 분리 (1일)
- [ ] `shared/shadow_core/` 생성
- [ ] 모델, 설정, 에러 이동
- [ ] 로컬 패키지 설치 테스트

### Phase 2: 서버 분리 및 Vercel 배포 (2일)
- [ ] `packages/server/` 생성
- [ ] 모듈 이동 (analysis, patterns, hitl, spec, slack, api)
- [ ] `vercel.json` 작성
- [ ] 환경 변수 설정
- [ ] Vercel 배포 테스트
- [ ] API 수정 (URL 기반 이미지 처리)

### Phase 3: 클라이언트 수정 (2일)
- [ ] `packages/client/` 생성
- [ ] capture, preprocessing 이동
- [ ] `uploader.py` 구현 (Supabase Storage)
- [ ] `api_client.py` 구현
- [ ] CLI 수정 (서버 연동)
- [ ] 로컬 테스트

### Phase 4: 통합 테스트 및 문서화 (1일)
- [ ] E2E 플로우 테스트
- [ ] README 업데이트
- [ ] 배포 가이드 작성
- [ ] 환경 변수 가이드

---

## ⚠️ 고려사항

### 장점
✅ 역할 분리 명확 (로컬=수집, 서버=분석)
✅ Vercel 무료 티어 활용 가능
✅ Supabase Storage로 이미지 관리 효율적
✅ CLI 가볍고 빠름 (Vision AI 로직 없음)

### 단점 및 해결책
⚠️ **네트워크 지연**: 이미지 업로드 + API 호출
  → 키프레임만 업로드 (전체 프레임 X)

⚠️ **Vercel 시간 제한** (Hobby: 10초, Pro: 60초)
  → Background Task 사용 (`BackgroundTasks`)
  → 긴 작업은 WebHook으로 완료 알림

⚠️ **스토리지 비용**
  → 분석 후 원본 삭제, 썸네일만 보관
  → Supabase 무료 티어: 1GB

---

## 🎯 최종 배포 형태

### 클라이언트
```bash
# 설치
uv pip install shadow-client

# 서버 URL 설정
export SHADOW_SERVER_URL=https://shadow-api.vercel.app

# 실행
shadow start --duration 10
```

### 서버
```bash
# Vercel 배포
vercel --prod

# 환경 변수 (Vercel Dashboard에서 설정)
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://...
SUPABASE_KEY=...
SLACK_BOT_TOKEN=xoxb-...
```

---

## 📊 작업 추정

**예상 작업 시간: 6일**
**난이도: 중**

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-02-04 | 초안 작성 |
