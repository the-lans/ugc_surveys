#!/bin/sh
set -e

# Ждём готовности PostgreSQL
echo "Waiting for database..."
while ! nc -z "${DB_HOST:-db}" "${DB_PORT:-5432}"; do
    sleep 1
done
echo "Database is ready."

python manage.py migrate --no-input
python manage.py collectstatic --no-input

exec "$@"
