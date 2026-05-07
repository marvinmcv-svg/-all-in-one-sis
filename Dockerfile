# Multi-stage build for All-in-One SIS
# Stage 1: Build API
FROM python:3.11-slim as api-builder
WORKDIR /app
COPY apps/api/requirements.txt apps/api/
RUN pip install --no-cache-dir -r apps/api/requirements.txt
COPY apps/api/ apps/api/
RUN cd apps/api && alembic generate-revision --autogenerate -m "init" || true

# Stage 2: Build Web
FROM node:20-alpine as web-builder
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json* apps/web/
RUN npm ci
COPY apps/web/ apps/web/
RUN npm run build

# Stage 3: Final runtime images
FROM python:3.11-slim as api
WORKDIR /app
COPY --from=api-builder /app/apps/api /app/apps/api
COPY --from=api-builder /app/apps /app/apps
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM nginx:alpine as web
WORKDIR /usr/share/nginx/html
COPY --from=web-builder /app/apps/web/.next/static ./.next/static
COPY --from=web-builder /app/apps/web/public ./public
COPY --from=web-builder /app/apps/web/.next/standalone ./
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
