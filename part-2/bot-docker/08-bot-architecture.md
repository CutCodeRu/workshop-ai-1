# Архитектура Telegram-бота секретаря с RAG

Актуально на **1 марта 2026**.

Документ фиксирует архитектурные решения для дальнейшей разработки Telegram-бота секретаря на основе стека из `07-stack-research.md`.

---

## 1. Цель системы

Бот должен решать четыре задачи:

- отвечать на вопросы клиентов по базе знаний компании;
- отсеивать вопросы вне тематики компании, чтобы не тратить лишние вызовы API;
- собирать заявки на консультацию в формате `имя -> телефон -> вопрос`;
- уведомлять владельца о новых заявках в Telegram.

---

## 2. Зафиксированный выбор архитектуры

### Стек

- **Язык:** `Python 3.12+`
- **Telegram framework:** `aiogram 3`
- **Режим приема сообщений:** `long polling`
- **Основная БД:** `PostgreSQL`
- **Поиск по базе знаний:** `pgvector + PostgreSQL FTS`
- **LLM:** `OpenAI GPT-5 mini`
- **Embeddings:** `text-embedding-3-small`
- **RAG orchestration:** собственный `2-step RAG`
- **Сбор заявок:** FSM в `aiogram`
- **Локальный запуск:** `Docker Compose`

### Почему выбран именно такой стек

#### 1. Python + aiogram 3

Это практичный выбор для MVP, потому что:

- `aiogram 3` хорошо подходит для асинхронного Telegram-бота;
- в нем удобно строить FSM для заявок;
- Python удобно использовать одновременно для Telegram-логики, ingestion базы знаний и RAG.

#### 2. Long polling

На первом этапе не нужен отдельный публичный сервер и webhook-инфраструктура.  
Long polling позволяет запустить бота локально или в Docker на постоянно включенной машине.

#### 3. PostgreSQL + pgvector + FTS

Это минимизирует инфраструктуру:

- в одной БД лежат знания;
- там же хранятся заявки;
- там же можно хранить историю диалогов и логи.

Также такой вариант поддерживает **hybrid retrieval**:

- semantic search по embeddings;
- keyword/full-text search по `tsvector`.

#### 4. Собственный 2-step RAG

Для первого релиза не нужен тяжелый orchestration framework.  
Свой пайплайн проще:

- тестировать;
- отлаживать;
- ограничивать;
- объяснять команде и бизнесу.

#### 5. OpenAI GPT-5 mini + text-embedding-3-small

Этот выбор закрывает два требования:

- достаточно качественные ответы для customer-facing бота;
- низкая стоимость индексации и запросов.

`text-embedding-3-small` использует размерность `1536`, поэтому в Postgres поле embedding хранится как `vector(1536)`.  
Это удобно и дешево для малого проекта: embedding-индексация KB обходится недорого, а для FAQ и корпоративной базы знаний качества обычно достаточно.

---

## 3. Главные архитектурные принципы

### 1. Один файл — одна ответственность

Каждый файл выполняет одну узкую задачу:

- handler только принимает Telegram update;
- use case только реализует бизнес-сценарий;
- repository только работает с одной таблицей;
- provider только вызывает внешний API.

Это уменьшает связанность и упрощает развитие проекта.

### 2. Разделение online и offline логики

Система делится на два контура:

- **online-контур** отвечает пользователю в реальном времени;
- **offline-контур** читает текстовую базу знаний, режет ее на чанки, строит embeddings и обновляет индекс.

Такое разделение нужно потому, что ответы пользователю должны быть быстрыми, а индексирование может выполняться отдельно после изменений в KB-файле.

### 3. Детерминированный lead flow отдельно от LLM

Сбор заявки не должен зависеть от свободной генерации модели.  
Имя, телефон и вопрос собираются строго через FSM, а не через prompt.

### 4. Отвечаем только по найденному контексту

LLM получает только найденные фрагменты KB.  
Если контекст слабый или вопрос вне тематики компании, бот не фантазирует, а:

- честно сообщает, что не может уверенно ответить;
- предлагает оставить заявку на консультацию.

### 5. Экономим API до вызова модели

Перед вызовом `GPT-5 mini` бот сначала:

- проверяет, относится ли вопрос к тематике компании;
- выполняет retrieval;
- оценивает силу найденного контекста.

Если уверенности нет, модель не вызывается.

---

## 4. Структура проекта

```text
workshop_1/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── logging.py
│   ├── bootstrap.py
│   ├── schemas/
│   │   ├── lead.py
│   │   ├── document.py
│   │   └── retrieval.py
│   ├── bot/
│   │   ├── bot_factory.py
│   │   ├── dispatcher_factory.py
│   │   ├── handlers/
│   │   │   ├── start.py
│   │   │   ├── question.py
│   │   │   ├── lead.py
│   │   │   └── cancel.py
│   │   ├── states/
│   │   │   └── lead_form.py
│   │   ├── keyboards/
│   │   │   ├── main_menu.py
│   │   │   └── lead_actions.py
│   │   └── texts/
│   │       ├── out_of_scope.py
│   │       ├── low_confidence.py
│   │       └── owner_notification.py
│   ├── use_cases/
│   │   ├── answer_company_question.py
│   │   ├── create_lead.py
│   │   ├── notify_owner.py
│   │   └── reindex_knowledge_base.py
│   ├── rag/
│   │   ├── scope_guard.py
│   │   ├── hybrid_retriever.py
│   │   ├── context_builder.py
│   │   ├── prompt_builder.py
│   │   ├── answer_generator.py
│   │   └── confidence_checker.py
│   ├── knowledge/
│   │   ├── source_reader.py
│   │   ├── section_parser.py
│   │   ├── metadata_extractor.py
│   │   ├── chunker.py
│   │   └── embedder.py
│   ├── providers/
│   │   ├── openai_chat.py
│   │   └── openai_embeddings.py
│   └── db/
│       ├── connection.py
│       └── repositories/
│           ├── documents.py
│           ├── document_chunks.py
│           ├── leads.py
│           ├── admins.py
│           └── message_logs.py
├── migrations/
├── data/
│   └── knowledge/
│       ├── company_kb.md
│       └── kb_template.md
├── scripts/
│   └── reindex_kb.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

### Назначение крупных модулей

- `app/bot` отвечает только за Telegram transport.
- `app/use_cases` отвечает только за бизнес-сценарии.
- `app/rag` отвечает только за online RAG pipeline.
- `app/knowledge` отвечает только за offline ingestion базы знаний.
- `app/providers` отвечает только за внешние API.
- `app/db` отвечает только за хранение и выборку данных.
- `app/schemas` отвечает только за структуры данных между слоями.
- `migrations` отвечают только за схему БД.
- `data/knowledge` содержит только бизнес-контент, который можно редактировать без программиста.

---

## 5. Переменные окружения

### Обязательные переменные

| Переменная | Зачем нужна |
|---|---|
| `APP_ENV` | Переключает режимы `dev` / `prod`. |
| `LOG_LEVEL` | Управляет подробностью логов. |
| `BOT_TOKEN` | Токен Telegram-бота. |
| `OWNER_TELEGRAM_ID` | Telegram ID владельца или главного администратора. |
| `LEAD_NOTIFICATION_CHAT_ID` | Чат или группа, куда отправлять уведомления о заявках. |
| `POSTGRES_HOST` | Хост PostgreSQL. |
| `POSTGRES_PORT` | Порт PostgreSQL. |
| `POSTGRES_DB` | Имя базы данных. |
| `POSTGRES_USER` | Пользователь БД. |
| `POSTGRES_PASSWORD` | Пароль БД. |
| `OPENAI_API_KEY` | Ключ OpenAI для chat и embeddings. |
| `OPENAI_CHAT_MODEL` | Имя chat-модели, по умолчанию `gpt-5-mini`. |
| `OPENAI_EMBEDDING_MODEL` | Имя embedding-модели, по умолчанию `text-embedding-3-small`. |
| `KNOWLEDGE_FILE_PATH` | Путь к текстовому файлу базы знаний. |
| `RAG_TOP_K` | Сколько чанков брать в контекст. |
| `RAG_MIN_HYBRID_SCORE` | Порог retrieval, ниже которого не идем в LLM. |
| `RAG_MIN_CONFIDENCE` | Порог уверенности ответа перед отправкой пользователю. |

---

## 6. Схема базы данных

Ниже описан рекомендуемый набор таблиц для MVP и ближайшего развития.

### 6.1. Таблица `knowledge_documents`

**Назначение:** хранит логические документы или секции базы знаний и их метаданные.

#### Поля

| Поле | Тип | Объяснение выбора |
|---|---|---|
| `id` | `bigserial primary key` | Простой внутренний идентификатор документа. |
| `source_key` | `text not null unique` | Стабильный ключ секции, например `company_kb.md#delivery`. |
| `title` | `text not null` | Заголовок секции KB. |
| `source_path` | `text not null` | Путь к исходному файлу, нужен для дебага и переиндексации. |
| `source_type` | `text not null default 'kb_markdown'` | Позволяет позже добавлять другие типы источников. |
| `category` | `text null` | Категория знаний. |
| `service` | `text null` | Услуга или продукт. |
| `branch` | `text null` | Филиал, если бизнес распределенный. |
| `version` | `integer not null default 1` | Версия документа при переиндексации. |
| `checksum` | `char(64) not null` | Хэш исходного текста для отслеживания изменений. |
| `metadata` | `jsonb not null default '{}'::jsonb` | Гибкое поле для дополнительных тегов. |
| `is_active` | `boolean not null default true` | Позволяет выключать документ из поиска без удаления. |
| `created_at` | `timestamptz not null default now()` | Время создания. |
| `updated_at` | `timestamptz not null default now()` | Время последнего обновления. |

#### Индексы

- `unique index (source_key)` — чтобы не дублировать один и тот же логический документ.
- `index (is_active)` — чтобы быстро выбирать только активные документы.
- `index (category, service, branch)` — для фильтрации retrieval по метаданным.

#### Связи

- `knowledge_documents.id -> knowledge_chunks.document_id` как связь `1:N`.

---

### 6.2. Таблица `knowledge_chunks`

**Назначение:** хранит чанки базы знаний для hybrid retrieval.

#### Поля

| Поле | Тип | Объяснение выбора |
|---|---|---|
| `id` | `bigserial primary key` | Внутренний идентификатор чанка. |
| `document_id` | `bigint not null references knowledge_documents(id) on delete cascade` | Чанк относится к документу; при удалении документа удаляются его чанки. |
| `chunk_no` | `integer not null` | Порядковый номер чанка внутри документа. |
| `heading` | `text null` | Заголовок секции или подзаголовок. |
| `content` | `text not null` | Исходный текст чанка. |
| `content_tsv` | `tsvector not null` | Представление для PostgreSQL FTS. |
| `embedding` | `vector(1536) not null` | Embedding из `text-embedding-3-small`, размерность 1536. |
| `token_count` | `integer not null` | Полезно для контроля размера чанков и стоимости embeddings. |
| `char_count` | `integer not null` | Полезно для отладки стратегии разбиения. |
| `chunk_hash` | `char(64) not null` | Хэш чанка для идемпотентной переиндексации. |
| `created_at` | `timestamptz not null default now()` | Время создания чанка. |

#### Индексы

- `unique index (document_id, chunk_no)` — чтобы не было повторяющихся номеров чанков в одном документе.
- `index (document_id)` — ускоряет выборку и удаление по документу.
- `gin index (content_tsv)` — нужен для full-text поиска.
- `hnsw index (embedding vector_cosine_ops)` — нужен для поиска похожих векторов.
- `index (chunk_hash)` — ускоряет контроль изменившихся чанков при переиндексации.

#### Связи

- `knowledge_chunks.document_id -> knowledge_documents.id`.

#### Почему именно `vector(1536)`

Для `OpenAI text-embedding-3-small` используется размерность `1536`, поэтому тип `vector(1536)` напрямую соответствует модели и не требует дополнительного преобразования.  
Этот вариант выбран как компромисс между стоимостью и качеством:

- embeddings достаточно хорошие для FAQ и KB;
- индексирование обходится дешево;
- модель хорошо подходит для MVP малого бизнеса.

---

### 6.3. Таблица `leads`

**Назначение:** хранит заявки клиентов, собранные ботом через FSM.

#### Поля

| Поле | Тип | Объяснение выбора |
|---|---|---|
| `id` | `bigserial primary key` | Внутренний идентификатор заявки. |
| `telegram_chat_id` | `bigint not null` | ID чата Telegram, откуда пришла заявка. |
| `telegram_user_id` | `bigint null` | ID пользователя Telegram, если доступен. |
| `telegram_username` | `text null` | Удобно для ручной обработки заявки. |
| `customer_name` | `text not null` | Имя клиента без искусственного ограничения длины. |
| `phone_raw` | `text not null` | Оригинальный телефон в том виде, как его ввел клиент. |
| `phone_normalized` | `text not null` | Нормализованный телефон для поиска и дедупликации. |
| `question` | `text not null` | Суть запроса клиента. |
| `status` | `text not null default 'new'` | Статус обработки заявки. |
| `thread_id` | `bigint null references dialog_threads(id) on delete set null` | Связь с диалогом, если история включена. |
| `notified_at` | `timestamptz null` | Когда владелец получил уведомление. |
| `created_at` | `timestamptz not null default now()` | Когда заявка создана. |
| `handled_at` | `timestamptz null` | Когда заявка была обработана вручную. |

#### Индексы

- `index (status, created_at desc)` — для быстрой работы со списком новых заявок.
- `index (phone_normalized)` — для поиска дублей и истории по номеру.
- `index (telegram_user_id, created_at desc)` — для истории обращений пользователя.
- `index (thread_id)` — если используется история диалогов.

#### Связи

- опционально `leads.thread_id -> dialog_threads.id`.

---

### 6.4. Таблица `dialog_threads` (опционально)

**Назначение:** хранит диалоговые сессии пользователя с ботом.

#### Поля

| Поле | Тип | Объяснение выбора |
|---|---|---|
| `id` | `bigserial primary key` | Внутренний идентификатор треда. |
| `telegram_chat_id` | `bigint not null` | Основной идентификатор чата. |
| `telegram_user_id` | `bigint null` | Пользователь Telegram, если известен. |
| `telegram_username` | `text null` | Удобно для поддержки и поиска. |
| `status` | `text not null default 'open'` | Состояние диалога. |
| `started_at` | `timestamptz not null default now()` | Когда началась сессия. |
| `last_message_at` | `timestamptz not null default now()` | Когда пришло последнее сообщение. |
| `closed_at` | `timestamptz null` | Когда сессия была закрыта. |

#### Индексы

- `index (telegram_chat_id, last_message_at desc)` — для быстрого поиска активного диалога.
- `index (status, last_message_at desc)` — для аналитики и фоновой обработки.

#### Связи

- `dialog_threads.id -> dialog_messages.thread_id` как `1:N`.
- `dialog_threads.id -> leads.thread_id` как `1:N`.

---

### 6.5. Таблица `dialog_messages` (опционально)

**Назначение:** хранит отдельные сообщения внутри диалогов для аналитики и отладки.

#### Поля

| Поле | Тип | Объяснение выбора |
|---|---|---|
| `id` | `bigserial primary key` | Внутренний идентификатор сообщения. |
| `thread_id` | `bigint not null references dialog_threads(id) on delete cascade` | Сообщение относится к определенному диалогу. |
| `telegram_message_id` | `bigint null` | Позволяет не записывать одно и то же сообщение дважды. |
| `direction` | `text not null` | `in` или `out`, чтобы различать входящее и исходящее сообщение. |
| `role` | `text not null` | `user`, `assistant`, `system`. |
| `text` | `text not null` | Текст сообщения. |
| `answer_mode` | `text null` | Режим ответа: `rag`, `out_of_scope`, `lead_offer`, `lead_form`. |
| `matched_chunk_ids` | `bigint[] null` | Какие чанки использовались для ответа. |
| `llm_model` | `text null` | Какая модель реально отвечала. |
| `prompt_tokens` | `integer null` | Контроль стоимости prompt. |
| `completion_tokens` | `integer null` | Контроль стоимости completion. |
| `created_at` | `timestamptz not null default now()` | Время сообщения. |

#### Индексы

- `index (thread_id, created_at)` — восстанавливает диалог в правильном порядке.
- `unique index (telegram_message_id)` — защищает от дублей, если ID доступен.
- `index (answer_mode, created_at desc)` — помогает анализировать fallback и оффтоп.

#### Связи

- `dialog_messages.thread_id -> dialog_threads.id`.

---

### Минимальный набор таблиц для MVP

- `knowledge_documents`
- `knowledge_chunks`
- `leads`

### Таблицы второго этапа

- `dialog_threads`
- `dialog_messages`

Они не обязательны для старта, но сильно помогают анализировать качество ответов и поведение пользователей.

---

## 7. Поток данных: пользователь задает вопрос

### Цель сценария

Понять, можно ли уверенно ответить по базе знаний, и только после этого вызывать LLM.

### Последовательность шагов

1. Пользователь отправляет сообщение в Telegram.
2. `app/main.py` получает update через `long polling`.
3. `app/bot/handlers/question.py` принимает сообщение и передает его в `app/use_cases/answer_company_question.py`.
4. `answer_company_question.py` вызывает `app/rag/scope_guard.py`.
5. `scope_guard.py` проверяет:
   - относится ли вопрос к тематике компании;
   - есть ли смысл продолжать retrieval.
6. Если вопрос явно вне тематики, бот сразу отвечает шаблоном из `app/bot/texts/out_of_scope.py` и предлагает оставить заявку.
7. Если вопрос подходит по теме, `app/providers/openai_embeddings.py` строит embedding пользовательского запроса.
8. `app/rag/hybrid_retriever.py` выполняет:
   - vector search по `knowledge_chunks.embedding`;
   - full-text search по `knowledge_chunks.content_tsv`;
   - объединение и ранжирование результатов.
9. `app/rag/context_builder.py` собирает лучшие чанки в компактный контекст.
10. `app/rag/confidence_checker.py` оценивает силу результатов.
11. Если уверенность ниже порога, бот отправляет fallback из `app/bot/texts/low_confidence.py` и предлагает заявку.
12. Если уверенность достаточна, `app/rag/prompt_builder.py` формирует строгий prompt.
13. `app/rag/answer_generator.py` через `app/providers/openai_chat.py` вызывает `GPT-5 mini`.
14. Ответ возвращается в `question.py`.
15. Бот отправляет ответ пользователю.
16. Если включена история, данные пишутся в `dialog_messages`.

### Какие модули участвуют и в каком порядке

1. `bot/handlers/question.py`
2. `use_cases/answer_company_question.py`
3. `rag/scope_guard.py`
4. `providers/openai_embeddings.py`
5. `rag/hybrid_retriever.py`
6. `rag/context_builder.py`
7. `rag/confidence_checker.py`
8. `rag/prompt_builder.py`
9. `rag/answer_generator.py`
10. `providers/openai_chat.py`
11. `db/repositories/message_logs.py` или `dialog_messages` при включенном логировании

### Где возможны задержки

#### 1. Построение embedding запроса

Это внешний API-вызов.  
Решение:

- ставить короткий timeout;
- логировать ошибки;
- при сбое уходить в fallback, а не зависать.

#### 2. Hybrid retrieval в PostgreSQL

Задержка возникает, если:

- нет `GIN` индекса на `content_tsv`;
- нет `HNSW` индекса на `embedding`;
- слишком много нерелевантных чанков.

Решение:

- индексировать данные;
- ограничивать `top_k`;
- хранить чанки разумного размера.

#### 3. Генерация ответа через LLM

Это самый дорогой по времени участок.

Решение:

- отправлять `typing...` пользователю;
- ограничивать размер контекста;
- задавать таймаут;
- не вызывать модель при слабом retrieval.

### Почему поток устроен именно так

- Сначала фильтр тематики, потом retrieval, потом LLM — это снижает стоимость.
- Retrieval идет до генерации, потому что бот должен отвечать только по базе знаний.
- Fallback нужен, чтобы не выдавать галлюцинации.

---

## 8. Поток данных: пользователь хочет записаться на консультацию

### Цель сценария

Собрать заявку детерминированно и без участия LLM.

### Последовательность FSM

1. Пользователь нажимает кнопку записи или соглашается оставить заявку после fallback.
2. `app/bot/handlers/lead.py` переводит пользователя в состояние `waiting_for_name`.
3. Бот просит указать имя.
4. После получения имени бот сохраняет его во временное FSM-хранилище и переводит пользователя в `waiting_for_phone`.
5. Бот просит телефон.
6. После получения телефона бот:
   - валидирует формат;
   - сохраняет `phone_raw`;
   - строит `phone_normalized`;
   - переводит пользователя в `waiting_for_question`.
7. Бот просит описать вопрос или тему консультации.
8. После получения вопроса FSM собирает полную структуру заявки.
9. `app/use_cases/create_lead.py` сохраняет заявку в таблицу `leads`.
10. `app/use_cases/notify_owner.py` отправляет уведомление владельцу в Telegram.
11. Пользователь получает подтверждение, что заявка принята.
12. FSM очищается.

### Состояния бота

| Состояние | Зачем нужно |
|---|---|
| `idle` | Базовое состояние, когда бот не собирает заявку. |
| `waiting_for_name` | Получаем минимальный входной контакт в самом простом шаге. |
| `waiting_for_phone` | Получаем ключевой контактный канал до длинного текста вопроса. |
| `waiting_for_question` | Получаем суть запроса после того, как контакт уже сохранен. |
| `completed` | Техническая точка завершения перед очисткой состояния. |

### Почему порядок именно такой

#### Сначала имя

Это самый легкий шаг для пользователя.  
Он снижает барьер входа в сценарий.

#### Потом телефон

Это ключевой бизнес-результат заявки.  
Если человек оборвет сценарий позже, контакт уже будет почти собран.

#### Потом вопрос

После имени и телефона пользователь уже более вовлечен и обычно пишет подробнее.

### Куда идут данные после сбора

#### 1. В таблицу `leads`

Там сохраняются:

- имя;
- телефон в сыром и нормализованном виде;
- вопрос;
- Telegram-идентификаторы;
- статус заявки;
- время создания.

#### 2. В Telegram владельца или админ-группу

Уведомление отправляется через `notify_owner.py` в `LEAD_NOTIFICATION_CHAT_ID`.

#### 3. Опционально в историю диалогов

Если история включена, заявка связывается с `dialog_threads`, а сообщения сценария пишутся в `dialog_messages`.

### Почему FSM отделен от RAG

- Сбор имени и телефона должен быть предсказуемым.
- Нельзя доверять критичные поля генеративной логике.
- Потерянная или испорченная заявка дороже, чем неточный FAQ-ответ.

---

## 9. Практический вывод для реализации

На первом этапе достаточно реализовать:

1. ingestion KB из `data/knowledge/company_kb.md`;
2. таблицы `knowledge_documents`, `knowledge_chunks`, `leads`;
3. online RAG pipeline с порогами уверенности;
4. FSM для заявки;
5. уведомление владельца в Telegram.

Историю диалогов можно добавить вторым этапом, когда появится задача:

- анализировать неотвеченные вопросы;
- оптимизировать траты на API;
- улучшать базу знаний по реальным обращениям.

