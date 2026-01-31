"""Supabase 통합 테스트

실제 Supabase DB에 연결하여 CRUD 작업을 검증합니다.

실행 방법:
    uv run pytest tests/test_supabase_integration.py -v

주의:
    - 실제 DB를 사용하므로 테스트 데이터가 생성됩니다
    - 테스트 후 자동으로 데이터를 정리합니다
    - SUPABASE_URL과 SUPABASE_KEY 환경변수가 필요합니다
"""

import uuid
from datetime import datetime

import pytest

from shadow.api.errors import ErrorCode, ShadowAPIError
from shadow.api.repositories import (
    HITLRepository,
    ObservationRepository,
    SessionRepository,
    SpecRepository,
)
from shadow.core.database import Database


@pytest.fixture(scope="module")
def check_db_configured():
    """DB 설정 확인"""
    if not Database.is_configured():
        pytest.skip("Supabase가 설정되지 않았습니다. .env 파일을 확인하세요.")


@pytest.fixture(scope="module")
def db_client(check_db_configured):
    """Supabase 클라이언트 fixture"""
    return Database.get_client()


@pytest.fixture
def test_user_id():
    """테스트용 사용자 ID"""
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def cleanup_sessions(db_client, test_user_id):
    """테스트 후 세션 정리"""
    yield
    # 테스트에서 생성된 세션 삭제
    try:
        db_client.table("sessions").delete().eq("user_id", test_user_id).execute()
    except Exception as e:
        print(f"세션 정리 실패: {e}")


@pytest.fixture
def cleanup_specs(db_client):
    """테스트 후 명세서 정리"""
    created_spec_ids = []

    def track_spec(spec_id):
        created_spec_ids.append(spec_id)

    yield track_spec

    # 테스트에서 생성된 명세서 삭제
    for spec_id in created_spec_ids:
        try:
            db_client.table("agent_specs").delete().eq("id", spec_id).execute()
        except Exception as e:
            print(f"명세서 정리 실패 ({spec_id}): {e}")


@pytest.fixture
def cleanup_questions(db_client):
    """테스트 후 HITL 질문 정리"""
    created_question_ids = []

    def track_question(question_id):
        created_question_ids.append(question_id)

    yield track_question

    # 테스트에서 생성된 질문 삭제
    for question_id in created_question_ids:
        try:
            # 먼저 응답 삭제
            db_client.table("hitl_answers").delete().eq("question_id", question_id).execute()
            # 질문 삭제
            db_client.table("hitl_questions").delete().eq("id", question_id).execute()
        except Exception as e:
            print(f"질문 정리 실패 ({question_id}): {e}")


# ====== DB 연결 테스트 ======


class TestDatabaseConnection:
    """데이터베이스 연결 테스트"""

    def test_db_connection(self, db_client):
        """DB 연결 확인"""
        assert db_client is not None
        assert Database.is_configured()

    @pytest.mark.asyncio
    async def test_connection_test(self):
        """연결 테스트 함수"""
        result = await Database.test_connection()
        assert result["status"] in ["connected", "error"]


# ====== Session Repository 테스트 ======


class TestSessionRepository:
    """Session CRUD 테스트"""

    def test_create_session(self, db_client, test_user_id, cleanup_sessions):
        """세션 생성 테스트"""
        repo = SessionRepository(db_client)

        session = repo.create_session(test_user_id)

        assert session is not None
        assert session["user_id"] == test_user_id
        assert session["status"] == "active"
        assert session["event_count"] == 0
        assert session["observation_count"] == 0
        assert "id" in session
        assert "start_time" in session

        print(f"\n✓ 세션 생성 성공: {session['id']}")

    def test_get_session(self, db_client, test_user_id, cleanup_sessions):
        """세션 조회 테스트"""
        repo = SessionRepository(db_client)

        # 세션 생성
        created_session = repo.create_session(test_user_id)
        session_id = created_session["id"]

        # 세션 조회
        session = repo.get_session(session_id)

        assert session is not None
        assert session["id"] == session_id
        assert session["user_id"] == test_user_id

        print(f"\n✓ 세션 조회 성공: {session_id}")

    def test_get_nonexistent_session(self, db_client):
        """존재하지 않는 세션 조회 시 에러"""
        repo = SessionRepository(db_client)

        with pytest.raises(ShadowAPIError) as exc_info:
            repo.get_session("nonexistent_session_id")

        assert exc_info.value.error_code == ErrorCode.E201

        print("\n✓ 존재하지 않는 세션 에러 처리 확인")

    def test_update_session_status(self, db_client, test_user_id, cleanup_sessions):
        """세션 상태 업데이트 테스트"""
        repo = SessionRepository(db_client)

        # 세션 생성
        created_session = repo.create_session(test_user_id)
        session_id = created_session["id"]

        # 상태를 completed로 변경
        updated_session = repo.update_session_status(session_id, "completed")

        assert updated_session["status"] == "completed"
        assert "end_time" in updated_session

        print(f"\n✓ 세션 상태 업데이트 성공: {session_id} -> completed")

    def test_increment_counts(self, db_client, test_user_id, cleanup_sessions):
        """세션 카운트 증가 테스트"""
        repo = SessionRepository(db_client)

        # 세션 생성
        created_session = repo.create_session(test_user_id)
        session_id = created_session["id"]

        # 카운트 증가
        updated_session = repo.increment_counts(
            session_id, event_count=5, observation_count=3
        )

        assert updated_session["event_count"] == 5
        assert updated_session["observation_count"] == 3

        # 추가 증가
        updated_session = repo.increment_counts(
            session_id, event_count=2, observation_count=1
        )

        assert updated_session["event_count"] == 7
        assert updated_session["observation_count"] == 4

        print(f"\n✓ 세션 카운트 증가 성공: events={7}, observations={4}")

    def test_get_active_session(self, db_client, test_user_id, cleanup_sessions):
        """활성 세션 조회 테스트"""
        repo = SessionRepository(db_client)

        # 세션 생성
        created_session = repo.create_session(test_user_id)

        # 활성 세션 조회
        active_session = repo.get_active_session(test_user_id)

        assert active_session is not None
        assert active_session["id"] == created_session["id"]
        assert active_session["status"] == "active"

        print(f"\n✓ 활성 세션 조회 성공: {active_session['id']}")


# ====== Spec Repository 테스트 ======


class TestSpecRepository:
    """Spec CRUD 테스트"""

    def test_create_spec(self, db_client, cleanup_specs):
        """명세서 생성 테스트"""
        repo = SpecRepository(db_client)

        spec_id = str(uuid.uuid4())
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"
        content = {
            "name": "테스트 명세서",
            "description": "테스트용 명세서입니다",
            "steps": [{"order": 1, "action": "test"}],
        }

        spec = repo.create_spec(
            spec_id=spec_id, pattern_id=pattern_id, version="0.1.0", content=content
        )

        cleanup_specs(spec_id)

        assert spec is not None
        assert spec["id"] == spec_id
        assert spec["pattern_id"] == pattern_id
        assert spec["version"] == "0.1.0"
        assert spec["status"] == "draft"
        assert spec["content"] == content

        print(f"\n✓ 명세서 생성 성공: {spec_id}")

    def test_get_spec(self, db_client, cleanup_specs):
        """명세서 조회 테스트"""
        repo = SpecRepository(db_client)

        # 명세서 생성
        spec_id = str(uuid.uuid4())
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"
        created_spec = repo.create_spec(
            spec_id=spec_id,
            pattern_id=pattern_id,
            version="0.1.0",
            content={"test": "data"},
        )

        cleanup_specs(spec_id)

        # 명세서 조회
        spec = repo.get_spec(spec_id)

        assert spec is not None
        assert spec["id"] == spec_id

        print(f"\n✓ 명세서 조회 성공: {spec_id}")

    def test_update_spec(self, db_client, cleanup_specs):
        """명세서 업데이트 테스트"""
        repo = SpecRepository(db_client)

        # 명세서 생성
        spec_id = str(uuid.uuid4())
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"
        repo.create_spec(
            spec_id=spec_id,
            pattern_id=pattern_id,
            version="0.1.0",
            content={"old": "content"},
        )

        cleanup_specs(spec_id)

        # 명세서 업데이트
        new_content = {"new": "content", "updated": True}
        updated_spec = repo.update_spec(
            spec_id=spec_id, content=new_content, change_summary="테스트 업데이트"
        )

        assert updated_spec["content"] == new_content

        print(f"\n✓ 명세서 업데이트 성공: {spec_id}")

    def test_list_specs(self, db_client, cleanup_specs):
        """명세서 목록 조회 테스트"""
        repo = SpecRepository(db_client)

        # 명세서 2개 생성
        spec_id1 = str(uuid.uuid4())
        spec_id2 = str(uuid.uuid4())
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"

        repo.create_spec(
            spec_id=spec_id1, pattern_id=pattern_id, version="0.1.0", content={}
        )
        repo.create_spec(
            spec_id=spec_id2, pattern_id=pattern_id, version="0.2.0", content={}
        )

        cleanup_specs(spec_id1)
        cleanup_specs(spec_id2)

        # 목록 조회
        specs = repo.list_specs(status="draft", limit=10)

        assert isinstance(specs, list)
        # 최소 2개는 있어야 함 (방금 생성한 것들)
        spec_ids = [s["id"] for s in specs]
        assert spec_id1 in spec_ids
        assert spec_id2 in spec_ids

        print(f"\n✓ 명세서 목록 조회 성공: {len(specs)}개")


# ====== HITL Repository 테스트 ======


class TestHITLRepository:
    """HITL CRUD 테스트"""

    def test_create_question(self, db_client, cleanup_questions):
        """HITL 질문 생성 테스트"""
        repo = HITLRepository(db_client)

        question_id = str(uuid.uuid4())
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"

        question = repo.create_question(
            question_id=question_id,
            pattern_id=pattern_id,
            question_type="hypothesis",
            question_text="이것은 테스트 질문입니다",
            options=[
                {"id": "opt1", "label": "예", "action": "confirm"},
                {"id": "opt2", "label": "아니오", "action": "reject"},
            ],
            allows_freetext=False,
            priority=3,
        )

        cleanup_questions(question_id)

        assert question is not None
        assert question["id"] == question_id
        assert question["pattern_id"] == pattern_id
        assert question["type"] == "hypothesis"
        assert question["status"] == "pending"

        print(f"\n✓ HITL 질문 생성 성공: {question_id}")

    def test_get_pending_questions(self, db_client, cleanup_questions):
        """대기 중인 질문 조회 테스트"""
        repo = HITLRepository(db_client)

        # 질문 생성
        question_id = str(uuid.uuid4())
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"

        repo.create_question(
            question_id=question_id,
            pattern_id=pattern_id,
            question_type="hypothesis",
            question_text="테스트 질문",
            options=[],
            priority=5,
        )

        cleanup_questions(question_id)

        # 대기 중인 질문 조회
        questions = repo.get_pending_questions(limit=10)

        assert isinstance(questions, list)
        question_ids = [q["id"] for q in questions]
        assert question_id in question_ids

        print(f"\n✓ 대기 중인 질문 조회 성공: {len(questions)}개")

    def test_create_answer(self, db_client, cleanup_questions):
        """HITL 응답 생성 테스트"""
        repo = HITLRepository(db_client)

        # 먼저 질문 생성
        question_id = str(uuid.uuid4())
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"

        repo.create_question(
            question_id=question_id,
            pattern_id=pattern_id,
            question_type="hypothesis",
            question_text="테스트 질문",
            options=[{"id": "opt1", "label": "예", "action": "confirm"}],
        )

        cleanup_questions(question_id)

        # 응답 생성
        answer_id = str(uuid.uuid4())
        answer = repo.create_answer(
            answer_id=answer_id,
            question_id=question_id,
            user_id="test_user",
            response_type="button",
            selected_option_id="opt1",
            freetext=None,
        )

        assert answer is not None
        assert answer["question_id"] == question_id
        assert answer["user_id"] == "test_user"

        # 질문 상태가 answered로 변경되었는지 확인
        question = repo.get_question(question_id)
        assert question["status"] == "answered"

        print(f"\n✓ HITL 응답 생성 성공: {answer_id}")


# ====== 통합 워크플로우 테스트 ======


class TestIntegrationWorkflow:
    """전체 워크플로우 통합 테스트"""

    def test_full_workflow(self, db_client, test_user_id, cleanup_sessions, cleanup_specs):
        """세션 생성 → 관찰 → 명세서 생성 전체 플로우"""
        session_repo = SessionRepository(db_client)
        spec_repo = SpecRepository(db_client)

        # 1. 세션 생성
        session = session_repo.create_session(test_user_id)
        session_id = session["id"]
        print(f"\n1. 세션 생성: {session_id}")

        # 2. 세션에 이벤트 추가
        session_repo.increment_counts(session_id, event_count=10, observation_count=5)
        print("2. 이벤트 추가 완료")

        # 3. 명세서 생성
        spec_id = str(uuid.uuid4())
        pattern_id = f"pattern_{uuid.uuid4().hex[:8]}"
        spec = spec_repo.create_spec(
            spec_id=spec_id,
            pattern_id=pattern_id,
            version="1.0.0",
            content={
                "name": "통합 테스트 명세서",
                "session_id": session_id,
                "steps": [],
            },
        )
        cleanup_specs(spec_id)
        print(f"3. 명세서 생성: {spec_id}")

        # 4. 세션 종료
        session_repo.update_session_status(session_id, "completed")
        print("4. 세션 종료")

        # 검증
        final_session = session_repo.get_session(session_id)
        assert final_session["status"] == "completed"
        assert final_session["event_count"] == 10
        assert final_session["observation_count"] == 5

        final_spec = spec_repo.get_spec(spec_id)
        assert final_spec["version"] == "1.0.0"

        print("\n✓ 전체 워크플로우 테스트 성공!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
