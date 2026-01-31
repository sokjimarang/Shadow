# Nemotron VL 분석기 통합 계획

> **상태**: 계획안 (미구현)
> **작성일**: 2026-01-31
> **예상 작업량**: 6개 파일 수정/생성

## 개요

NVIDIA NIM의 Nemotron VL 모델을 Shadow 프로젝트의 Vision 분석기 백엔드로 추가합니다.

**핵심 특징:**
- OpenAI SDK 호환 API (별도 SDK 불필요)
- 모델: `nvidia/nemotron-nano-12b-v2-vl` (12.6B 파라미터)
- 문서/OCR에 강점, OCRBench 1위

---

## 수정 파일 목록

| 파일 | 작업 |
|------|------|
| `pyproject.toml` | `openai>=1.0.0` 의존성 추가 |
| `shadow/config.py` | Nemotron 설정 항목 추가 |
| `shadow/analysis/base.py` | `AnalyzerBackend.NEMOTRON` 추가 |
| `shadow/analysis/nemotron.py` | **신규** - NemotronAnalyzer 클래스 |
| `shadow/analysis/__init__.py` | import 및 팩토리 함수 업데이트 |
| `.env.example` | `NVIDIA_API_KEY` 추가 |

---

## 구현 상세

### 1. 의존성 추가 (`pyproject.toml`)

```toml
# Vision AI - NVIDIA NIM (OpenAI 호환)
"openai>=1.0.0",
```

### 2. 설정 추가 (`shadow/config.py`)

```python
# NVIDIA NIM API
nvidia_api_key: str = ""

# Nemotron 분석 설정
nemotron_model: str = "nvidia/nemotron-nano-12b-v2-vl"
nemotron_base_url: str = "https://integrate.api.nvidia.com/v1"
nemotron_max_image_size: int = 1024
```

### 3. Backend Enum 확장 (`shadow/analysis/base.py:17-22`)

```python
class AnalyzerBackend(Enum):
    CLAUDE = "claude"
    NEMOTRON = "nemotron"  # 추가
```

### 4. NemotronAnalyzer 구현 (`shadow/analysis/nemotron.py`)

```python
class NemotronAnalyzer(BaseVisionAnalyzer):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_image_size: int | None = None,
        base_url: str | None = None,
    ):
        self._api_key = api_key or settings.nvidia_api_key
        if not self._api_key:
            raise ValueError("NVIDIA_API_KEY가 설정되지 않았습니다.")

        self._model = model or settings.nemotron_model
        self._max_image_size = max_image_size or settings.nemotron_max_image_size
        self._base_url = base_url or settings.nemotron_base_url

        self._client = OpenAI(
            base_url=self._base_url,
            api_key=self._api_key,
        )

    @property
    def backend(self) -> AnalyzerBackend:
        return AnalyzerBackend.NEMOTRON

    @property
    def model_name(self) -> str:
        return self._model

    async def analyze_keyframe_pair(self, pair: KeyframePair) -> LabeledAction:
        # OpenAI 호환 API 호출
        # - Base64 이미지 2개 (Before/After)
        # - 시스템 프롬프트 (기존과 동일)
        # - max_tokens=512
        ...

    async def analyze_batch(self, pairs: list[KeyframePair]) -> list[LabeledAction]:
        # 순차 처리 (배치 API 미지원)
        ...

    def _parse_response(self, response_text: str) -> LabeledAction:
        # JSON 파싱 (기존 패턴과 동일)
        ...
```

**API 호출 형식:**
```python
response = self._client.chat.completions.create(
    model=self._model,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "[Before 이미지]"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{before_b64}"}},
                {"type": "text", "text": "[After 이미지]"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{after_b64}"}},
                {"type": "text", "text": user_message},
            ],
        }
    ],
    max_tokens=512,
)
```

### 5. 팩토리 함수 업데이트 (`shadow/analysis/__init__.py`)

```python
from shadow.analysis.nemotron import NemotronAnalyzer

def create_analyzer(backend, **kwargs):
    # ... 기존 코드 ...
    elif backend == AnalyzerBackend.NEMOTRON:
        return NemotronAnalyzer(**kwargs)
    # ...

__all__ = [
    # ...
    "NemotronAnalyzer",
]
```

### 6. 환경변수 문서화 (`.env.example`)

```env
# NVIDIA NIM API 키 (Nemotron VL)
NVIDIA_API_KEY=nvapi-your_api_key_here
```

---

## 구현 순서

1. `pyproject.toml` - openai 의존성 추가 → `uv sync`
2. `shadow/config.py` - Nemotron 설정 추가
3. `shadow/analysis/base.py` - NEMOTRON enum 추가
4. `shadow/analysis/nemotron.py` - NemotronAnalyzer 클래스 작성
5. `shadow/analysis/__init__.py` - import 및 팩토리 업데이트
6. `.env.example` - NVIDIA_API_KEY 추가

---

## 검증 방법

### 1. Import 테스트
```bash
python -c "from shadow.analysis import NemotronAnalyzer, create_analyzer; print('OK')"
```

### 2. 팩토리 함수 테스트
```bash
python -c "
from shadow.analysis import create_analyzer, AnalyzerBackend
# API 키 없이 enum 값만 확인
print(AnalyzerBackend.NEMOTRON)
"
```

### 3. API 연동 테스트 (API 키 필요)
```bash
export NVIDIA_API_KEY=nvapi-...
python -c "
from shadow.analysis import create_analyzer
analyzer = create_analyzer('nemotron')
print(f'Backend: {analyzer.backend}')
print(f'Model: {analyzer.model_name}')
"
```

### 4. E2E 테스트 (demo.py 수정 후)
```bash
python demo.py --record 5 --backend nemotron
```

---

## 고려사항

- **캐싱 미지원**: NVIDIA NIM은 프롬프트 캐싱을 지원하지 않음 (Claude와 다름)
- **동기 API**: OpenAI SDK는 동기 호출, 필요시 `run_in_executor` 사용 가능
- **에러 처리**: `RateLimitError`, `APIConnectionError`, `APIError` 처리 필요

---

## 참고 자료

- [NVIDIA NIM - Nemotron Nano VL](https://build.nvidia.com/nvidia/nemotron-nano-12b-v2-vl/modelcard)
- [NVIDIA NIM VLM Documentation](https://docs.nvidia.com/nim/vision-language-models/latest/getting-started.html)
- [OpenAI SDK](https://github.com/openai/openai-python)