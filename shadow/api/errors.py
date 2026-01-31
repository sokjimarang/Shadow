"""API 에러 정의 및 핸들러

API 명세서의 에러 코드 체계 (E001~E203) 구현
"""

from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode(str, Enum):
    """API 에러 코드 (명세서 기준)"""

    # 일반 에러 (E001~E005)
    E001 = "E001"  # 내부 서버 오류
    E002 = "E002"  # 잘못된 요청 형식
    E003 = "E003"  # 인증 실패
    E004 = "E004"  # 리소스 없음
    E005 = "E005"  # 요청 제한 초과

    # 외부 API 에러 (E101~E103)
    E101 = "E101"  # VLM API 호출 실패
    E102 = "E102"  # LLM API 호출 실패
    E103 = "E103"  # Slack API 호출 실패

    # 리소스 에러 (E201~E203)
    E201 = "E201"  # 세션 없음
    E202 = "E202"  # 명세서 없음
    E203 = "E203"  # 질문 없음


class ErrorDetail(BaseModel):
    """에러 상세 정보"""

    code: ErrorCode
    message: str
    details: str | None = None
    timestamp: str


class ErrorResponse(BaseModel):
    """에러 응답 모델"""

    error: ErrorDetail


class ShadowAPIError(HTTPException):
    """Shadow API 커스텀 예외"""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: str | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail=message)


# 에러 코드별 HTTP 상태 코드 매핑
ERROR_STATUS_MAP: dict[ErrorCode, int] = {
    ErrorCode.E001: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.E002: status.HTTP_400_BAD_REQUEST,
    ErrorCode.E003: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.E004: status.HTTP_404_NOT_FOUND,
    ErrorCode.E005: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.E101: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.E102: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.E103: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.E201: status.HTTP_400_BAD_REQUEST,
    ErrorCode.E202: status.HTTP_400_BAD_REQUEST,
    ErrorCode.E203: status.HTTP_400_BAD_REQUEST,
}


def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: str | None = None,
) -> ErrorResponse:
    """에러 응답 객체 생성"""
    return ErrorResponse(
        error=ErrorDetail(
            code=error_code,
            message=message,
            details=details,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    )


async def shadow_api_error_handler(request: Request, exc: ShadowAPIError) -> JSONResponse:
    """Shadow API 에러 핸들러"""
    error_response = create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )

    return JSONResponse(
        status_code=ERROR_STATUS_MAP.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR),
        content=error_response.model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """일반 예외 핸들러 (예상하지 못한 에러)"""
    error_response = create_error_response(
        error_code=ErrorCode.E001,
        message="내부 서버 오류가 발생했습니다",
        details=str(exc),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )
