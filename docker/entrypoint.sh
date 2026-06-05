#!/bin/sh
set -e

echo "Waiting for database at ${DB_HOST:-db}:${DB_PORT:-3306}..."
until python -c "
import socket
import os
host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', '3306'))
s = socket.create_connection((host, port), timeout=2)
s.close()
" 2>/dev/null; do
  sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application..."
exec "$@"
