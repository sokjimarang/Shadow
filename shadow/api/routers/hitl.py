"""HITL API 라우터

shadow-web과의 연동을 위한 HITL 질문/응답 관리 엔드포인트
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, status
from supabase import Client

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.api.models import HITLQuestionResponse, HITLQuestionsResponse, SuccessResponse
from shadow.api.repositories import HITLRepository
from shadow.core.database import get_db

router = APIRouter(prefix="/api/hitl", tags=["hitl"])


# ====== POST /api/hitl/response ======


@router.post("/response", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def receive_hitl_response(
    response_data: HITLQuestionResponse, db: Client = Depends(get_db)
) -> SuccessResponse:
    """HITL 응답 수신 (shadow-web → shadow-py)

    Args:
        response_data: 사용자 응답 데이터
        db: Supabase 클라이언트

    Returns:
        처리 결과

    Raises:
        ShadowAPIError: 처리 실패 시
    """
    hitl_repo = HITLRepository(db)

    try:
        # 질문 존재 확인
        hitl_repo.get_question(response_data.question_id)

        # 응답 저장
        hitl_repo.create_answer(
            answer_id=str(uuid.uuid4()),
            question_id=response_data.question_id,
            user_id=response_data.user_id,
            response_type=response_data.response_type,
            selected_option_id=response_data.selected_option_id,
            freetext=response_data.freetext,
        )

        # TODO: 응답 해석 및 명세서 업데이트 로직
        # 이 부분은 향후 InterpretedAnswer 생성 및 Spec 업데이트로 확장

        return SuccessResponse(status="ok", message="응답이 성공적으로 처리되었습니다")

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="HITL 응답 처리 중 오류 발생",
            details=str(e),
        )


# ====== GET /api/hitl/questions ======


@router.get("/questions", response_model=HITLQuestionsResponse, status_code=status.HTTP_200_OK)
async def get_pending_questions(
    limit: int = 10, db: Client = Depends(get_db)
) -> HITLQuestionsResponse:
    """대기 중인 HITL 질문 목록 조회

    Args:
        limit: 최대 개수
        db: Supabase 클라이언트

    Returns:
        질문 목록

    Raises:
        ShadowAPIError: 조회 실패 시
    """
    hitl_repo = HITLRepository(db)

    try:
        questions = hitl_repo.get_pending_questions(limit=limit)

        # 응답 형식에 맞게 변환
        from shadow.api.models import HITLQuestionItem

        question_items = [
            HITLQuestionItem(
                id=q["id"],
                pattern_id=q["pattern_id"],
                question_text=q["question_text"],
                status=q["status"],
                created_at=q.get("created_at", datetime.utcnow().isoformat()),
            )
            for q in questions
        ]

        return HITLQuestionsResponse(count=len(question_items), questions=question_items)

    except ShadowAPIError:
        raise
    except Exception as e:
        raise ShadowAPIError(
            error_code=ErrorCode.E001,
            message="질문 목록 조회 중 오류 발생",
            details=str(e),
        )
