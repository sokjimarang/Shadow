"""Shadow REST API

기본 엔드포인트:
- GET /status: 서버 상태
- POST /recording/start: 녹화 시작
- POST /recording/stop: 녹화 중지
- GET /recording/status: 녹화 상태
- POST /analyze: 녹화 데이터 분석
- GET /patterns: 패턴 감지 결과
"""

import asyncio
import threading
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from shadow.analysis.models import LabeledAction
from shadow.analysis.claude import ClaudeAnalyzer
from shadow.analysis.gemini import GeminiAnalyzer
from shadow.api.errors import ShadowAPIError, general_exception_handler, shadow_api_error_handler
from shadow.api.routers import agent_router, hitl_router, slack_router, specs_router
from shadow.capture.recorder import Recorder, RecordingSession
from shadow.config import settings
from shadow.patterns.detector import PatternDetector
from shadow.preprocessing.keyframe import KeyframeExtractor


# === 상태 관리 ===


class AppState:
    """애플리케이션 전역 상태"""

    def __init__(self) -> None:
        self.recorder: Recorder | None = None
        self.session: RecordingSession | None = None
        self.recording_thread: threading.Thread | None = None
        self.labels: list[LabeledAction] = []
        self.patterns: list[dict[str, Any]] = []
        self.is_analyzing: bool = False


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 초기화"""
    yield
    # 종료 시 녹화 정리
    if state.recorder and state.recorder.is_recording:
        state.recorder.stop()


app = FastAPI(
    title="Shadow API",
    description="화면 녹화 → Vision AI 분석 → 패턴 감지 API",
    version="0.1.0",
    lifespan=lifespan,
)

# === 에러 핸들러 등록 ===
app.add_exception_handler(ShadowAPIError, shadow_api_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# === API 라우터 등록 ===
app.include_router(agent_router)  # /api/v1/*
app.include_router(hitl_router)  # /api/hitl/*
app.include_router(specs_router)  # /api/specs/*
app.include_router(slack_router)  # /slack/*


# === 요청/응답 모델 ===


class RecordingStartRequest(BaseModel):
    duration: float = Field(default=10.0, ge=1.0, le=300.0, description="녹화 시간(초)")
    monitor: int = Field(default=1, ge=1, description="캡처할 모니터 번호")
    fps: int = Field(default=10, ge=1, le=30, description="초당 프레임 수")


class AnalyzeRequest(BaseModel):
    backend: str = Field(default="claude", description="분석 백엔드 (claude/gemini)")


class RecordingStatus(BaseModel):
    is_recording: bool
    has_session: bool
    frame_count: int = 0
    event_count: int = 0
    duration: float = 0.0


class StatusResponse(BaseModel):
    status: str
    recording: RecordingStatus
    has_labels: bool
    has_patterns: bool
    is_analyzing: bool


# === 엔드포인트 ===


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """서버 및 녹화 상태 조회"""
    recording_status = RecordingStatus(
        is_recording=state.recorder.is_recording if state.recorder else False,
        has_session=state.session is not None,
        frame_count=len(state.session.frames) if state.session else 0,
        event_count=len(state.session.events) if state.session else 0,
        duration=state.session.duration if state.session else 0.0,
    )
    return StatusResponse(
        status="ok",
        recording=recording_status,
        has_labels=len(state.labels) > 0,
        has_patterns=len(state.patterns) > 0,
        is_analyzing=state.is_analyzing,
    )


@app.post("/recording/start")
async def start_recording(request: RecordingStartRequest):
    """녹화 시작 (백그라운드 실행)"""
    if state.recorder and state.recorder.is_recording:
        raise HTTPException(status_code=400, detail="이미 녹화 중입니다")

    # 이전 세션 정리
    state.session = None
    state.labels = []
    state.patterns = []

    state.recorder = Recorder(monitor=request.monitor, fps=request.fps)

    def record_task():
        state.session = state.recorder.record(request.duration)

    state.recording_thread = threading.Thread(target=record_task, daemon=True)
    state.recording_thread.start()

    return {
        "message": "녹화 시작",
        "duration": request.duration,
        "monitor": request.monitor,
        "fps": request.fps,
    }


@app.post("/recording/stop")
async def stop_recording():
    """녹화 중지"""
    if not state.recorder or not state.recorder.is_recording:
        raise HTTPException(status_code=400, detail="녹화 중이 아닙니다")

    state.recorder.stop()

    # 스레드 종료 대기 (최대 2초)
    if state.recording_thread:
        state.recording_thread.join(timeout=2.0)

    return {"message": "녹화 중지됨"}


@app.get("/recording/status", response_model=RecordingStatus)
async def get_recording_status():
    """녹화 상태 상세 조회"""
    return RecordingStatus(
        is_recording=state.recorder.is_recording if state.recorder else False,
        has_session=state.session is not None,
        frame_count=len(state.session.frames) if state.session else 0,
        event_count=len(state.session.events) if state.session else 0,
        duration=state.session.duration if state.session else 0.0,
    )


@app.post("/analyze")
async def analyze_session(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """녹화 세션 분석 (백그라운드 실행)"""
    if not state.session:
        raise HTTPException(status_code=400, detail="녹화 세션이 없습니다")

    if state.is_analyzing:
        raise HTTPException(status_code=400, detail="이미 분석 중입니다")

    if len(state.session.frames) == 0:
        raise HTTPException(status_code=400, detail="녹화된 프레임이 없습니다")

    # 분석기 선택
    if request.backend == "claude":
        if not settings.anthropic_api_key:
            raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY가 설정되지 않았습니다")
        analyzer = ClaudeAnalyzer()
    elif request.backend == "gemini":
        if not settings.gemini_api_key:
            raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 설정되지 않았습니다")
        analyzer = GeminiAnalyzer()
    else:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 백엔드: {request.backend}")

    async def analyze_task():
        state.is_analyzing = True
        try:
            # 키프레임 추출
            extractor = KeyframeExtractor()
            keyframes = extractor.extract(state.session)

            if not keyframes:
                return

            # 분석
            state.labels = await analyzer.analyze_batch(keyframes)

            # 패턴 감지
            if state.labels:
                detector = PatternDetector()
                patterns = detector.detect(state.labels)
                state.patterns = [
                    {
                        "actions": [a.model_dump() for a in p.actions],
                        "occurrences": p.occurrence_indices,
                        "count": p.count,
                    }
                    for p in patterns
                ]
        finally:
            state.is_analyzing = False

    # 백그라운드에서 비동기 작업 실행
    background_tasks.add_task(lambda: asyncio.run(analyze_task()))

    return {
        "message": "분석 시작",
        "backend": request.backend,
        "frame_count": len(state.session.frames),
        "event_count": len(state.session.events),
    }


@app.get("/labels")
async def get_labels():
    """분석된 액션 라벨 조회"""
    return {
        "count": len(state.labels),
        "labels": [label.model_dump() for label in state.labels],
    }


@app.get("/patterns")
async def get_patterns():
    """감지된 패턴 조회"""
    return {
        "count": len(state.patterns),
        "patterns": state.patterns,
    }
