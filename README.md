# 🎓 All-in-One SIS

### Modern Student Information System with LMS, Attendance, Gradebook, and AI

<!-- Badges Row -->
<div align="center">

![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-cyan.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Redis](https://img.shields.io/badge/Redis-7+-red.svg)

</div>

---

## ✨ Features

### Core System
- ✅ **Student Information Management** — Comprehensive student profiles, admission tracking, document management
- ✅ **Teacher & Staff Management** — Employee profiles, department assignment, performance records
- ✅ **Attendance Tracking** — Daily and period-wise attendance with excuse workflow
- ✅ **Gradebook & Exam Management** — Configurable grading systems, exams, report cards
- ✅ **Course & Content Management (LMS)** — Chapters, lessons, multimedia content
- ✅ **Assignment & Quiz System** — Online submission, auto-grading, feedback
- ✅ **Fee Management** — Fee structures, payments, discounts, receipts
- ✅ **Scheduling & Timetables** — Class schedules, period management, conflict detection

### Architecture
- ✅ **Multi-tenant Architecture** — Isolated data per school/tenant
- ✅ **Role-based Access Control** — Admin, Teacher, Student, Parent roles

### Future Roadmap
- 🚧 **AI Tutor Integration** — 24/7 AI-powered learning assistant
- 🚧 **Mobile-First Design** — React Native app for iOS & Android
- 🚧 **Smart Analytics** — At-risk student prediction, engagement scoring

---

## 🛠️ Tech Stack

<table>
<tr>
<td align="center" width="100"><strong>Backend</strong></td>
<td align="center" width="100"><strong>Frontend</strong></td>
<td align="center" width="100"><strong>Database</strong></td>
<td align="center" width="100"><strong>Cache</strong></td>
<td align="center" width="100"><strong>Mobile</strong></td>
<td align="center" width="100"><strong>AI</strong></td>
</tr>
<tr>
<td align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
<br>**Python/FastAPI**

</td>
<td align="center">

![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=next.js&logoColor=white)
<br>**React, TypeScript**

</td>
<td align="center">

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white)
<br>**PostgreSQL**

</td>
<td align="center">

![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)
<br>**Redis**

</td>
<td align="center">

![React Native](https://img.shields.io/badge/React_Native-20232A?style=flat-square&logo=react&logoColor=61DAFB)
<br>**React Native**

</td>
<td align="center">

![LangChain](https://img.shields.io/badge/LangChain-★★★-FFFFFF?style=flat-square)
<br>**LangChain + OpenAI**

</td>
</tr>
</table>

| Component | Technology |
|-----------|------------|
| **API Framework** | FastAPI (Async, Type Safety, OpenAPI) |
| **Web Framework** | Next.js 14 (App Router, Server Components) |
| **ORM** | SQLAlchemy 2.0 (Async) |
| **Validation** | Pydantic v2 |
| **Auth** | JWT with refresh tokens |
| **File Storage** | S3-compatible (MinIO) |
| **Search** | PostgreSQL full-text + pgvector |
| **Real-time** | WebSocket (Socket.io) |
| **Containerization** | Docker + Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### 1. Clone the Repository

```bash
git clone <repo-url>
cd all-in-one-sis
```

### 2. Start Infrastructure (Database & Cache)

```bash
docker-compose up -d db redis
```

### 3. Install and Setup Backend

```bash
cd apps/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed demo data
python seed.py

# Start development server
uvicorn main:app --reload
```

### 4. Install and Setup Frontend (New Terminal)

```bash
cd apps/web

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Access the Application

| Service | URL |
|---------|-----|
| **Web App** | http://localhost:3000 |
| **API Server** | http://localhost:8000 |
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |

---

## 🔐 Login Credentials

| Role | Email | Password |
|------|-------|----------|
| 🔴 **Admin** | admin@demo.edu | admin123 |
| 🔵 **Teacher** | john@demo.edu | teacher123 |
| 🟢 **Student** | student1@demo.edu | student123 |

---

## 📚 API Documentation

Interactive API documentation is available at:

- **Swagger UI** — [http://localhost:8000/docs](http://localhost:8000/docs)
  - Try out endpoints directly in your browser
  - Authentication support built-in

- **ReDoc** — [http://localhost:8000/redoc](http://localhost:8000/redoc)
  - Beautiful documentation layout
  - Offline-friendly

---

## 📁 Project Structure

```
all-in-one-sis/
├── apps/
│   ├── api/                          # FastAPI Backend
│   │   ├── main.py                   # Application entry point
│   │   ├── config.py                 # Configuration management
│   │   ├── database.py               # Database connection
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── tenant.py             # Multi-tenant models
│   │   │   ├── person.py             # Person/User models
│   │   │   ├── student.py             # Student model
│   │   │   ├── teacher.py             # Teacher model
│   │   │   ├── attendance.py          # Attendance records
│   │   │   ├── gradebook.py           # Grades & exams
│   │   │   ├── scheduling.py          # Timetables
│   │   │   ├── fees.py                # Fee management
│   │   │   └── lms.py                 # LMS models
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── api/                       # API route handlers
│   │   │   ├── auth.py                # Authentication endpoints
│   │   │   ├── students.py            # Student management
│   │   │   ├── teachers.py            # Teacher management
│   │   │   ├── attendance.py          # Attendance endpoints
│   │   │   ├── grades.py              # Gradebook endpoints
│   │   │   ├── courses.py             # LMS courses
│   │   │   ├── assignments.py         # Assignment endpoints
│   │   │   ├── quizzes.py             # Quiz endpoints
│   │   │   ├── fees.py                # Fee endpoints
│   │   │   └── schedules.py           # Schedule endpoints
│   │   ├── services/                  # Business logic layer
│   │   └── core/                      # Security & configuration
│   │
│   ├── web/                           # Next.js Frontend
│   │   ├── src/
│   │   │   ├── app/                   # Next.js App Router
│   │   │   │   ├── (auth)/            # Auth pages (login, register)
│   │   │   │   └── (dashboard)/       # Dashboard pages
│   │   │   │       ├── admin/         # Admin portal
│   │   │   │       ├── teacher/        # Teacher portal
│   │   │   │       ├── student/        # Student portal
│   │   │   │       └── parent/         # Parent portal
│   │   │   ├── components/            # React components
│   │   │   │   ├── ui/                # Shadcn/ui components
│   │   │   │   ├── layout/            # Layout components
│   │   │   │   └── forms/             # Form components
│   │   │   └── lib/                   # Utilities & API client
│   │   └── public/                    # Static assets
│   │
│   └── mobile/                        # React Native Mobile App
│       └── src/
│           ├── app/                   # App screens
│           ├── components/            # Mobile components
│           └── services/              # API services
│
├── infrastructure/
│   ├── nginx/                         # Nginx configuration
│   └── backups/                       # Database backups
│
├── scripts/                           # Utility scripts
│   ├── init_db.sh                     # Database initialization
│   ├── seed.sh                        # Data seeding
│   └── backup.sh                      # Backup script
│
├── docker-compose.yml                 # Development Docker setup
├── docker-compose.prod.yml            # Production Docker setup
├── docker-compose.yml
├── Dockerfile                          # API Docker image
├── Dockerfile.web                      # Web Docker image
├── Makefile                            # Development commands
├── SPEC.md                             # Detailed specification
└── README.md                           # This file
```

---

## 🌐 API Endpoints Overview

| Module | Description | Key Endpoints |
|--------|-------------|---------------|
| **Auth** | Authentication & authorization | `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/me` |
| **Students** | Student management | CRUD, search, bulk-import, enrollments, attendance, grades |
| **Teachers** | Teacher management | CRUD, search, assignments, department |
| **Attendance** | Attendance tracking | Mark, bulk-mark, excuses, class/student attendance |
| **Grades** | Gradebook & exams | Grading systems, exams, results, report cards |
| **Courses** | LMS course management | CRUD, enrollment, chapters, lessons |
| **Assignments** | Assignment system | Create, submit, grade, submissions list |
| **Quizzes** | Quiz & assessment | Create, attempt, auto-grading, results |
| **Fees** | Fee management | Structures, payments, reports |
| **Schedules** | Timetable management | Create, class/teacher schedules, auto-generate |
| **AI** | AI tutor & analytics | Chat, predictions, progress reports |

### Full API Documentation

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for complete endpoint documentation with interactive testing.

---

## ⚙️ Environment Variables

Create a `.env` file in `apps/api/` with the following variables:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sis

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# S3/MinIO (Optional)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET= sis-uploads

# AI (Future)
OPENAI_API_KEY=your-openai-api-key
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the Repository** — Create your own fork of the project

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes** — Follow the existing code style and conventions

4. **Write Tests** — Ensure new features have adequate test coverage

5. **Commit Your Changes** — Use conventional commit format
   ```bash
   git commit -m "feat(module): add new feature"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** — Describe your changes and submit for review

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript best practices for React code
- Write meaningful commit messages
- Update documentation for any new features
- Ensure tests pass before submitting PR

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

For full license text, see [LICENSE](LICENSE) or visit [GNU AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.en.html).

---

<div align="center">

**Built with ❤️ for modern education**

*© 2026 All-in-One SIS — Modern Student Information System*

</div>
