#!/bin/bash
set -e

BACKUP_DIR=${BACKUP_DIR:-./backups}
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sis_backup_$DATE.sql"

echo "Creating backup: $BACKUP_FILE"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
PGPASSWORD=$DB_PASSWORD pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "Backup created: $BACKUP_FILE"

# Keep only last 7 backups
cd "$BACKUP_DIR"
ls -t *.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm

echo "Backup complete!"
