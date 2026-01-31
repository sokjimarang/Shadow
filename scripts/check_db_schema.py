"""Supabase DB 스키마 확인 스크립트

실제 DB 테이블과 컬럼을 확인하여 코드와 스키마 불일치를 파악합니다.

실행 방법:
    uv run python scripts/check_db_schema.py
"""

from shadow.core.database import Database


def check_table_schema(db, table_name: str):
    """테이블 스키마 확인"""
    try:
        # 빈 쿼리로 컬럼 정보 가져오기
        response = db.table(table_name).select("*").limit(0).execute()

        print(f"\n✓ {table_name} 테이블 존재")
        print(f"  응답: {response}")

        # 실제 데이터 1개만 가져와서 컬럼 확인
        sample_response = db.table(table_name).select("*").limit(1).execute()

        if sample_response.data:
            sample = sample_response.data[0]
            print(f"  컬럼: {list(sample.keys())}")
        else:
            print("  (데이터 없음 - 컬럼 확인 불가)")

        return True

    except Exception as e:
        print(f"\n✗ {table_name} 테이블 오류")
        print(f"  에러: {e}")
        return False


def main():
    """메인 함수"""
    print("=" * 60)
    print("Supabase DB 스키마 확인")
    print("=" * 60)

    # DB 연결
    if not Database.is_configured():
        print("\n❌ Supabase가 설정되지 않았습니다.")
        print("   .env 파일에 SUPABASE_URL과 SUPABASE_KEY를 설정하세요.")
        return

    db = Database.get_client()
    print(f"\n✓ DB 연결 성공: {db}")

    # 테스트할 테이블 목록 (우리 코드에서 사용하는 테이블)
    tables = [
        "users",
        "sessions",
        "screenshots",
        "input_events",
        "observations",
        "labeled_actions",
        "patterns",
        "hitl_questions",
        "hitl_answers",
        "agent_specs",
        "spec_history",
    ]

    print("\n" + "=" * 60)
    print("테이블 존재 여부 및 스키마 확인")
    print("=" * 60)

    results = {}
    for table in tables:
        results[table] = check_table_schema(db, table)

    # 요약
    print("\n" + "=" * 60)
    print("요약")
    print("=" * 60)

    existing_tables = [t for t, exists in results.items() if exists]
    missing_tables = [t for t, exists in results.items() if not exists]

    print(f"\n✓ 존재하는 테이블 ({len(existing_tables)}개):")
    for table in existing_tables:
        print(f"  - {table}")

    if missing_tables:
        print(f"\n✗ 존재하지 않는 테이블 ({len(missing_tables)}개):")
        for table in missing_tables:
            print(f"  - {table}")

    # 실제 Supabase에 있는 모든 테이블 목록 가져오기 (가능하면)
    print("\n" + "=" * 60)
    print("실제 DB에 있는 모든 테이블 확인 (public 스키마)")
    print("=" * 60)

    try:
        # PostgreSQL information_schema 쿼리
        # Supabase는 PostgREST를 사용하므로 직접 쿼리 불가
        # 대신 알려진 테이블들만 체크
        print("\n(Supabase PostgREST는 모든 테이블 목록을 직접 조회할 수 없습니다)")
        print("위의 테이블 체크 결과를 참고하세요.")

    except Exception as e:
        print(f"에러: {e}")


if __name__ == "__main__":
    main()
