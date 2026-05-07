#!/bin/bash
set -e

echo "Initializing database..."

# Wait for PostgreSQL
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Run migrations
echo "Running Alembic migrations..."
cd /app
alembic upgrade head

echo "Database initialized successfully!"
