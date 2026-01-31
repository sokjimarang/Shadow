# Shadow 클라이언트/서버 분리 계획

> 작성일: 2026-01-31
> 상태: 계획 (미구현)

## 목표

Shadow 코드베이스를 클라이언트(macOS 데스크톱)와 서버(Replit)로 분리하여:
- 클라이언트: 화면 캡처 + 입력 이벤트 수집 → 서버로 전송
- 서버: AI 분석 + 패턴 감지 + DB 저장

## 현재 구조 요약

```
shadow/
├── capture/       # 클라이언트 전용 (mss, pynput, PyObjC)
├── preprocessing/ # 클라이언트에서 실행 가능
├── analysis/      # 서버 전용 (anthropic, google-genai)
├── patterns/      # 서버 전용
├── api/           # 서버 전용 (FastAPI)
├── core/          # 서버 전용 (Supabase)
└── main.py        # 로컬 녹화 + API 서버 혼재 (분리 필요)
```

## 구현 계획

### Phase 1: 의존성 그룹화

**파일**: `pyproject.toml`

```toml
[project]
dependencies = [
    # 공통 (클라이언트/서버 모두)
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.28.0",  # 클라이언트 HTTP 전송용 (신규)
]

[dependency-groups]
client = [
    "mss>=9.0.0",
    "pynput>=1.7.0",
    "pillow>=10.0.0",
    "numpy>=2.0.0",
    "pyobjc-framework-Cocoa>=10.3.1; sys_platform == 'darwin'",
    "pyobjc-framework-Quartz>=10.3.1; sys_platform == 'darwin'",
]
server = [
    "fastapi>=0.128.0",
    "uvicorn>=0.40.0",
    "anthropic>=0.40.0",
    "google-genai>=1.0.0",
    "numpy>=2.0.0",
    "python-levenshtein>=0.26.0",
    "pillow>=10.0.0",
    "supabase>=2.0.0",
]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-httpx>=0.35.0",
]

[project.scripts]
shadow-agent = "shadow.client.agent:main"
```

**설치 명령**:
- 클라이언트: `uv sync --group client`
- 서버: `uv sync --group server`

---

### Phase 2: 클라이언트 모듈 생성

**신규 디렉토리**: `shadow/client/`

#### 2.1 ShadowClient (HTTP 클라이언트)

**파일**: `shadow/client/client.py`

```python
class ShadowClient:
    """Shadow 서버 API 클라이언트"""

    def __init__(self, server_url: str, timeout: float = 30.0):
        self.server_url = server_url
        self._client = httpx.AsyncClient(base_url=server_url, timeout=timeout)

    async def start_session(self) -> str:
        """새 세션 시작 → session_id 반환"""

    async def send_observations(self, keyframe_pairs: list[KeyframePair]) -> list[str]:
        """관찰 데이터 전송 (base64 이미지 + 메타데이터)"""

    async def stop_session(self) -> None:
        """세션 종료"""
```

#### 2.2 ShadowAgent (백그라운드 에이전트)

**파일**: `shadow/client/agent.py`

```python
class ShadowAgent:
    """백그라운드 에이전트 - 녹화 + 전송"""

    def __init__(self, config: ClientConfig):
        self.client = ShadowClient(config.server_url)
        self.recorder = Recorder()
        self.extractor = KeyframeExtractor()

    async def run(self) -> None:
        """무한 루프: 녹화 → 키프레임 추출 → 서버 전송"""
```

#### 2.3 클라이언트 설정

**파일**: `shadow/client/config.py`

```python
class ClientConfig(BaseSettings):
    server_url: str = "http://localhost:8000"
    chunk_duration: float = 30.0  # 녹화 청크 크기(초)
    fps: int = 10
    monitor: int = 1
```

---

### Phase 3: 서버 진입점 분리

**파일**: `main.py` 수정

현재 `main.py`에는 로컬 녹화 코드가 포함되어 있음 (line 25-46, 126-177, 180-258).
서버 배포 시 이 코드를 제거하거나 분리.

**결정**: 기존 main.py를 서버 전용으로 정리
- `Recorder`, `RecordingSession` import 제거
- `/recording/*`, `/analyze`, `/labels`, `/patterns` 엔드포인트 제거
- agent_router의 `/api/v1/*` 엔드포인트만 유지
- 인증 없이 진행 (빠른 프로토타이핑 우선)

---

### Phase 4: API 엔드포인트 확정

**서버 API** (agent_router에 이미 존재):

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/observations` | POST | 관찰 데이터 수신 |
| `/api/v1/status` | GET | 시스템 상태 |
| `/api/v1/control` | POST | 세션 제어 (start/stop) |
| `/health` | GET | 헬스 체크 |

**기존 모델 활용** (`shadow/api/models.py`):
- `ObservationsRequest` - 클라이언트 → 서버 데이터
- `ObservationsResponse` - 서버 → 클라이언트 응답
- `ControlRequest/Response` - 세션 제어

---

### Phase 5: Replit 배포 설정

**파일**: `.replit` (신규)

```
run = "uvicorn main:app --host 0.0.0.0 --port 8000"
```

**환경 변수** (Replit Secrets):
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `ANTHROPIC_API_KEY`

---

## 파일 변경 목록

### 수정
1. `pyproject.toml` - 의존성 그룹화 + httpx 추가 + scripts 추가
2. `main.py` - 로컬 녹화 코드 제거, 서버 전용으로 정리

### 신규 생성
3. `shadow/client/__init__.py`
4. `shadow/client/client.py` - ShadowClient
5. `shadow/client/agent.py` - ShadowAgent + CLI 진입점
6. `shadow/client/config.py` - ClientConfig
7. `.replit` - Replit 배포 설정

---

## 데이터 흐름

```
[클라이언트 macOS]                      [서버 Replit]
      |                                      |
      | 1. POST /api/v1/control (start)      |
      |------------------------------------->|
      |    {"session_id": "..."}             |
      |<-------------------------------------|
      |                                      |
      | [녹화 30초]                           |
      | [키프레임 추출]                        |
      |                                      |
      | 2. POST /api/v1/observations         |
      |   {session_id, observations[]}       |
      |------------------------------------->|
      |                                      | [VLM 분석]
      |    {"processed": 5}                  | [패턴 감지]
      |<-------------------------------------| [DB 저장]
      |                                      |
      | ... 반복 ...                          |
      |                                      |
      | 3. POST /api/v1/control (stop)       |
      |------------------------------------->|
```

---

## 검증 방법

### 1. 의존성 분리 확인
```bash
# 클라이언트만 설치
uv sync --group client
python -c "from shadow.capture import Recorder; print('OK')"
python -c "from shadow.analysis import ClaudeAnalyzer"  # ImportError 예상

# 서버만 설치
uv sync --group server
python -c "from shadow.api.routers import agent_router; print('OK')"
python -c "from shadow.capture import Recorder"  # ImportError 예상
```

### 2. 클라이언트 동작 확인
```bash
# 로컬 서버 실행
uvicorn main:app --port 8000

# 별도 터미널에서 클라이언트 실행
shadow-agent --server http://localhost:8000 --chunk 10
```

### 3. E2E 테스트
```bash
# 서버 상태 확인
curl http://localhost:8000/api/v1/status

# 관찰 데이터 전송 테스트
curl -X POST http://localhost:8000/api/v1/observations \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "observations": []}'
```

---

## 주의사항

1. **PyObjC는 macOS 전용**: 클라이언트는 macOS에서만 실행 가능
2. **이미지 크기**: base64 인코딩으로 ~33% 증가, 네트워크 대역폭 고려
3. **API 키 보안**: 서버에만 저장, 클라이언트에 노출 금지
4. **기존 테스트**: 의존성 분리 후 테스트 import 경로 확인 필요
