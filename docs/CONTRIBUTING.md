# Contributing to All-in-One SIS

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`
5. Start PostgreSQL and Redis
6. Run migrations: `alembic upgrade head`
7. Start dev server: `uvicorn apps.api.main:app --reload`

## Code Style

- Python: Follow PEP 8, use Black formatter
- TypeScript: Use ESLint + Prettier
- Write type hints for all Python functions
- Use async/await for all database operations

## Testing

```bash
# Run Python tests
pytest apps/api/tests/

# Run frontend tests
npm test --prefix apps/web

# E2E tests
playwright test
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit using conventional commits
3. Push and create PR
4. Ensure CI passes
5. Request review

## Commit Format

```
type(scope): subject

feat(auth): add password reset
fix(attendance): resolve bulk mark bug
docs(api): update endpoint docs
```

Types: feat, fix, docs, style, refactor, test, chore