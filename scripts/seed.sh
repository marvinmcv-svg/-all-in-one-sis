#!/bin/bash
set -e

echo "Seeding database..."

cd /app

# Seed data
python -m apps.api.seed

echo "Database seeded successfully!"
