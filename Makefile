# Shadow-py Makefile
# Database management commands

.PHONY: db-start db-stop db-status db-reset db-push db-pull db-diff db-migration-new db-migration-list

# Supabase 로컬 환경 시작
db-start:
	@echo "Starting Supabase local environment..."
	supabase start

# Supabase 로컬 환경 중지
db-stop:
	@echo "Stopping Supabase local environment..."
	supabase stop

# Supabase 상태 확인
db-status:
	@echo "Checking Supabase status..."
	supabase status

# 로컬 DB 초기화 (모든 마이그레이션 재실행)
db-reset:
	@echo "Resetting local database..."
	supabase db reset

# 프로덕션 DB에 마이그레이션 배포
db-push:
	@echo "Pushing migrations to production..."
	supabase db push

# 프로덕션 DB 스키마 가져오기
db-pull:
	@echo "Pulling schema from production..."
	supabase db pull

# 로컬-프로덕션 차이 확인
db-diff:
	@echo "Checking differences between local and production..."
	supabase db diff

# 새로운 마이그레이션 파일 생성
db-migration-new:
	@read -p "Enter migration name: " name; \
	echo "Creating new migration: $$name"; \
	supabase migration new $$name

# 마이그레이션 목록 확인
db-migration-list:
	@echo "Listing migrations..."
	supabase migration list
