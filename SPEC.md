# All-in-One SIS (Student Information System) — Specification

**Version:** 1.0.0
**Created:** May 6, 2026
**Type:** Full-stack Educational Management Platform

---

## 1. Vision & Goals

### North Star
Build a **modern, unified educational management platform** that combines:
- Full Student Information System (SIS) capabilities
- Learning Management System (LMS) features
- AI-powered tutoring and administrative automation
- Mobile-first experience for all stakeholders
- Multi-tenant SaaS architecture for single or multi-school deployment

### Target Users
1. **Administrators** — School leadership, data management, reports
2. **Teachers** — Gradebook, attendance, course content, communications
3. **Students** — Course access, grades, assignments, schedules
4. **Parents** — Real-time visibility into child's progress, attendance, announcements
5. **Super Admin** — Multi-school SaaS management

### Success Metrics
- Complete academic workflow from enrollment to graduation
- 95%+ feature coverage vs. top 10 analyzed systems
- Mobile-first responsive design
- AI assistant available for students and teachers
- Multi-tenant with isolated data per school

---

## 2. Technical Architecture

### Tech Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Backend API** | Python/FastAPI | Async performance, type safety, modern |
| **Database** | PostgreSQL | Reliability, JSONB, full-text search |
| **Cache/Sessions** | Redis | Fast sessions, real-time features |
| **Web Frontend** | Next.js 14 (App Router) | React, SSR, SEO, fast |
| **Mobile App** | React Native (Expo) | Cross-platform iOS/Android |
| **AI Engine** | LangChain + OpenAI/Gemini | Tutoring, auto-grading, analytics |
| **File Storage** | S3-compatible (Local/MinIO) | Documents, images, videos |
| **Search** | PostgreSQL full-text + pgvector | Student search, AI embeddings |
| **Real-time** | WebSocket (Socket.io) | Notifications, live updates |
| **Deployment** | Docker + Docker Compose | Consistent environments |

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTS                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Web App    │  │  Mobile App │  │  PWA         │          │
│  │  (Next.js)  │  │  (React     │  │  (Offline)   │          │
│  │             │  │   Native)   │  │             │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │ HTTPS/WSS
┌──────────────────────────┼──────────────────────────────────┐
│                     API GATEWAY                             │
│              (Nginx / Traefik reverse proxy)                 │
│         Rate limiting, Auth, SSL termination                 │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                    BACKEND SERVICES                          │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              FastAPI Application                    │     │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐        │     │
│  │  │ SIS Module│ │ LMS Module │ │  AI Module│        │     │
│  │  │           │ │           │ │           │        │     │
│  │  │ -Students │ │ -Courses  │ │ -Tutor    │        │     │
│  │  │ -Staff    │ │ -Content  │ │ -Grading  │        │     │
│  │  │ -Attendance│ │ -Quizzes  │ │ -Analytics│        │     │
│  │  │ -Grades   │ │ -Submissions│ │-Chatbot  │        │     │
│  │  │ -Scheduling│ │ -Certificates│ │         │        │     │
│  │  │ -Fees     │ │           │ │           │        │     │
│  │  └───────────┘ └───────────┘ └───────────┘        │     │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐        │     │
│  │  │ Auth      │ │ Notif.    │ │ Reports    │        │     │
│  │  │ (JWT/SSO) │ │ (Real-time)│ │ (Export)   │        │     │
│  │  └───────────┘ └───────────┘ └───────────┘        │     │
│  └─────────────────────────────────────────────────────┘     │
│           │                │                │                │
│  ┌────────┴────────────────┴────────────────┴────────┐       │
│  │              DATA LAYER                            │       │
│  │  PostgreSQL  │  Redis (Cache/Sessions)  │  S3/MinIO│       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema

### Core Entities

```
┌─────────────────────────────────────────────────────────────┐
│                    MULTI-TENANT LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Tenant (id, name, slug, logo_url, settings JSONB, created) │
│    └── School (id, tenant_id, name, address, phone,         │
│                email, timezone, academic_year, is_active)    │
│          ├── Branch (id, school_id, name, code)             │
│          ├── AcademicTerm (id, school_id, name, start_date, │
│          │                  end_date, is_current)          │
│          ├── GradeLevel (id, school_id, name, code,         │
│          │                  next_grade_id, sequence)        │
│          └── Department (id, school_id, name, head_teacher_id)
│
├─────────────────────────────────────────────────────────────┤
│                       PEOPLE                                 │
├─────────────────────────────────────────────────────────────┤
│  User (id, tenant_id, email, password_hash, role, is_active) │
│    └── Person (id, user_id, first_name, last_name,          │
│                gender, dob, phone, address, photo_url,      │
│                emergency_contact, emergency_phone)            │
│          ├── Student (id, person_id, student_id, admission_no│
│          │     grade_level_id, section_id, status,          │
│          │     father_name, mother_name, guardian_id)        │
│          │     └── Enrollment (id, student_id, academic_term│
│          │         grade_level_id, section_id, status,      │
│          │         roll_number)                             │
│          ├── Teacher (id, person_id, employee_id,           │
│          │     department_id, designation, salary)          │
│          │     └── TeacherAssignment (teacher_id, subject_id│
│          │         class_section_id, academic_term_id)       │
│          └── Parent (id, person_id, student_id, relationship│
│              occupation, income, education)                   │
│
├─────────────────────────────────────────────────────────────┤
│                    ACADEMICS                                 │
├─────────────────────────────────────────────────────────────┤
│  Subject (id, school_id, name, code, description, credit_hours│
│       type: THEORY/PRACTICAL)                                │
│  ClassSection (id, school_id, grade_level_id, name,         │
│       room_number, capacity, academic_term_id)               │
│       └── ClassSubject (id, class_section_id, subject_id,    │
│           teacher_assignment_id, is_active)                   │
│  Schedule (id, class_section_id, subject_id, teacher_id,     │
│       day_of_week, period_number, room_number,               │
│       start_time, end_time, academic_term_id)                │
│  TimetableTemplate (id, school_id, name, periods JSONB,      │
│       days JSONB)                                           │
│
├─────────────────────────────────────────────────────────────┤
│                   ATTENDANCE                                 │
├─────────────────────────────────────────────────────────────┤
│  AttendanceRecord (id, student_id, class_section_id,        │
│       academic_term_id, date, status: PRESENT/ABSENT/LATE,  │
│       excuse_id, marked_by_teacher_id, created_at)          │
│  AttendanceExcuse (id, student_id, start_date, end_date,    │
│       reason, approved_by_id, status)                       │
│  StaffAttendance (id, teacher_id, date, status,            │
│       marked_by_id, created_at)                             │
│
├─────────────────────────────────────────────────────────────┤
│                     GRADES                                   │
├─────────────────────────────────────────────────────────────┤
│  GradingSystem (id, school_id, name, type, is_default)      │
│       └── GradeScale (id, grading_system_id, letter,          │
│           min_percentage, max_percentage, grade_point)        │
│  ExamType (id, school_id, name, weight, description)         │
│  Exam (id, academic_term_id, class_section_id, subject_id,  │
│       exam_type_id, name, max_marks, exam_date, duration_mins│
│       is_published)                                          │
│       └── ExamResult (id, exam_id, student_id, marks_obtained│
│           grade_id, remarks, graded_by_teacher_id, graded_at)│
│  GradeReport (id, student_id, academic_term_id,                │
│       cumulative_gpa, rank, teacher_remarks, finalized_at)     │
│
├─────────────────────────────────────────────────────────────┤
│                       FEES                                   │
├─────────────────────────────────────────────────────────────┤
│  FeeStructure (id, school_id, academic_term_id, name,         │
│       amount, due_date, late_fee_per_day, is_mandatory)       │
│       └── FeeCategory (id, school_id, name, description)     │
│  StudentFee (id, student_id, fee_structure_id, amount,        │
│       discount_amount, paid_amount, status, due_date,        │
│       paid_at, payment_method, transaction_id)               │
│  Payment (id, student_fee_id, amount, method, transaction_ref│
│       received_by_id, collected_at)                         │
│
├─────────────────────────────────────────────────────────────┤
│                       LMS                                    │
├─────────────────────────────────────────────────────────────┤
│  Course (id, school_id, subject_id, teacher_id, name,        │
│       description, is_published, enrollment_type)            │
│       └── CourseEnrollment (id, course_id, student_id,       │
│           enrolled_at, completed_at, progress_percentage)    │
│  Chapter (id, course_id, title, description, order_index)  │
│       └── Lesson (id, chapter_id, title, content_type,      │
│           content_url, duration_mins, order_index, is_preview│
│           └── LessonProgress (id, lesson_id, student_id,     │
│               completed_at, time_spent_secs)                 │
│  Assignment (id, course_id, title, description, due_date,    │
│       max_marks, submission_type, allowed_extensions JSONB)  │
│       └── AssignmentSubmission (id, assignment_id, student_id│
│           file_url, submitted_at, marks_obtained,            │
│           feedback, graded_by_id, graded_at)                 │
│  Quiz (id, course_id, title, time_limit_mins, max_attempts, │
│       passing_percentage, is_published)                     │
│       └── QuizQuestion (id, quiz_id, question_text,         │
│           question_type, options JSONB, correct_answer JSONB │
│           marks, order_index)                               │
│           └── QuizAttempt (id, quiz_id, student_id,         │
│               started_at, submitted_at, score, passed)       │
│               └── QuizResponse (id, attempt_id, question_id, │
│                   answer JSONB, is_correct, marks_obtained)  │
│  Certificate (id, course_id, student_id, issued_at,          │
│       certificate_url, verify_code)                         │
│
├─────────────────────────────────────────────────────────────┤
│                   COMMUNICATIONS                             │
├─────────────────────────────────────────────────────────────┤
│  Notice (id, school_id, author_id, title, content,          │
│       priority, target_roles JSONB, class_section_ids JSONB │
│       publish_at, expires_at, is_published)                  │
│  Message (id, sender_id, recipient_id, subject, body,       │
│       is_read, sent_at, read_at)                            │
│  Announcement (id, school_id, title, body, target_audience │
│       publish_at, created_by_id)                             │
│
├─────────────────────────────────────────────────────────────┤
│                   AI MODULE                                  │
├─────────────────────────────────────────────────────────────┤
│  AIConversation (id, user_id, user_type, context,            │
│       messages JSONB, created_at, updated_at)                │
│  AIUsageLog (id, user_id, module, tokens_used,              │
│       response_time_ms, created_at)                          │
│  StudentAnalytics (id, student_id, academic_term_id,       │
│       attendance_rate, avg_marks, predicted_failure_risk,    │
│       engagement_score, generated_at)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Module Specifications

### 4.1 SIS Module

#### Student Management
- Student registration with comprehensive profile
- Admission number auto-generation
- Document upload (birth certificate, transcripts, photos)
- Medical information tracking
- Emergency contact management
- Student status (active, inactive, graduated, transferred, expelled)
- Bulk import via CSV/Excel
- Advanced search with filters

#### Staff Management
- Teacher and employee profiles
- Employee ID generation
- Department assignment
- Salary/scale tracking
- Leave management
- Performance records

#### Attendance System
- Daily attendance (Present/Absent/Late/Excuse)
- Period-wise attendance tracking
- Bulk attendance entry
- Excuse request and approval workflow
- Attendance reports (daily, monthly, perfect attendance)
- SMS/Email notification to parents for absences
- Staff attendance tracking

#### Gradebook
- Configurable grading systems (A-F, 1-10, percentage, GPA)
- Multiple exam types (FA, SA1, SA2, Terminal, Final)
- Weight-based grade calculation
- Subject-wise grades
- GPA calculation
- Class rank and section rank
- Progress reports (customizable templates)
- Report card generation (PDF export)
- Transcript generation

#### Scheduling
- Class timetable management
- Period/rotation setup
- Teacher availability
- Room allocation
- Conflict detection
- Student course selection (for higher ed)

#### Fee Management
- Fee structure setup (by grade, category)
- One-time and recurring fees
- Discount management (sibling, merit, financial aid)
- Payment collection (cash, card, online)
- Receipt generation
- Due date reminders
- Online payment gateway integration
- Outstanding reports
- Collection reports

### 4.2 LMS Module

#### Course Management
- Course creation with syllabus
- Chapter and lesson structure
- Multiple content types (video, PDF, text, embed)
- Enrollment settings (open, approval, paid)
- Course completion rules

#### Content Delivery
- Video hosting/streaming
- Document viewer
- SCORM support (future)
- Progress tracking per lesson
- Completion certificates

#### Assessment
- Quiz creation (multiple choice, true/false, short answer)
- Timed quizzes
- Assignment submission (file upload)
- Peer review (optional)
- Auto-grading for objective questions
- Manual grading with feedback
- Grade passback to SIS gradebook

#### Communication
- Course announcements
- Discussion forums
- Direct messaging
- Video conferencing integration (Zoom/Jitsi)

### 4.3 AI Module

#### AI Tutor
- 24/7 availability for student questions
- Context-aware responses based on course content
- Study recommendations
- Assignment hints (not answers)
- Language support

#### Smart Analytics
- Student performance prediction
- At-risk student identification
- Attendance pattern analysis
- Engagement scoring
- Personalized learning paths
- Dashboard visualizations

#### Administrative AI
- Auto-generation of progress reports
- Schedule optimization suggestions
- Fee default prediction
- Faculty workload analysis

### 4.4 Portal Module

#### Student Portal
- Dashboard (courses, assignments, attendance summary)
- Course catalog and enrollment
- Class schedule
- Grades and transcripts
- Assignment submission
- Quiz taking
- Announcements
- Messages
- AI tutor access

#### Teacher Portal
- Dashboard (classes, upcoming, pending grades)
- Attendance management
- Gradebook (own subjects)
- Assignment creation
- Quiz creation
- Course content management
- Messages
- Reports

#### Parent Portal
- Child's attendance
- Grades and progress
- Announcements
- Fee status
- Teacher messages
- Appointment scheduling

#### Admin Dashboard
- School overview
- Student management
- Staff management
- Attendance overview
- Fee collection
- Academic reports
- User management
- System settings
- Multi-school switcher (SaaS)

---

## 5. File Structure

```
all-in-one-sis/
├── .gitignore
├── README.md
├── LICENSE (AGPL-3.0)
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── Dockerfile.api
├── Dockerfile.web
├── .env.example
├── .env.test
├── .opencode/
│   └── memory/
│       ├── MEMORY.md
│       ├── task_plan.md
│       ├── findings.md
│       ├── progress.md
│       └── schema.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_SPEC.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
├── apps/
│   ├── api/                      # FastAPI Backend
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/               # SQLAlchemy/Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   ├── person.py
│   │   │   ├── student.py
│   │   │   ├── teacher.py
│   │   │   ├── parent.py
│   │   │   ├── academic.py
│   │   │   ├── attendance.py
│   │   │   ├── gradebook.py
│   │   │   ├── scheduling.py
│   │   │   ├── fees.py
│   │   │   ├── lms.py
│   │   │   ├── communication.py
│   │   │   └── ai.py
│   │   ├── schemas/              # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── student.py
│   │   │   ├── teacher.py
│   │   │   ├── attendance.py
│   │   │   ├── gradebook.py
│   │   │   ├── lms.py
│   │   │   └── common.py
│   │   ├── api/                 # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── students.py
│   │   │   ├── teachers.py
│   │   │   ├── attendance.py
│   │   │   ├── grades.py
│   │   │   ├── courses.py
│   │   │   ├── assignments.py
│   │   │   ├── quizzes.py
│   │   │   ├── fees.py
│   │   │   ├── schedules.py
│   │   │   ├── announcements.py
│   │   │   ├── ai.py
│   │   │   └── admin.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── student_service.py
│   │   │   ├── attendance_service.py
│   │   │   ├── gradebook_service.py
│   │   │   ├── scheduling_service.py
│   │   │   ├── lms_service.py
│   │   │   ├── ai_service.py
│   │   │   └── notification_service.py
│   │   ├── core/                # Security, config
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── deps.py
│   │   │   └── config.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── conftest.py
│   │       ├── test_auth.py
│   │       ├── test_students.py
│   │       ├── test_attendance.py
│   │       └── test_grades.py
│   ├── web/                      # Next.js Frontend
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   ├── globals.css
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── login/page.tsx
│   │   │   │   │   └── register/page.tsx
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── layout.tsx
│   │   │   │   │   ├── admin/
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── students/page.tsx
│   │   │   │   │   ├── teachers/page.tsx
│   │   │   │   │   ├── attendance/page.tsx
│   │   │   │   │   ├── grades/page.tsx
│   │   │   │   │   ├── schedule/page.tsx
│   │   │   │   │   ├── fees/page.tsx
│   │   │   │   │   └── settings/page.tsx
│   │   │   │   │   ├── teacher/
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   ├── attendance/page.tsx
│   │   │   │   │   │   ├── gradebook/page.tsx
│   │   │   │   │   │   ├── courses/page.tsx
│   │   │   │   │   │   └── messages/page.tsx
│   │   │   │   │   ├── student/
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── courses/page.tsx
│   │   │   │   │   │   ├── attendance/page.tsx
│   │   │   │   │   │   ├── grades/page.tsx
│   │   │   │   │   │   ├── assignments/page.tsx
│   │   │   │   │   │   └── schedule/page.tsx
│   │   │   │   │   └── parent/
│   │   │   │   │       ├── page.tsx
│   │   │   │   │       ├── child/page.tsx
│   │   │   │   │       ├── attendance/page.tsx
│   │   │   │   │       ├── grades/page.tsx
│   │   │   │   │       └── fees/page.tsx
│   │   │   │   └── api/         # Next.js API routes (proxy)
│   │   │   ├── components/
│   │   │   │   ├── ui/         # Shadcn/ui components
│   │   │   │   ├── layout/
│   │   │   │   │   ├── Sidebar.tsx
│   │   │   │   │   ├── Header.tsx
│   │   │   │   │   └── Navbar.tsx
│   │   │   │   ├── forms/
│   │   │   │   ├── tables/
│   │   │   │   └── charts/
│   │   │   ├── lib/
│   │   │   │   ├── api.ts
│   │   │   │   ├── auth.ts
│   │   │   │   ├── utils.ts
│   │   │   │   └── constants.ts
│   │   │   ├── hooks/
│   │   │   │   ├── useAuth.ts
│   │   │   │   └── useApi.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── stores/
│   │   │       └── authStore.ts
│   │   └── public/
│   │       └── ...static files
│   └── mobile/                  # React Native Expo App
│       ├── package.json
│       ├── app.json
│       ├── tsconfig.json
│       ├── src/
│       │   ├── app/
│       │   │   ├── _layout.tsx
│       │   │   ├── index.tsx
│       │   │   ├── login.tsx
│       │   │   ├── (tabs)/
│       │   │   │   ├── _layout.tsx
│       │   │   │   ├── home.tsx
│       │   │   │   ├── courses.tsx
│       │   │   │   ├── attendance.tsx
│       │   │   │   ├── grades.tsx
│       │   │   │   ├── assignments.tsx
│       │   │   │   └── messages.tsx
│       │   │   └── (stack)/
│       │   │       ├── course-detail.tsx
│       │   │       ├── lesson.tsx
│       │   │       ├── quiz.tsx
│       │   │       └── ...
│       │   ├── components/
│       │   ├── services/
│       │   ├── stores/
│       │   ├── types/
│       │   └── utils/
├── infrastructure/
│   ├── nginx/
│   │   └── nginx.conf
│   ├── minio/
│   │   └── ...
│   └── backups/
│       └── ...
├── scripts/
│   ├── init_db.sh
│   ├── seed.sh
│   ├── backup.sh
│   └── restore.sh
└── tests/
    ├── e2e/
    │   └── ...
    └── load/
        └── ...
```

---

## 6. API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Get current user |

### Students
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/students` | List students |
| POST | `/api/v1/students` | Create student |
| GET | `/api/v1/students/{id}` | Get student |
| PUT | `/api/v1/students/{id}` | Update student |
| DELETE | `/api/v1/students/{id}` | Delete student |
| GET | `/api/v1/students/{id}/enrollments` | Get enrollments |
| GET | `/api/v1/students/{id}/attendance` | Get attendance |
| GET | `/api/v1/students/{id}/grades` | Get grades |
| POST | `/api/v1/students/bulk-import` | Bulk import |
| GET | `/api/v1/students/search` | Search students |

### Attendance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/attendance` | List attendance |
| POST | `/api/v1/attendance` | Mark attendance |
| GET | `/api/v1/attendance/class/{class_id}` | Class attendance |
| GET | `/api/v1/attendance/student/{student_id}` | Student attendance |
| POST | `/api/v1/attendance/bulk` | Bulk mark |
| POST | `/api/v1/attendance/excuse` | Request excuse |
| PUT | `/api/v1/attendance/excuse/{id}` | Approve/reject excuse |

### Grades
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/grades/systems` | List grading systems |
| POST | `/api/v1/grades/systems` | Create system |
| GET | `/api/v1/grades/exams` | List exams |
| POST | `/api/v1/grades/exams` | Create exam |
| POST | `/api/v1/grades/exams/{id}/results` | Submit results |
| GET | `/api/v1/grades/student/{student_id}` | Student grades |
| GET | `/api/v1/grades/report/{student_id}` | Generate report |
| POST | `/api/v1/grades/bulk-import` | Bulk import marks |

### Courses (LMS)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/courses` | List courses |
| POST | `/api/v1/courses` | Create course |
| GET | `/api/v1/courses/{id}` | Get course |
| PUT | `/api/v1/courses/{id}` | Update course |
| DELETE | `/api/v1/courses/{id}` | Delete course |
| POST | `/api/v1/courses/{id}/enroll` | Enroll student |
| GET | `/api/v1/courses/{id}/content` | Get content |
| POST | `/api/v1/courses/{id}/chapter` | Add chapter |

### Assignments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/assignments` | List assignments |
| POST | `/api/v1/assignments` | Create assignment |
| GET | `/api/v1/assignments/{id}` | Get assignment |
| PUT | `/api/v1/assignments/{id}` | Update |
| POST | `/api/v1/assignments/{id}/submit` | Submit |
| GET | `/api/v1/assignments/{id}/submissions` | List submissions |
| PUT | `/api/v1/submissions/{id}/grade` | Grade submission |

### Quizzes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/quizzes` | List quizzes |
| POST | `/api/v1/quizzes` | Create quiz |
| GET | `/api/v1/quizzes/{id}` | Get quiz with questions |
| POST | `/api/v1/quizzes/{id}/attempt` | Start attempt |
| PUT | `/api/v1/quizzes/attempts/{id}` | Submit attempt |
| GET | `/api/v1/quizzes/attempts/{id}/result` | Get result |

### Schedules
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/schedules` | List schedules |
| POST | `/api/v1/schedules` | Create schedule |
| GET | `/api/v1/schedules/class/{class_id}` | Class schedule |
| GET | `/api/v1/schedules/teacher/{teacher_id}` | Teacher schedule |
| POST | `/api/v1/schedules/generate` | Auto-generate |

### Fees
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/fees/structures` | List fee structures |
| POST | `/api/v1/fees/structures` | Create structure |
| GET | `/api/v1/fees/student/{student_id}` | Student fees |
| POST | `/api/v1/fees/pay` | Record payment |
| GET | `/api/v1/fees/reports/outstanding` | Outstanding report |
| GET | `/api/v1/fees/reports/collection` | Collection report |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/chat` | Chat with AI tutor |
| GET | `/api/v1/ai/analytics/{student_id}` | Student analytics |
| GET | `/api/v1/ai/predictions/at-risk` | At-risk students |
| POST | `/api/v1/ai/reports/progress` | Generate progress report |

---

## 7. Acceptance Criteria

### Phase 1: Core Foundation
- [ ] PostgreSQL database with all tables created
- [ ] FastAPI backend running with all core endpoints
- [ ] Authentication (JWT) working
- [ ] Multi-tenant isolation working

### Phase 2: SIS Core
- [ ] Student CRUD operations
- [ ] Teacher CRUD operations
- [ ] Attendance system (mark, view, report)
- [ ] Gradebook with configurable grading systems
- [ ] Exam management and results
- [ ] Basic scheduling

### Phase 3: LMS
- [ ] Course creation and enrollment
- [ ] Chapter/lesson content management
- [ ] Assignment creation and submission
- [ ] Quiz with auto-grading
- [ ] Progress tracking

### Phase 4: Advanced SIS
- [ ] Fee management with payments
- [ ] Report card generation
- [ ] Parent portal
- [ ] Bulk operations (import/export)
- [ ] Notifications system

### Phase 5: AI & Mobile
- [ ] AI tutor integration
- [ ] Student analytics
- [ ] React Native mobile app
- [ ] Push notifications

### Phase 6: Production
- [ ] Docker deployment
- [ ] CI/CD pipeline
- [ ] Performance optimization
- [ ] Security audit

---

## 8. Non-Functional Requirements

### Performance
- API response time < 200ms (p95)
- Database queries optimized with proper indexes
- Redis caching for hot paths
- Lazy loading for large datasets

### Security
- JWT with short expiry + refresh tokens
- Password hashing (bcrypt/argon2)
- Role-based access control (RBAC)
- SQL injection prevention (ORM)
- XSS prevention
- CORS configuration
- Rate limiting
- Audit logging

### Scalability
- Horizontal scaling ready
- Stateless API
- Database connection pooling
- Redis for sessions

### Accessibility
- WCAG 2.1 AA compliance (web)
- Keyboard navigation
- Screen reader support
- High contrast mode

---

*End of SPEC.md*
