# workshop_1

## Docker Compose

Для запуска через Docker Compose нужен заполненный `.env` файл. Проще всего начать с копии `.env.example`.

```bash
cp .env.example .env
docker compose up --build
```

Что происходит при старте `backend`:

1. контейнер ждёт готовности PostgreSQL;
2. выполняется `python scripts/reindex_kb.py`;
3. после успешной реиндексации запускается приложение командой `python -m app.main`.

Сервис базы данных использует образ `pgvector/pgvector:pg16`, а данные Postgres сохраняются в volume `postgres_data`.
