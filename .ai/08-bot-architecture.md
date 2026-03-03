# 08. Bot Architecture

Актуально на **3 марта 2026**.

Документ фиксирует архитектурную проработку Telegram-бота секретаря с RAG на стеке из [07-stack-research.md](/Users/oleg/Documents/work/cut-code/workshop-ai-1/.ai/07-stack-research.md):

- **Python 3.12+**
- **aiogram 3**
- **PostgreSQL**
- **pgvector**
- **PostgreSQL Full Text Search**
- **самописный RAG pipeline**
- **long polling** на старте

---

## 1. Цель архитектуры

Бот должен решать три практические задачи:

1. отвечать на вопросы клиентов по базе знаний компании;
2. собирать заявки на консультацию;
3. не тратить LLM API там, где можно ответить через retrieval или прямой FAQ-ответ.

Архитектурный принцип:

**один файл — одна ответственность**

Это уменьшает связность и делает систему понятной для сопровождения:

- Telegram-обработчики не знают SQL;
- SQL-слой не знает про aiogram;
- RAG-логика не смешивается с FSM заявки;
- LLM-провайдер можно заменить без переписывания бизнес-логики.

---

## 2. Структура проекта

```text
bot/
├── .env.example                           # шаблон переменных окружения для локального запуска и деплоя
├── README.md                              # инструкция по запуску, миграциям, индексации и структуре проекта
├── pyproject.toml                         # зависимости Python, настройки инструментов и entrypoints
│
├── app/
│   ├── main.py                            # главный entrypoint приложения и запуск long polling
│   ├── bootstrap.py                       # сборка всех зависимостей приложения в одном месте
│   │
│   ├── config/
│   │   ├── settings.py                    # чтение .env и типизированная конфигурация
│   │   └── logging.py                     # настройка логирования
│   │
│   ├── bot/
│   │   ├── router.py                      # регистрация aiogram routers
│   │   └── commands.py                    # регистрация команд Telegram
│   │
│   ├── handlers/
│   │   ├── start.py                       # обработка /start и стартового сценария
│   │   ├── knowledge.py                   # обработка вопросов по базе знаний
│   │   ├── lead.py                        # FSM-сценарий сбора заявки
│   │   └── fallback.py                    # ответы на непонятные или неподдерживаемые сообщения
│   │
│   ├── fsm/
│   │   └── lead_form.py                   # состояния сценария заявки
│   │
│   ├── services/
│   │   ├── intent_service.py              # определение интента: вопрос, заявка, fallback
│   │   ├── lead_service.py                # валидация и сохранение заявки
│   │   ├── notification_service.py        # уведомление владельца о новой заявке
│   │   └── dialog_log_service.py          # журналирование вопросов, ответов и retrieval-метаданных
│   │
│   ├── rag/
│   │   ├── knowledge_loader.py            # чтение текстового файла базы знаний
│   │   ├── text_normalizer.py             # нормализация текстов перед индексированием и поиском
│   │   ├── chunker.py                     # разбиение документа на чанки
│   │   ├── indexer.py                     # генерация embeddings и запись индекса в PostgreSQL
│   │   ├── retriever.py                   # hybrid retrieval: FTS + vector search + merge
│   │   ├── relevance_policy.py            # решение, достаточно ли уверенности для ответа
│   │   ├── direct_answer_resolver.py      # прямой ответ без LLM при высоком confidence
│   │   ├── prompt_builder.py              # сборка prompt из вопроса и чанков
│   │   └── answer_service.py              # оркестрация RAG pipeline
│   │
│   ├── adapters/
│   │   ├── llm/
│   │   │   ├── base.py                    # интерфейс LLM-провайдера
│   │   │   └── openai_adapter.py          # адаптер OpenAI для генерации ответа
│   │   └── embeddings/
│   │       ├── base.py                    # интерфейс embeddings-провайдера
│   │       └── openai_adapter.py          # адаптер OpenAI для embeddings
│   │
│   ├── repositories/
│   │   ├── knowledge_repository.py        # SQL для документов и чанков базы знаний
│   │   ├── lead_repository.py             # SQL для заявок
│   │   └── dialog_log_repository.py       # SQL для истории диалогов и технических логов
│   │
│   └── db/
│       └── connection.py                  # создание и выдача пула соединений PostgreSQL
│
├── migrations/
│   ├── 001_enable_pgvector.sql            # расширение pgvector и базовая подготовка БД
│   ├── 002_create_knowledge_tables.sql    # таблицы базы знаний и индексы retrieval
│   ├── 003_create_leads_table.sql         # таблица заявок
│   └── 004_create_dialog_tables.sql       # опциональная история диалогов
│
├── scripts/
│   ├── run_bot.py                         # CLI-скрипт запуска бота
│   └── reindex_knowledge.py               # ручная переиндексация базы знаний после изменения файла
│
├── knowledge/
│   └── company.md                         # редактируемая бизнесом база знаний без программирования
│
└── tests/
    ├── test_lead_flow.py                  # тест FSM-сценария заявки
    ├── test_retriever.py                  # тест retrieval и merge ранжирования
    └── test_relevance_policy.py           # тест логики экономии LLM API
```

### Почему структура именно такая

- **`app/handlers` отделены от `app/services`**, чтобы Telegram-слой не хранил бизнес-правила.
- **`app/services` отделены от `app/repositories`**, чтобы SQL не расползался по приложению.
- **`app/rag` вынесен в отдельный контур**, потому что ingestion, retrieval и answer generation меняются независимо от Telegram-части.
- **`adapters` вынесены отдельно**, чтобы не привязывать бизнес-логику к SDK конкретного AI-провайдера.
- **`knowledge/company.md` лежит отдельно от кода**, чтобы базу знаний можно было редактировать как обычный текст.
- **`scripts/reindex_knowledge.py` существует отдельно**, потому что переиндексация знаний — это операционный сценарий, а не runtime-логика бота.
- **`migrations/` ведутся SQL-файлами**, потому что схема БД должна быть явной, проверяемой и воспроизводимой.

---

## 3. Ответственность модулей

- `main.py` отвечает только за запуск приложения.
- `bootstrap.py` отвечает только за сборку зависимостей.
- `settings.py` отвечает только за конфигурацию.
- `logging.py` отвечает только за логирование.
- `router.py` отвечает только за регистрацию роутеров.
- `commands.py` отвечает только за команды Telegram.
- `start.py` отвечает только за стартовый сценарий.
- `knowledge.py` отвечает только за сценарий вопроса по базе знаний.
- `lead.py` отвечает только за сценарий заявки.
- `fallback.py` отвечает только за сценарий непонятного сообщения.
- `lead_form.py` отвечает только за состояния FSM заявки.
- `intent_service.py` отвечает только за определение типа пользовательского запроса.
- `lead_service.py` отвечает только за обработку заявки.
- `notification_service.py` отвечает только за уведомление владельца.
- `dialog_log_service.py` отвечает только за запись журналов диалога.
- `knowledge_loader.py` отвечает только за чтение источника знаний.
- `text_normalizer.py` отвечает только за очистку и нормализацию текста.
- `chunker.py` отвечает только за нарезку текста на чанки.
- `indexer.py` отвечает только за индексацию знаний.
- `retriever.py` отвечает только за поиск релевантных чанков.
- `relevance_policy.py` отвечает только за решение, можно ли отвечать уверенно.
- `direct_answer_resolver.py` отвечает только за дешёвый ответ без LLM.
- `prompt_builder.py` отвечает только за сборку prompt.
- `answer_service.py` отвечает только за orchestration ответа.
- `knowledge_repository.py` отвечает только за SQL по знаниям.
- `lead_repository.py` отвечает только за SQL по заявкам.
- `dialog_log_repository.py` отвечает только за SQL по истории диалогов.
- `connection.py` отвечает только за доступ к PostgreSQL.

---

## 4. Переменные окружения

| Переменная | Зачем нужна |
|---|---|
| `APP_ENV` | Разделяет режимы `dev`, `test`, `prod` без изменения кода. |
| `LOG_LEVEL` | Управляет уровнем подробности логов. |
| `TELEGRAM_BOT_TOKEN` | Секрет доступа к Telegram Bot API. |
| `TELEGRAM_OWNER_CHAT_ID` | Чат владельца, куда приходят уведомления о заявках. |
| `DATABASE_URL` | Подключение к PostgreSQL одной строкой. |
| `LLM_PROVIDER` | Позволяет менять LLM-провайдера без правки бизнес-логики. |
| `LLM_API_KEY` | Секрет для вызова облачной LLM. |
| `LLM_MODEL` | Имя модели генерации ответа. |
| `EMBEDDINGS_PROVIDER` | Позволяет менять embeddings-провайдера отдельно от LLM. |
| `EMBEDDINGS_API_KEY` | Секрет для embeddings API. |
| `EMBEDDINGS_MODEL` | Имя embeddings-модели для индексации и поиска. |
| `KNOWLEDGE_FILE_PATH` | Путь к редактируемому файлу базы знаний. |
| `RAG_TOP_K` | Сколько чанков брать в контекст. |
| `RAG_MIN_CONFIDENCE` | Порог уверенности для ответа. |
| `DIRECT_ANSWER_SCORE` | Порог, при котором можно ответить без LLM. |

Пример:

```env
APP_ENV=dev
LOG_LEVEL=INFO

TELEGRAM_BOT_TOKEN=
TELEGRAM_OWNER_CHAT_ID=

DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/secretary_bot

LLM_PROVIDER=openai
LLM_API_KEY=
LLM_MODEL=gpt-4.1-mini

EMBEDDINGS_PROVIDER=openai
EMBEDDINGS_API_KEY=
EMBEDDINGS_MODEL=text-embedding-3-small

KNOWLEDGE_FILE_PATH=./knowledge/company.md

RAG_TOP_K=5
RAG_MIN_CONFIDENCE=0.72
DIRECT_ANSWER_SCORE=0.90
```

---

## 5. Схема базы данных

Минимальный состав таблиц:

- `kb_documents`
- `kb_chunks`
- `leads`

Опционально для истории диалогов:

- `dialog_sessions`
- `dialog_messages`

### Почему `vector(1536)`

Для embeddings выбран размер `vector(1536)`, потому что это стандартная размерность модели **`text-embedding-3-small`**.

Почему это хорошее решение:

- это дешёвая модель для регулярной переиндексации базы знаний;
- для малого бизнеса её качества обычно достаточно;
- размер вектора меньше, чем у более тяжёлых моделей, значит дешевле хранение и быстрее retrieval;
- это удобный баланс между стоимостью, качеством и простотой эксплуатации.

Практически:

- `text-embedding-3-small` хорошо подходит для FAQ и knowledge bot;
- цена низкая, порядка **нескольких центов за миллион токенов**, поэтому переиндексация небольшого markdown/txt-корпуса не становится дорогой операцией.

---

## 6. Таблицы базы данных

### 6.1. `kb_documents`

Назначение: хранит исходные документы базы знаний и их версии.

| Поле | Тип | Почему выбран этот тип |
|---|---|---|
| `id` | `bigint generated always as identity primary key` | Компактный числовой PK, удобный для join и индексов. |
| `source_path` | `text not null` | Путь к исходному файлу вроде `knowledge/company.md`. |
| `title` | `text not null` | Название документа для отладки и вывода. |
| `source_type` | `text not null` | Тип источника, например `markdown` или `txt`; `text + check` проще PostgreSQL enum. |
| `content` | `text not null` | Снимок исходного текста на момент индексации. |
| `content_sha256` | `char(64) not null` | Хэш для контроля изменений и дедупликации. |
| `version` | `integer not null` | Номер версии документа после переиндексации. |
| `is_active` | `boolean not null default true` | Позволяет хранить несколько версий, но использовать одну активную. |
| `created_at` | `timestamptz not null default now()` | Время создания записи с учётом таймзон. |
| `indexed_at` | `timestamptz not null default now()` | Время индексации. |

Индексы:

- `primary key (id)` — основной ключ документа.
- `unique (source_path, version)` — одна версия файла не может дублироваться.
- `unique (source_path) where is_active = true` — активна только одна версия на путь.
- `index (is_active, indexed_at desc)` — быстрый доступ к актуальным документам.

Связи:

- `kb_documents.id -> kb_chunks.document_id`

Почему таблица выделена отдельно:

- нужен уровень версионности документа;
- чанки должны знать своё происхождение;
- это позволяет безопасно переиндексировать знания.

### 6.2. `kb_chunks`

Назначение: хранит чанки базы знаний, embeddings и текстовый индекс для hybrid retrieval.

| Поле | Тип | Почему выбран этот тип |
|---|---|---|
| `id` | `bigint generated always as identity primary key` | Компактный PK для retrieval-таблицы. |
| `document_id` | `bigint not null references kb_documents(id) on delete cascade` | Каждый чанк привязан к версии документа. |
| `chunk_no` | `integer not null` | Порядок чанка внутри документа. |
| `section_title` | `text null` | Заголовок раздела, если он есть. |
| `content` | `text not null` | Текст чанка. |
| `token_count` | `integer not null` | Нужен для контроля размера контекста. |
| `embedding` | `vector(1536) not null` | Вектор под `text-embedding-3-small`. |
| `embedding_model` | `text not null default 'text-embedding-3-small'` | Явно фиксирует, какой моделью построен embedding. |
| `content_tsv` | `tsvector generated always as (...) stored` | Предвычисленный вектор для PostgreSQL FTS. |
| `metadata` | `jsonb not null default '{}'::jsonb` | Гибкие технические метаданные: секция, теги, offsets. |
| `created_at` | `timestamptz not null default now()` | Время создания чанка. |

Индексы:

- `unique (document_id, chunk_no)` — внутри документа номер чанка уникален.
- `index (document_id)` — быстрый доступ ко всем чанкам документа.
- `gin (content_tsv)` — полнотекстовый поиск по ключевым словам.
- `hnsw (embedding vector_cosine_ops)` — быстрый semantic search по cosine distance.
- опционально `index ((metadata->>'category'))` — если появятся категории или фильтры.

Связи:

- `kb_chunks.document_id -> kb_documents.id`

Почему таблица устроена именно так:

- в одной записи лежат и текст, и FTS-индекс, и embedding;
- это удобно для hybrid retrieval;
- `metadata` даёт гибкость без раздувания схемы.

### 6.3. `leads`

Назначение: хранит заявки клиентов, пришедшие через Telegram-бота.

| Поле | Тип | Почему выбран этот тип |
|---|---|---|
| `id` | `bigint generated always as identity primary key` | Простой и дешёвый PK. |
| `telegram_user_id` | `bigint null` | Telegram user id числовой и стабильно хранится в `bigint`. |
| `telegram_chat_id` | `bigint not null` | Позволяет связать заявку с чатом. |
| `telegram_username` | `text null` | Username может отсутствовать и меняться. |
| `customer_name` | `text not null` | Имя вводится свободным текстом. |
| `phone_raw` | `text not null` | Телефон в том виде, как его прислал пользователь. |
| `phone_normalized` | `text not null` | Нормализованный номер для поиска и дедупликации. |
| `question` | `text not null` | Суть запроса или консультации. |
| `status` | `text not null default 'new'` | Статус обработки заявки; `text + check` гибче enum. |
| `owner_notified_at` | `timestamptz null` | Когда владельцу ушло уведомление. |
| `owner_message_id` | `bigint null` | Id сообщения у владельца для reply-flow. |
| `created_at` | `timestamptz not null default now()` | Время создания заявки. |
| `updated_at` | `timestamptz not null default now()` | Время последнего изменения. |

Индексы:

- `index (status, created_at desc)` — быстро находить новые заявки.
- `index (telegram_user_id, created_at desc)` — история обращений пользователя.
- `index (phone_normalized)` — поиск и дедупликация по телефону.
- опционально `index (owner_notified_at)` — контроль неотправленных уведомлений.

Связи:

- в минимальной схеме таблица автономна;
- в расширенной схеме на неё могут ссылаться `dialog_sessions`.

Почему таблица устроена именно так:

- одновременно храним исходный и нормализованный телефон;
- статус позволяет повторно отправлять уведомления и вести простую обработку;
- `owner_message_id` пригодится, если появится reply workflow из Telegram владельца.

### 6.4. `dialog_sessions` (опционально)

Назначение: хранит пользовательские сессии диалога.

| Поле | Тип | Почему выбран этот тип |
|---|---|---|
| `id` | `bigint generated always as identity primary key` | PK сессии. |
| `telegram_user_id` | `bigint not null` | Пользователь Telegram. |
| `telegram_chat_id` | `bigint not null` | Чат Telegram. |
| `started_at` | `timestamptz not null default now()` | Начало сессии. |
| `last_message_at` | `timestamptz not null default now()` | Последняя активность. |
| `closed_at` | `timestamptz null` | Когда сессия завершилась. |
| `current_intent` | `text null` | Последний определённый интент. |
| `fsm_state` | `text null` | Последнее FSM-состояние для отладки сценария заявки. |
| `lead_id` | `bigint null references leads(id) on delete set null` | Если из диалога родилась заявка. |

Индексы:

- `index (telegram_chat_id, last_message_at desc)` — быстро найти текущую сессию чата.
- `index (telegram_user_id, last_message_at desc)` — история пользователя.
- `partial index where closed_at is null` — выборка активных сессий.

Связи:

- `dialog_sessions.lead_id -> leads.id`
- `dialog_sessions.id -> dialog_messages.session_id`

### 6.5. `dialog_messages` (опционально)

Назначение: хранит отдельные сообщения и техническую информацию по ответам.

| Поле | Тип | Почему выбран этот тип |
|---|---|---|
| `id` | `bigint generated always as identity primary key` | PK сообщения. |
| `session_id` | `bigint not null references dialog_sessions(id) on delete cascade` | Связь с сессией. |
| `telegram_message_id` | `bigint null` | Id сообщения Telegram для трассировки. |
| `role` | `text not null` | `user`, `assistant`, `system`; `text + check` проще сопровождать. |
| `message_text` | `text not null` | Текст сообщения. |
| `intent` | `text null` | Интент, определённый на этом шаге. |
| `answer_strategy` | `text null` | `direct`, `llm`, `fallback`, `lead_flow`. |
| `retrieval_meta` | `jsonb null` | Top chunks, scores, latency, модель, технические детали. |
| `created_at` | `timestamptz not null default now()` | Время создания записи. |

Индексы:

- `index (session_id, created_at)` — читать диалог по порядку.
- `index (created_at desc)` — быстро смотреть последние сообщения.
- `index (answer_strategy, created_at desc)` — анализировать расход API.
- опционально `gin (retrieval_meta jsonb_path_ops)` — если нужен поиск по technical metadata.

Связи:

- `dialog_messages.session_id -> dialog_sessions.id`

---

## 7. Схема связей

Минимальный вариант:

```text
kb_documents 1 ──< kb_chunks

leads
```

Расширенный вариант:

```text
kb_documents 1 ──< kb_chunks

leads 1 ── 0..1 dialog_sessions 1 ──< dialog_messages
```

Логика:

- один документ содержит много чанков;
- одна сессия содержит много сообщений;
- одна заявка может быть связана с сессией, из которой она возникла.

---

## 8. Поток данных №1: пользователь задаёт вопрос

Цель сценария:

- ответить по базе знаний;
- не тратить LLM без необходимости;
- безопасно уйти в fallback, если знания недостаточно.

### Пошаговая схема

1. `app.main.run_bot()` запускает long polling и принимает обновление от Telegram.
2. `bot.router.register_routers()` направляет сообщение в `handlers.knowledge.handle_knowledge_message(message, state, services)`.
3. `services.intent_service.detect_intent(text)` определяет, что это вопрос, а не заявка.
4. `rag.answer_service.answer_question(user_text)` запускает RAG pipeline.
5. `rag.text_normalizer.normalize_query(user_text)` нормализует пользовательский вопрос.
6. `rag.retriever.retrieve(query)` выполняет hybrid retrieval.
7. `repositories.knowledge_repository.search_fts(query)` ищет совпадения по `content_tsv`.
8. `repositories.knowledge_repository.search_vector(query_embedding)` ищет semantic matches по `embedding`.
9. `rag.retriever.merge_results(fts_hits, vector_hits)` объединяет результаты и считает итоговый score.
10. `rag.relevance_policy.should_answer(result_set)` решает, есть ли достаточно уверенный ответ.
11. Если уверенность низкая, `rag.answer_service.build_fallback_response()` формирует безопасный fallback: нет точной информации, можно оставить заявку.
12. Если уверенность высокая, `rag.direct_answer_resolver.try_resolve(result_set)` пытается вернуть прямой ответ без LLM.
13. Если direct answer не подходит, `rag.prompt_builder.build_prompt(question, chunks)` собирает prompt.
14. `adapters.llm.openai_adapter.generate_answer(prompt)` вызывает LLM.
15. `services.dialog_log_service.log_qa(...)` записывает результат, top chunks и strategy ответа.
16. `handlers.knowledge.handle_knowledge_message(...)` отправляет ответ через `message.answer(response_text)`.

### Порядок модулей

```text
Telegram Update
-> handlers.knowledge.handle_knowledge_message()
-> services.intent_service.detect_intent()
-> rag.answer_service.answer_question()
-> rag.text_normalizer.normalize_query()
-> rag.retriever.retrieve()
-> repositories.knowledge_repository.search_fts()
-> repositories.knowledge_repository.search_vector()
-> rag.retriever.merge_results()
-> rag.relevance_policy.should_answer()
-> rag.direct_answer_resolver.try_resolve() / rag.prompt_builder.build_prompt()
-> adapters.llm.openai_adapter.generate_answer()
-> services.dialog_log_service.log_qa()
-> Telegram message.answer()
```

### Где могут быть задержки

#### 1. Telegram long polling

Причина:

- сеть;
- кратковременные ошибки Bot API.

Обработка:

- retry и устойчивый polling;
- идемпотентные handlers.

#### 2. Получение query embedding

Причина:

- отдельный внешний API вызов к embeddings-провайдеру.

Обработка:

- таймаут;
- retry с backoff;
- кэширование embeddings для повторяющихся вопросов.

#### 3. Retrieval в PostgreSQL

Причина:

- рост объёма чанков;
- плохо настроенные индексы.

Обработка:

- `GIN` индекс для `tsvector`;
- `HNSW` индекс для `embedding`;
- ограничение `top_k`.

#### 4. Вызов LLM

Причина:

- самая дорогая и медленная точка пайплайна.

Обработка:

- вызывать LLM только после `relevance_policy`;
- сначала пытаться ответить через `direct_answer_resolver`;
- ставить таймаут и fallback при ошибке.

#### 5. Логирование

Причина:

- дополнительная запись в БД.

Обработка:

- одна короткая запись после ответа;
- best-effort режим, если лог временно не записался.

### Почему поток устроен именно так

- сначала определяется интент, чтобы не запускать RAG на явную заявку;
- затем идёт retrieval, потому что ответ должен опираться на базу знаний;
- затем идёт `relevance_policy`, чтобы не галлюцинировать и не тратить API зря;
- `direct_answer_resolver` идёт раньше LLM, чтобы закрывать простые FAQ бесплатно или почти бесплатно;
- логирование идёт в конце, чтобы не увеличивать latency ответа пользователю.

---

## 9. Поток данных №2: пользователь хочет записаться на консультацию

Цель сценария:

- провести пользователя по короткому сценарию;
- получить контакт и суть запроса;
- сохранить заявку и уведомить владельца.

### FSM-состояния

- `LeadForm.waiting_for_name`
- `LeadForm.waiting_for_phone`
- `LeadForm.waiting_for_question`

### Почему порядок именно такой

1. **Сначала имя** — это самый простой первый шаг, он снижает сопротивление пользователя.
2. **Потом телефон** — это обязательный контакт, который нужно проверить до финала.
3. **Потом вопрос** — после контакта пользователь обычно охотнее пишет детали.

Такой порядок минимизирует риск потерять лид до получения контактных данных.

### Пошаговая схема

1. Пользователь пишет: “хочу записаться”, “нужна консультация” или использует `/request`.
2. `handlers.lead.handle_lead_entry(message, state, services)` принимает событие.
3. `services.intent_service.detect_intent(text)` подтверждает интент `lead`.
4. `state.set_state(LeadForm.waiting_for_name)` переводит FSM в первый шаг.
5. `handlers.lead.ask_name(message, state)` отправляет вопрос: “Как вас зовут?”
6. Пользователь присылает имя.
7. `handlers.lead.receive_name(message, state)` валидирует ввод.
8. `state.update_data(customer_name=...)` сохраняет имя во временное FSM-хранилище.
9. `state.set_state(LeadForm.waiting_for_phone)` переводит бота к следующему шагу.
10. `handlers.lead.ask_phone(message, state)` просит телефон.
11. Пользователь присылает телефон.
12. `handlers.lead.receive_phone(message, state)` вызывает `services.lead_service.normalize_phone(raw_phone)`.
13. Если телефон невалиден, `handlers.lead.reject_phone(message)` просит ввести его заново и состояние не меняется.
14. Если телефон валиден, `state.update_data(phone_raw=..., phone_normalized=...)` сохраняет оба варианта номера.
15. `state.set_state(LeadForm.waiting_for_question)` переводит FSM на последний шаг.
16. `handlers.lead.ask_question(message, state)` просит описать вопрос или цель консультации.
17. Пользователь присылает текст вопроса.
18. `handlers.lead.receive_question(message, state)` сохраняет вопрос во временное состояние.
19. `handlers.lead.finish_lead_collection(message, state, services)` получает все собранные данные через `state.get_data()`.
20. `services.lead_service.create_lead(lead_data)` подготавливает заявку к сохранению.
21. `repositories.lead_repository.insert_lead(...)` записывает заявку в таблицу `leads`.
22. `services.notification_service.notify_owner(lead)` отправляет владельцу уведомление в Telegram.
23. `services.dialog_log_service.log_lead_created(...)` опционально фиксирует событие в историю.
24. `state.clear()` очищает FSM.
25. `handlers.lead.send_confirmation(message)` отправляет пользователю подтверждение.

### Порядок модулей

```text
Telegram Update
-> handlers.lead.handle_lead_entry()
-> services.intent_service.detect_intent()
-> state.set_state(LeadForm.waiting_for_name)
-> handlers.lead.receive_name()
-> state.set_state(LeadForm.waiting_for_phone)
-> handlers.lead.receive_phone()
-> services.lead_service.normalize_phone()
-> state.set_state(LeadForm.waiting_for_question)
-> handlers.lead.receive_question()
-> services.lead_service.create_lead()
-> repositories.lead_repository.insert_lead()
-> services.notification_service.notify_owner()
-> services.dialog_log_service.log_lead_created()
-> state.clear()
-> Telegram message.answer()
```

### Что происходит после сбора данных

После завершения FSM данные идут в три направления:

1. **В таблицу `leads`**
   - `customer_name`
   - `phone_raw`
   - `phone_normalized`
   - `question`
   - `telegram_user_id`
   - `telegram_chat_id`

2. **В уведомление владельцу**
   - имя клиента;
   - телефон;
   - текст запроса;
   - техническая ссылка на Telegram-пользователя при необходимости.

3. **Опционально в историю диалогов**
   - `dialog_sessions`
   - `dialog_messages`

### Где могут быть задержки

#### 1. Пользователь делает паузу между шагами

Это нормальный сценарий.

Обработка:

- FSM хранит текущее состояние;
- диалог можно продолжить с последнего шага.

#### 2. Валидация телефона

Причина:

- номер введён в свободной форме.

Обработка:

- локальная нормализация без внешних API;
- повтор запроса на том же состоянии при ошибке.

#### 3. Сохранение заявки в БД

Причина:

- кратковременная ошибка базы.

Обработка:

- заявка сохраняется транзакционно;
- если запись не удалась, FSM не очищается и пользователь может повторить попытку позже.

#### 4. Уведомление владельца

Причина:

- ошибки сети или Telegram API.

Обработка:

- заявка уже есть в `leads`;
- статус можно оставить `new` или `notification_pending`;
- уведомление можно отправить повторно фоновым процессом.

### Почему поток устроен именно так

- сначала собираются простые и обязательные поля;
- запись в БД идёт раньше уведомления, чтобы лид не потерялся;
- FSM очищается только после успешного завершения бизнес-сценария;
- уведомление владельцу вынесено в отдельный сервис, потому что это самостоятельный канал доставки.

---

## 10. Резюме архитектурных решений

### Почему выбран такой проектный каркас

- он поддерживает чёткое разделение ответственности;
- его легко объяснить команде;
- он не зависит от тяжёлых RAG-фреймворков;
- он масштабируется от локального MVP к production.

### Почему выбран такой слой базы данных

- PostgreSQL хранит и бизнес-данные, и knowledge index;
- `pgvector` даёт semantic search без отдельной vector DB;
- PostgreSQL FTS даёт точный поиск по ключевым словам;
- hybrid retrieval лучше работает на реальных FAQ и внутренних документах.

### Почему бот сможет экономить API

- `relevance_policy` не даёт вызывать LLM без достаточного retrieval confidence;
- `direct_answer_resolver` позволяет отвечать без генерации там, где найден сильный матч;
- база знаний редактируется в одном текстовом файле и индексируется контролируемо, а не хаотично.

### Почему база знаний вынесена в текстовый файл

- это простой способ редактирования без админки и без разработчика;
- удобно хранить изменения в git;
- проще воспроизводить состояние знаний для отладки.

---

## 11. Что входит в MVP

- Telegram-бот на `aiogram 3`
- сценарий FAQ
- сценарий заявки
- `PostgreSQL + pgvector + FTS`
- индексация `markdown/txt`
- hybrid retrieval
- один LLM-провайдер
- журналирование запросов и ответов

Что можно отложить:

- сложный reranker
- web-admin
- агентные сценарии
- автоматическую переиндексацию по событиям файловой системы
- расширенную observability-платформу
