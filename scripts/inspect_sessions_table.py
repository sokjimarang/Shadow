"""sessions 테이블 구조 확인"""

from shadow.core.database import Database


def main():
    db = Database.get_client()

    # 1. 테스트 세션 생성 (최소 필드만)
    print("=" * 60)
    print("sessions 테이블 구조 확인")
    print("=" * 60)

    # 먼저 어떤 필드가 필요한지 확인하기 위해 기본 insert 시도
    test_data_variants = [
        {"user_id": "test_user_minimal"},
        {"user_id": "test_user", "status": "active"},
        {"user_id": "test_user", "status": "active", "start_time": "2025-01-31T00:00:00Z"},
    ]

    for i, test_data in enumerate(test_data_variants, 1):
        print(f"\n시도 {i}: {test_data}")
        try:
            response = db.table("sessions").insert(test_data).execute()
            print(f"✓ 성공: {response.data[0]}")

            # 생성된 세션 ID로 조회하여 전체 컬럼 확인
            session_id = response.data[0].get("id")
            if session_id:
                full_response = db.table("sessions").select("*").eq("id", session_id).execute()
                if full_response.data:
                    print(f"\n전체 컬럼: {list(full_response.data[0].keys())}")
                    print(f"전체 데이터: {full_response.data[0]}")

                # 정리
                db.table("sessions").delete().eq("id", session_id).execute()
                print(f"✓ 테스트 세션 삭제 완료")

            break  # 성공하면 더 이상 시도하지 않음

        except Exception as e:
            print(f"✗ 실패: {e}")

    # 2. patterns 테이블도 확인
    print("\n" + "=" * 60)
    print("patterns 테이블 구조 확인")
    print("=" * 60)

    test_pattern = {
        "name": "test_pattern",
        "description": "Test pattern for schema inspection",
    }

    print(f"\n시도: {test_pattern}")
    try:
        response = db.table("patterns").insert(test_pattern).execute()
        print(f"✓ 성공: {response.data[0]}")

        # 전체 컬럼 확인
        pattern_id = response.data[0].get("id")
        if pattern_id:
            full_response = db.table("patterns").select("*").eq("id", pattern_id).execute()
            if full_response.data:
                print(f"\n전체 컬럼: {list(full_response.data[0].keys())}")
                print(f"전체 데이터: {full_response.data[0]}")

            # 정리
            db.table("patterns").delete().eq("id", pattern_id).execute()
            print(f"✓ 테스트 패턴 삭제 완료")

    except Exception as e:
        print(f"✗ 실패: {e}")


if __name__ == "__main__":
    main()
