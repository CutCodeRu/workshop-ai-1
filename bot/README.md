# Bot First Stage

## Что нужно перед запуском

- Python 3.12+
- PostgreSQL 14+
- созданная база данных PostgreSQL
- Telegram bot token от BotFather
- `OWNER_CHAT_ID` владельца, куда будут приходить уведомления о заявках

## Подготовка окружения

Из корня проекта:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

После этого заполните `.env` минимум такими переменными:

```env
APP_ENV=dev
LOG_LEVEL=INFO
TELEGRAM_BOT_TOKEN=your_bot_token
OWNER_CHAT_ID=123456789
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/secretary_bot
SYSTEM_PROMPT_PATH=system_prompt.txt
```

Примечания:

- `OWNER_CHAT_ID` используется для уведомлений о новых заявках. Если оставить пустым, бот запустится, но отправка уведомлений владельцу будет отключена.
- `SYSTEM_PROMPT_PATH` по умолчанию указывает на `system_prompt.txt`.
- Если в проекте лежит файл `system-prompt.txt`, приложение тоже сможет его прочитать как fallback.

## Как запустить миграции

На первом этапе отдельного мигратора нет. Минимальная схема создаётся функцией `init_db()` из `app/db/database.py`.

Чтобы создать таблицы `applications` и `knowledge_chunks`, выполните из корня проекта:

```bash
python3 -c "import asyncio; from app.db import init_db; asyncio.run(init_db())"
```

Если подключение к PostgreSQL настроено корректно, команда завершится без вывода и создаст нужные таблицы.

## Как запустить бота в polling режиме

Из корня проекта:

```bash
python3 scripts/run_bot.py
```

Что делает запуск:

- загружает настройки из `.env`
- читает системный промпт из файла
- вызывает `init_db()`
- регистрирует команды и роутеры `aiogram 3`
- запускает long polling

## Быстрая проверка

Если бот успешно стартовал, в консоли не будет traceback, а в Telegram:

- команда `/start` покажет две кнопки:
  - `Задать вопрос`
  - `Записаться на консультацию`
- обычный текст вернёт заглушку: `Принял ваш вопрос, скоро отвечу`
- сценарий записи соберёт имя, телефон и вопрос, затем сохранит заявку в БД и отправит уведомление владельцу
