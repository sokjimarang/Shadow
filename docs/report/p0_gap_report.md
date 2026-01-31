# P0 기능 종합 리포트 (구현/PRD/갭)

**기준 문서**: `docs/prd.md`, `docs/implementation_status.md`  
**검증 대상 코드**: `shadow/*`, `main.py`, `shadow/cli.py`

이 문서는 P0 기능에 대해 **현재 구현 상태**, **PRD 기준**, **부족한 부분(갭)**, **향후 구현 필요 사항**을 정리합니다.

---

## F-01 화면 캡처

- **현재 구현**
  - MSS 기반 화면 캡처: `shadow/capture/screen.py`
  - Recorder의 연속 캡처 루프: `shadow/capture/recorder.py`
- **PRD 기준**
  - 클릭 이벤트 발생 시 Before/After 스크린샷 캡처
  - 이미지 파일 2개 저장
- **부족/갭**
  - 클릭 기준 Before/After 저장 경로가 통합 흐름에서 명확히 검증되지 않음
  - 권한/모니터 인덱스 오류 처리 미흡
- **앞으로 구현해야 할 부분**
  - 캡처 실패/권한 오류 핸들링 및 명확한 에러 메시지
  - 클릭 기준 Before/After 저장 결과를 파일로 보장하는 통합 경로 확정

---

## F-02 마우스 이벤트 캡처

- **현재 구현**
  - pynput 기반 이벤트 수집: `shadow/capture/input_events.py`
  - Recorder와 동시 수집: `shadow/capture/recorder.py`
- **PRD 기준**
  - 클릭 위치, 버튼 타입, 타임스탬프 기록
  - 이벤트 JSON 저장
- **부족/갭**
  - 이벤트 저장(JSON) 경로가 통합 흐름에서 명확히 연결되지 않음
  - 권한/리스너 실패 시 복구 전략 없음
- **앞으로 구현해야 할 부분**
  - 이벤트 저장 경로 확정 및 파일 출력 검증
  - 이벤트 수집 실패 처리 및 재시도/경고 로그

---

## F-03 활성 윈도우 정보

- **현재 구현**
  - macOS 기반 활성 앱/창 타이틀 수집 (macOS 전용): `shadow/capture/window.py`
  - 이벤트 생성 시 app_name/window_title 포함: `shadow/capture/input_events.py`
- **PRD 기준**
  - app_name 필드 존재 (macOS 전용)
- **부족/갭**
  - 비-macOS 환경은 "Unknown" 반환 (정확성 검증 불가)
- **앞으로 구현해야 할 부분**
  - 필요 시 OS별 구현 보강
  - 권한/포커스 문제 발생 시 진단 로그 보강 (현재 경고 로그 추가됨)

---

## F-04 행동 라벨링 (VLM)

- **현재 구현**
  - Claude 분석기: `shadow/analysis/claude.py`
  - 키프레임 쌍 분석 로직: `shadow/analysis/base.py`, `shadow/preprocessing/keyframe.py`
- **PRD 기준**
  - Before/After + 이벤트 입력 → semantic_label 생성
- **부족/갭**
  - API 실패/타임아웃/재시도 처리 없음
  - 결과 파싱 실패 시 "unknown" 처리만 수행
- **앞으로 구현해야 할 부분**
  - API 오류/쿼터/네트워크 실패 대응
  - 결과 스키마 검증, 로깅, 재시도 정책

---

## F-05 패턴 감지 (LLM) ✅ 완료

- **현재 구현**
  - LLM 기반 패턴 감지: `shadow/patterns/analyzer/claude.py`
  - 패턴 + 불확실성(uncertainties) 한 번에 추출
- **PRD 기준**
  - LLM 기반 패턴 추론 ✅
  - uncertainties 포함 ✅
- **남은 갭**
  - 3개 이상 세션 비교 미구현 (현재 단일 세션만 처리)
  - 3회 이상 반복 검증 로직 없음 (LLM 응답 신뢰)

---

## F-06 HITL 질문 생성

- **현재 구현**
  - 질문 생성기: `shadow/hitl/generator.py`
- **PRD 기준**
  - 불확실 지점에서 가설검증/품질확인 질문 2개 이상 생성
- **부족/갭**
  - 실제 패턴/uncertainty와의 통합 흐름 검증 부족
- **앞으로 구현해야 할 부분**
  - 패턴 감지 결과(uncertainty 포함)와 연결한 통합 흐름 테스트
  - 질문 중복/우선순위 정책 필요 시 추가

---

## F-07 Slack 메시지 송신

- **현재 구현**
  - Slack Block Kit 전송: `shadow/slack/client.py`
- **PRD 기준**
  - 질문을 Slack DM으로 전송, 메시지 ts 반환
- **부족/갭**
  - 전송 실패/레이트리밋/재시도 처리 없음
  - DM 채널 확인 로직 부재
- **앞으로 구현해야 할 부분**
  - 실패 대응 및 재시도 정책
  - 채널/사용자 ID 매핑·검증 흐름

---

## F-08 Slack 응답 수신

- **현재 구현**
  - 없음 (미구현)
- **PRD 기준**
  - 버튼 클릭 이벤트 수신 → selected_option_id 획득
- **부족/갭**
  - Interactive payload 처리 서버/엔드포인트 자체가 없음
- **앞으로 구현해야 할 부분**
  - Slack Interactive Components 핸들러
  - 서명 검증, payload 파싱
  - Question/Response로 변환 로직
  - 응답 저장/연결

---

## F-09 명세서 생성

- **현재 구현**
  - Spec builder/storage: `shadow/spec/builder.py`, `shadow/spec/storage.py`
- **PRD 기준**
  - 패턴 + 응답 반영 후 spec.json 생성, decisions.rules 포함
- **부족/갭**
  - Slack 응답 수신과 spec 생성의 통합 흐름 부재
  - Rule 생성이 일부 응답 타입만 반영
- **앞으로 구현해야 할 부분**
  - 응답 수신 → SpecBuilder 연결
  - 질문 유형 확장 시 rule 생성 보완

---

## F-10 CLI 시작/중지

- **현재 구현**
  - `shadow start` 동작, `shadow stop`은 안내 메시지만 출력: `shadow/cli.py`
- **PRD 기준**
  - CLI 시작/중지 명령 동작
- **부족/갭**
  - stop이 실제 녹화 종료를 수행하지 않음
- **앞으로 구현해야 할 부분**
  - CLI stop이 실제 Recorder 제어하도록 변경
  - 상태 확인/에러 처리 추가

---

# 종합 결론

- **완전 충족:** 없음
- **부분 충족/연결 미완성:** F-01/02/03/04/06/07/09/10
- **명확히 미구현:** F-05(LLM 패턴), F-08(Slack 응답 수신)
- **가장 큰 병목:** F-05, F-08, 그리고 실제 E2E 파이프라인 연결(관찰→분석→질문→응답→명세서)
