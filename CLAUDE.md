# Shadow 프로젝트 가이드

> **참고**: 이 문서에 명시되지 않은 기본 작성규칙(코드 작성 원칙, 플랜 수립, 에이전트 활용, 문제 해결 등)은 전역 CLAUDE.md (`~/.claude/CLAUDE.md`)를 참조하세요.

## 개발 규칙

### Database 스키마 참조

Database 관련 참조가 필요할 때는 [shadow-web 레포지토리](https://github.com/sokjimarang/shadow-web)의 스키마 migration 파일을 참조합니다.

### 기능 구현 시 참조 문서

기능 구현 시 다음 문서를 참조하여 스펙이 맞는지 확인하고 구현합니다:

- **PRD 문서**: `docs/prd.md` - 제품 요구사항 및 기능 정의
- **Service Plan 문서**: `docs/service-plan-v1.2.md` - 서비스 아키텍처 및 구현 계획

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

