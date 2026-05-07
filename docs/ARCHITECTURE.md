# All-in-One SIS Architecture

## System Overview

All-in-One SIS is a modern, multi-tenant Student Information System built with:

- **Backend**: Python/FastAPI (async)
- **Frontend**: Next.js 14 (App Router)
- **Mobile**: React Native (Expo)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Storage**: S3/MinIO

## Architecture Layers

### 1. API Layer (FastAPI)
- Async REST API with Pydantic validation
- JWT authentication with role-based access
- 12 main routers covering all SIS modules
- 173+ API endpoints

### 2. Data Layer
- SQLAlchemy 2.0 async ORM
- Alembic for migrations
- PostgreSQL with JSONB for flexible data
- Redis for sessions and caching

### 3. Frontend Layer (Next.js 14)
- App Router with Server Components
- Tailwind CSS + shadcn/ui
- NextAuth.js for authentication
- React Query for data fetching

### 4. Mobile Layer (React Native/Expo)
- Tab-based navigation
- Native iOS/Android builds
- Offline-first architecture

## Module Architecture

### SIS Module
- Student Management
- Teacher Management  
- Attendance Tracking
- Gradebook & Exams
- Fee Management
- Scheduling

### LMS Module
- Course Management
- Content Delivery
- Assignments & Quizzes
- Progress Tracking

### AI Module
- AI Tutor Chat
- Student Analytics
- At-Risk Prediction

## Security

- JWT tokens with short expiry
- bcrypt password hashing
- Role-based access control (RBAC)
- CORS configuration
- Rate limiting
- SQL injection prevention via ORM

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.