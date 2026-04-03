# VibeMatching

## Project Structure

```text
app/
	api/
	core/
	models/
	repositories/
	schemas/
	services/
alembic/
	versions/
docker-compose.yml
```

## Environment Setup

1. Copy environment template:

```bash
cp .env.example .env
```

2. Install dependencies:

```bash
poetry install
```

## Run Infrastructure

Start services:

```bash
docker compose up -d
```

Start infra + backend API together:

```bash
docker compose up -d --build
```

Start backend + bot together:

```bash
docker compose up -d --build backend bot
```

Published host ports:
- `backend`: `8000`
- `postgres`: `5433` (mapped to container `5432`)
- `redis`: `6379`
- `rabbitmq`: `5672` (AMQP), `15672` (UI)
- `minio`: `9000` (S3 API), `9001` (console)

Telegram bot service uses long polling and does not publish host ports.
Set `TELEGRAM_BOT_TOKEN` in `.env` before starting `bot`.

Run bot smoke test (happy path against backend API):

```bash
poetry run python -m bot.smoke_test
```

Stop services:

```bash
docker compose down
```

Stop and remove volumes (full reset):

```bash
docker compose down -v
```

## Apply Migrations

```bash
poetry run alembic upgrade head
```

## Run Backend

```bash
poetry run uvicorn app.main:app --reload
```

If backend runs in Docker Compose, API is available on:

```text
http://localhost:8000
```

Healthcheck endpoint:

```text
GET http://localhost:8000/health
```