FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=voting_entrance.settings

WORKDIR /app

# mysqlclient build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Windows checkouts often use CRLF; strip CR so the script runs in Linux containers.
RUN sed -i 's/\r$//' docker/entrypoint.sh && chmod +x docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "docker/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "voting_entrance.asgi:application"]
