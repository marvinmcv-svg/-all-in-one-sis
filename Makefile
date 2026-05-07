.PHONY: migrate create-migration rollback db-init db-reset help

# Database migration commands
# Usage: make migrate, make create-migration msg="description", make rollback

# Apply all pending migrations
migrate:
	cd apps/api && alembic upgrade head

# Create a new migration with autogenerate
# Usage: make create-migration msg="add users table"
create-migration:
	cd apps/api && alembic revision --autogenerate -m "$(msg)"

# Rollback the last migration
rollback:
	cd apps/api && alembic downgrade -1

# Rollback to a specific revision
# Usage: make rollback-to rev=abc123
rollback-to:
	cd apps/api && alembic downgrade $(rev)

# Show current migration
current:
	cd apps/api && alembic current

# Show migration history
history:
	cd apps/api && alembic history

# Show pending migrations (SQL mode)
sql:
	cd apps/api && alembic upgrade --sql

# Initialize database with tables (alternative to migrations)
db-init:
	cd apps/api && python -c "import asyncio; from database import init_db; asyncio.run(init_db())"

# Reset database (WARNING: drops all tables)
db-reset:
	cd apps/api && alembic downgrade base && alembic upgrade head

help:
	@echo "Database Migration Commands:"
	@echo "  make migrate              - Apply all pending migrations"
	@echo "  make create-migration msg='description' - Create new migration"
	@echo "  make rollback             - Rollback last migration"
	@echo "  make rollback-to rev=<id>  - Rollback to specific revision"
	@echo "  make current              - Show current migration"
	@echo "  make history              - Show migration history"
	@echo "  make sql                  - Show SQL for pending migrations"
	@echo "  make db-init              - Initialize database tables"
	@echo "  make db-reset             - Reset database (WARNING: drops all tables)"
