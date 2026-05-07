# Project Memory — all-in-one-sis

**Type:** project_active
**Created:** May 6, 2026
**Tech Stack:** Python/FastAPI, Next.js 14, React Native, PostgreSQL, Redis

## Key Facts
- Modern educational platform combining SIS + LMS + AI
- Multi-tenant SaaS architecture
- 4 user roles: Admin, Teacher, Student, Parent
- 8 main modules: SIS, LMS, Attendance, Gradebook, Scheduling, Fees, AI, Communication

## Architecture
- API: FastAPI on port 8000
- Web: Next.js 14 on port 3000
- DB: PostgreSQL
- Cache: Redis
- Storage: S3/MinIO
- Real-time: WebSocket

## Important Links
- SPEC.md: Full specification
- task_plan.md: Roadmap
- Repository research: ../SIS_RESEARCH.md

## Current Phase
Phase 1: Foundation (Project Initialization)

## Decisions Made
- Using FastAPI over Django/FastAPI for async performance
- Next.js App Router over Pages Router
- shadcn/ui for components
- PostgreSQL with SQLAlchemy + Alembic
- JWT auth with Redis sessions
- Docker-first deployment

## Known Constraints
- Must support offline/PWA for mobile
- Need FERPA/GDPR consideration for student data
- Multi-school isolation required
