#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "Restoring database from: $BACKUP_FILE"

# Stop application
echo "Stopping application..."
docker-compose stop api || true

# Restore PostgreSQL
if [[ "$BACKUP_FILE" == *.gz ]]; then
  gunzip -c "$BACKUP_FILE" | PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"
else
  PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"
fi

echo "Database restored successfully!"

# Restart application
docker-compose start api

echo "Application restarted!"
