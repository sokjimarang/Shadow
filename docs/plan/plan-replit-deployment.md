# Replit Reserved VM 배포 계획

> 작성일: 2026-01-31
> 상태: 계획 (핵심 기능 구현 후 진행 예정)

## 개요

Shadow API 서버를 Replit Reserved VM으로 배포하기 위한 계획서.

**배포 범위**: API 서버만 (화면 캡처 기능 제외)

## Replit Reserved VM 특징

| 항목 | 내용 |
|------|------|
| 환경 | Linux 기반 headless 서버 |
| 가동률 | 99.9% SLA |
| 비용 | 월 $20~ (Replit Core 플랜 필요) |
| 도메인 | `https://<subdomain>.replit.app` |

## 필요한 설정 파일

### 1. `.replit`

```toml
run = "uvicorn main:app --host 0.0.0.0 --port 8000"
entrypoint = "main.py"

[deployment]
run = ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000"]
deploymentTarget = "cloudrun"

[[ports]]
localPort = 8000
externalPort = 80
```

### 2. `replit.nix`

```nix
{ pkgs }: {
  deps = [
    pkgs.python313
    pkgs.poetry
  ];
}
```

## 환경 변수 (Secrets)

Replit Secrets 탭에서 설정:

| Key | 설명 |
|-----|------|
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `SUPABASE_URL` | Supabase 프로젝트 URL |
| `SUPABASE_KEY` | Supabase anon key |
| `SLACK_BOT_TOKEN` | Slack Bot 토큰 (선택) |

## 배포 절차

1. GitHub 저장소를 Replit으로 Import
2. `.replit`, `replit.nix` 파일 추가 및 커밋
3. Replit Secrets에 환경 변수 설정
4. Deployments 탭 → Reserved VM 선택
5. 머신 크기 선택 (권장: 0.5 vCPU, 512MB RAM 이상)
6. Deploy 클릭

## 사전 작업 필요 사항

### 1. API 전용 엔트리포인트 분리

현재 `main.py`에서 `shadow.capture` 모듈을 import하고 있음. 이 모듈은 macOS 전용 의존성(`pyobjc`)과 GUI 환경 필요 패키지(`mss`, `pynput`)를 사용.

**해결 방안**:
- API 전용 엔트리포인트 생성 (`api_main.py`)
- 또는 조건부 import로 변경

```python
# 예시: 조건부 import
import sys

if sys.platform == "darwin":
    from shadow.capture.recorder import Recorder
else:
    Recorder = None  # Linux에서는 녹화 기능 비활성화
```

### 2. 녹화 관련 엔드포인트 비활성화

Linux 환경에서 다음 엔드포인트는 동작하지 않음:
- `POST /recording/start`
- `POST /recording/stop`
- `GET /recording/status`
- `POST /analyze` (녹화 데이터 의존)

**해결 방안**: 환경 변수로 기능 토글 또는 에러 메시지 반환

### 3. 동작 가능한 API 목록

녹화 없이도 동작하는 API:
- `GET /status` - 서버 상태
- `GET /api/v1/*` - Agent 관련 API
- `GET /api/hitl/*` - HITL 관련 API
- `GET /api/specs/*` - Spec 관련 API

## 참고 자료

- [Replit Reserved VM Deployments 공식 문서](https://docs.replit.com/cloud-services/deployments/reserved-vm-deployments)
- [Replit Pricing](https://replit.com/pricing)
