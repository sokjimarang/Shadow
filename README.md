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

`.env` 파일을 생성하고 API 키를 설정하세요:

```bash
cp .env.example .env
```

```env
# Claude API (기본 백엔드)
ANTHROPIC_API_KEY=sk-ant-...

# Gemini API (선택)
GEMINI_API_KEY=...
```

## 사용법

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

## 프로젝트 구조

```
shadow/
├── capture/           # 화면 캡처 및 입력 이벤트
│   ├── screen.py      # mss 기반 스크린샷 캡처
│   ├── input_events.py # pynput 기반 입력 이벤트 수집
│   ├── recorder.py    # 통합 녹화기
│   └── models.py      # 데이터 모델
├── preprocessing/     # 전처리
│   └── keyframe.py    # 키프레임 추출기
├── analysis/          # Vision AI 분석
│   ├── base.py        # 분석기 베이스 클래스
│   ├── claude.py      # Claude Opus 4.5 분석기
│   ├── gemini.py      # Gemini 분석기
│   └── prompts.py     # 프롬프트 템플릿
├── patterns/          # 패턴 감지
│   ├── detector.py    # 패턴 감지기
│   └── similarity.py  # 유사도 계산
└── config.py          # 설정 관리
```

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
- mss (화면 캡처)
- pynput (입력 이벤트)
- Anthropic SDK (Claude API)
- Google GenAI SDK (Gemini API)
- Pillow (이미지 처리)
- NumPy (패턴 분석)
- python-Levenshtein (문자열 유사도)

## 라이선스

MIT
