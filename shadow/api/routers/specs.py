"""명세서 API 라우터

에이전트 명세서 CRUD 엔드포인트
"""

import uuid

from fastapi import APIRouter, Depends, status
from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.api.models import (
    SpecCreateRequest,
    SpecDetailResponse,
    SpecListResponse,
    SpecSummary,
    SpecUpdateRequest,
    SuccessResponse,
)
from shadow.api.repositories import SpecRepository
from shadow.core.database import get_db

router = APIRouter(prefix="/api/specs", tags=["specs"])


# ====== GET /api/specs ======


@router.get("", response_model=SpecListResponse, status_code=status.HTTP_200_OK)
async def list_specs(
    status_filter: str | None = None, limit: int = 100, db: Client = Depends(get_db)
) -> SpecListResponse:
    """명세서 목록 조회

    Args:
        status_filter: 상태 필터 (None이면 전체)
        limit: 최대 개수
        db: Supabase 클라이언트

    Returns:
        명세서 목록

    Raises:
        ShadowAPIError: 조회 실패 시
    """
    spec_repo = SpecRepository(db)

    try:
        specs = spec_repo.list_specs(status=status_filter, limit=limit)

        spec_summaries = [
            SpecSummary(
                id=s["id"],
                pattern_id=s["pattern_id"],
                version=s["version"],
                status=s["status"],
                created_at=s.get("created_at", ""),
                updated_at=s.get("updated_at", ""),
            )
            for s in specs
        ]

        return SpecListResponse(count=len(spec_summaries), specs=spec_summaries)

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="명세서 목록 조회 중 오류 발생",
            details=str(e),
        )


# ====== GET /api/specs/{spec_id} ======


@router.get("/{spec_id}", response_model=SpecDetailResponse, status_code=status.HTTP_200_OK)
async def get_spec(spec_id: str, db: Client = Depends(get_db)) -> SpecDetailResponse:
    """명세서 상세 조회

    Args:
        spec_id: 명세서 ID
        db: Supabase 클라이언트

    Returns:
        명세서 상세 정보

    Raises:
        ShadowAPIError: 명세서 없음 또는 조회 실패
    """
    spec_repo = SpecRepository(db)

    try:
        spec = spec_repo.get_spec(spec_id)

        return SpecDetailResponse(
            id=spec["id"],
            pattern_id=spec["pattern_id"],
            version=spec["version"],
            created_at=spec.get("created_at", ""),
            updated_at=spec.get("updated_at", ""),
            status=spec["status"],
            content=spec.get("content", {}),
        )

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="명세서 조회 중 오류 발생",
            details=str(e),
        )


# ====== POST /api/specs ======


@router.post("", response_model=SpecDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_spec(
    request: SpecCreateRequest, db: Client = Depends(get_db)
) -> SpecDetailResponse:
    """명세서 생성

    Args:
        request: 명세서 생성 요청
        db: Supabase 클라이언트

    Returns:
        생성된 명세서

    Raises:
        ShadowAPIError: 생성 실패
    """
    spec_repo = SpecRepository(db)

    try:
        spec_id = str(uuid.uuid4())
        version = "0.1.0"  # 초기 버전

        spec = spec_repo.create_spec(
            spec_id=spec_id,
            pattern_id=request.pattern_id,
            version=version,
            content=request.content,
        )

        return SpecDetailResponse(
            id=spec["id"],
            pattern_id=spec["pattern_id"],
            version=spec["version"],
            created_at=spec.get("created_at", ""),
            updated_at=spec.get("updated_at", ""),
            status=spec["status"],
            content=spec.get("content", {}),
        )

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="명세서 생성 중 오류 발생",
            details=str(e),
        )


# ====== PUT /api/specs/{spec_id} ======


@router.put("/{spec_id}", response_model=SpecDetailResponse, status_code=status.HTTP_200_OK)
async def update_spec(
    spec_id: str, request: SpecUpdateRequest, db: Client = Depends(get_db)
) -> SpecDetailResponse:
    """명세서 업데이트

    Args:
        spec_id: 명세서 ID
        request: 업데이트 요청
        db: Supabase 클라이언트

    Returns:
        업데이트된 명세서

    Raises:
        ShadowAPIError: 업데이트 실패
    """
    spec_repo = SpecRepository(db)

    try:
        # TODO: 버전 증가 로직 (semver)
        # 현재는 버전 유지, 향후 변경 내용에 따라 major/minor/patch 증가

        spec = spec_repo.update_spec(
            spec_id=spec_id,
            content=request.content,
            version=None,  # 현재 버전 유지
            change_summary=request.change_summary,
        )

        return SpecDetailResponse(
            id=spec["id"],
            pattern_id=spec["pattern_id"],
            version=spec["version"],
            created_at=spec.get("created_at", ""),
            updated_at=spec.get("updated_at", ""),
            status=spec["status"],
            content=spec.get("content", {}),
        )

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="명세서 업데이트 중 오류 발생",
            details=str(e),
        )
