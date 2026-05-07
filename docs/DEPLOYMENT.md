# Deployment Guide

## Prerequisites

- Docker & Docker Compose
- PostgreSQL 15
- Redis 7
- Node.js 20 (for local development)

## Production Deployment

### 1. Clone and Configure

```bash
git clone <repo-url>
cd all-in-one-sis
cp .env.example .env
# Edit .env with production values
```

### 2. Build and Start

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Initialize Database

```bash
docker-compose exec api alembic upgrade head
docker-compose exec api python -m apps.api.seed
```

### 4. Verify

- API: http://localhost:8000/docs
- Web: http://localhost:3000
- MinIO Console: http://localhost:9001

## Environment Variables

See `.env.example` for all required variables.

## Scaling

- API: `docker-compose up -d --scale api=3`
- Use nginx for load balancing
- PostgreSQL with read replicas for scaling