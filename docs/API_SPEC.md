# API Specification

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except `/auth/*`) require JWT Bearer token:
```
Authorization: Bearer <token>
```

## Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/register` | Register new user |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user |

### Students
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/students` | List all students |
| POST | `/students` | Create student |
| GET | `/students/{id}` | Get student |
| PUT | `/students/{id}` | Update student |
| DELETE | `/students/{id}` | Delete student |
| GET | `/students/search?q=` | Search students |

### Attendance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/attendance` | List attendance |
| POST | `/attendance` | Mark attendance |
| POST | `/attendance/bulk` | Bulk mark attendance |
| GET | `/attendance/student/{id}` | Student attendance |

### Grades
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/grades/systems` | List grading systems |
| POST | `/grades/exams` | Create exam |
| POST | `/grades/exams/{id}/results` | Submit results |
| GET | `/grades/student/{id}` | Student grades |

### Courses (LMS)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses` | List courses |
| POST | `/courses` | Create course |
| POST | `/courses/{id}/enroll` | Enroll student |
| GET | `/courses/{id}/content` | Get content |

## Response Format

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## Error Format

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```