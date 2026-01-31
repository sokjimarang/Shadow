"""Agent ↔ Server API 라우터

Agent가 관찰 데이터를 전송하고 시스템을 제어하는 엔드포인트
"""

from fastapi import APIRouter, Depends, status
from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.api.models import (
    ControlRequest,
    ControlResponse,
    ObservationsRequest,
    ObservationsResponse,
    SystemStatus,
)
from shadow.api.repositories import ObservationRepository, SessionRepository
from shadow.core.database import get_db

router = APIRouter(prefix="/api/v1", tags=["agent"])


# ====== POST /api/v1/observations ======


@router.post("/observations", response_model=ObservationsResponse, status_code=status.HTTP_200_OK)
async def create_observations(
    request: ObservationsRequest, db: Client = Depends(get_db)
) -> ObservationsResponse:
    """관찰 데이터 전송 (Agent → Server)

    Args:
        request: 관찰 데이터 요청
        db: Supabase 클라이언트

    Returns:
        처리 결과

    Raises:
        ShadowAPIError: 처리 실패 시
    """
    session_repo = SessionRepository(db)
    obs_repo = ObservationRepository(db)

    # 세션 존재 확인
    session_repo.get_session(request.session_id)

    processed_ids: list[str] = []

    try:
        for obs_data in request.observations:
            # 1. Before 스크린샷 저장
            before_screenshot = obs_repo.create_screenshot(
                screenshot_id=f"{obs_data.id}_before",
                session_id=request.session_id,
                timestamp=obs_data.timestamp,
                screenshot_type="before",
                data=obs_data.before_screenshot,
                thumbnail=obs_data.before_screenshot[:100],  # 임시: 실제로는 썸네일 생성 필요
                resolution={"width": 1920, "height": 1080},  # 임시: 실제 해상도 필요
                trigger_event_id=obs_data.id,
            )

            # 2. After 스크린샷 저장
            after_screenshot = obs_repo.create_screenshot(
                screenshot_id=f"{obs_data.id}_after",
                session_id=request.session_id,
                timestamp=obs_data.timestamp,
                screenshot_type="after",
                data=obs_data.after_screenshot,
                thumbnail=obs_data.after_screenshot[:100],
                resolution={"width": 1920, "height": 1080},
                trigger_event_id=obs_data.id,
            )

            # 3. 입력 이벤트 저장
            input_event = obs_repo.create_input_event(
                event_id=obs_data.id,
                session_id=request.session_id,
                timestamp=obs_data.timestamp,
                event_type=obs_data.event.type,
                position=obs_data.event.position,
                button=obs_data.event.button,
                active_window=obs_data.active_window.model_dump(),
            )

            # 4. 관찰 데이터 저장
            observation = obs_repo.create_observation(
                session_id=request.session_id,
                observation_id=obs_data.id,
                timestamp=obs_data.timestamp,
                before_screenshot_id=before_screenshot["id"],
                after_screenshot_id=after_screenshot["id"],
                event_id=input_event["id"],
            )

            processed_ids.append(observation["id"])

        # 세션 카운트 업데이트
        session_repo.increment_counts(
            session_id=request.session_id,
            event_count=len(request.observations),
            observation_count=len(request.observations),
        )

        return ObservationsResponse(
            status="ok",
            processed=len(processed_ids),
            observation_ids=processed_ids,
        )

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="관찰 데이터 처리 중 오류 발생",
            details=str(e),
        )


# ====== GET /api/v1/status ======


@router.get("/status", response_model=SystemStatus, status_code=status.HTTP_200_OK)
async def get_status(db: Client = Depends(get_db)) -> SystemStatus:
    """시스템 상태 조회

    Args:
        db: Supabase 클라이언트

    Returns:
        시스템 상태 정보

    Raises:
        ShadowAPIError: 조회 실패 시
    """
    session_repo = SessionRepository(db)

    try:
        # TODO: 실제 사용자 ID 가져오기 (현재는 하드코딩)
        # 인증 시스템 구현 후 수정 필요
        user_id = "default_user"

        active_session = session_repo.get_active_session(user_id)

        if active_session:
            return SystemStatus(
                state="recording",
                session_id=active_session["id"],
                start_time=active_session.get("start_time"),
                event_count=active_session.get("event_count", 0),
                observation_count=active_session.get("observation_count", 0),
                pattern_count=0,  # TODO: 패턴 카운트 조회
                pending_questions=0,  # TODO: 대기 중인 질문 조회
            )
        else:
            return SystemStatus(
                state="idle",
                session_id=None,
                start_time=None,
                event_count=0,
                observation_count=0,
                pattern_count=0,
                pending_questions=0,
            )

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="상태 조회 중 오류 발생",
            details=str(e),
        )


# ====== POST /api/v1/control ======


@router.post("/control", response_model=ControlResponse, status_code=status.HTTP_200_OK)
async def control_system(
    request: ControlRequest, db: Client = Depends(get_db)
) -> ControlResponse:
    """시스템 제어 (start/stop/pause/resume)

    Args:
        request: 제어 명령
        db: Supabase 클라이언트

    Returns:
        제어 결과

    Raises:
        ShadowAPIError: 제어 실패 시
    """
    session_repo = SessionRepository(db)

    try:
        # TODO: 실제 사용자 ID 가져오기
        user_id = "default_user"

        if request.command == "start":
            # 새 세션 시작
            session = session_repo.create_session(user_id)

            return ControlResponse(
                status="ok",
                new_state="recording",
                session_id=session["id"],
            )

        elif request.command == "stop":
            if not request.session_id:
                raise ShadowAPIError(
                    error_code=ErrorCode.E002,
                    message="stop 명령에는 session_id가 필요합니다",
                    status_code=400,
                )

            session = session_repo.update_session_status(request.session_id, "completed")

            return ControlResponse(
                status="ok",
                new_state="idle",
                session_id=session["id"],
            )

        elif request.command == "pause":
            if not request.session_id:
                raise ShadowAPIError(
                    error_code=ErrorCode.E002,
                    message="pause 명령에는 session_id가 필요합니다",
                    status_code=400,
                )

            session = session_repo.update_session_status(request.session_id, "paused")

            return ControlResponse(
                status="ok",
                new_state="paused",
                session_id=session["id"],
            )

        elif request.command == "resume":
            if not request.session_id:
                raise ShadowAPIError(
                    error_code=ErrorCode.E002,
                    message="resume 명령에는 session_id가 필요합니다",
                    status_code=400,
                )

            session = session_repo.update_session_status(request.session_id, "active")

            return ControlResponse(
                status="ok",
                new_state="recording",
                session_id=session["id"],
            )

        else:
            raise ShadowAPIError(
                error_code=ErrorCode.E002,
                message=f"지원하지 않는 명령: {request.command}",
                status_code=400,
            )

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="제어 명령 처리 중 오류 발생",
            details=str(e),
        )
