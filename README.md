# Двухсервисная система LLM-консультаций

Проект реализует два независимых сервиса:

- `auth_service` на FastAPI для регистрации, логина и выпуска JWT
- `bot_service` на aiogram/FastAPI для Telegram-бота, валидации JWT и асинхронной работы с LLM

Дополнительно используются:

- `RabbitMQ` как брокер задач Celery
- `Redis` как хранилище JWT для привязки к `Telegram user_id` и backend результатов
- `OpenRouter` как LLM API

Инфраструктура `Redis` и `RabbitMQ` развернута на удаленном Docker host `192.168.1.98` через локальный Docker CLI context `nucbox-rancher`.

## Структура проекта

- `auth_service/` — сервис авторизации и выпуска JWT
- `bot_service/` — Telegram-бот, Celery task, Redis, OpenRouter client
- `docker/` — manifest для удаленного разворачивания `Redis` и `RabbitMQ`
- `IMPLEMENTATION_PLAN.md` — план реализации
- `TelegramBot_Specification.md` — текст технического задания

## Используемое окружение

Проект настроен на уже существующее виртуальное окружение `.venv`.

VS Code настроен на интерпретатор:

- `.venv/bin/python`

## Установленные Python-зависимости

Зависимости установлены в `.venv` и также зафиксированы в:

- `auth_service/pyproject.toml`
- `bot_service/pyproject.toml`

## Переменные окружения

Для запуска используются файлы:

- `auth_service/.env.example`
- `bot_service/.env.example`

При необходимости создайте локальные `.env` рядом с ними и переопределите значения.

Критичные переменные для реального запуска:

- `JWT_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `OPENROUTER_API_KEY`

## Auth Service

Реализовано:

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /health`

Особенности:

- пароль хранится только в виде хеша
- JWT содержит `sub`, `role`, `iat`, `exp`
- endpoint-ы не содержат SQL и не создают токен напрямую

### Запуск Auth Service

```bash
cd auth_service
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger будет доступен по адресу:

- `http://0.0.0.0:8000/docs`

## Bot Service

Реализовано:

- команда `/token <jwt>`
- сохранение JWT в Redis по ключу `token:<telegram_user_id>`
- локальная проверка JWT без обращения к БД Auth Service
- постановка задач в Celery через RabbitMQ
- вызов OpenRouter из worker
- отправка ответа пользователю прямо из Celery worker
- `GET /health` для bot-side FastAPI части

### Запуск bot-side health API

```bash
cd bot_service
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Запуск Telegram-бота

```bash
cd bot_service
../.venv/bin/python run_bot.py
```

### Запуск Celery worker

```bash
cd bot_service
../.venv/bin/celery -A app.infra.celery_app:celery_app worker --loglevel=info
```

## Удаленная инфраструктура

Файл разворачивания:

- `docker/docker-compose.remote.yml`

Команда развертывания:

```bash
docker --context nucbox-rancher compose -f docker/docker-compose.remote.yml up -d
```

Что поднято на `192.168.1.98`:

- `Redis` на `6379`
- `RabbitMQ` на `5672`
- `RabbitMQ Management UI` на `15672`

Учетные данные RabbitMQ по текущему manifest:

- user: `llm_bot`
- password: `llm_bot_pass`

## Тестирование

### Auth Service

```bash
cd auth_service
../.venv/bin/ruff check .
../.venv/bin/pytest -q
```

### Bot Service

```bash
cd bot_service
../.venv/bin/ruff check .
../.venv/bin/pytest -q
```

## Что уже проверено

- `Auth Service`: `11 passed`
- `Bot Service`: `7 passed`
- `Ruff` проходит для обоих сервисов
- `Redis` и `RabbitMQ` развернуты на `192.168.1.98`

## Что требует ваших секретов

Для полного живого сценария с Telegram и OpenRouter нужны данные, которых нет в репозитории:

- `TELEGRAM_BOT_TOKEN`
- `OPENROUTER_API_KEY`

Без них код, тесты и инфраструктура проверяются локально, но живой end-to-end сценарий с реальным ботом и LLM не запускается.

## Пошаговая проверка полного сценария

1. Заполнить `auth_service/.env` и `bot_service/.env` при необходимости.
2. Поднять `Auth Service`.
3. Поднять `bot_service` FastAPI health API при необходимости.
4. Поднять `Celery worker`.
5. Запустить Telegram-бота.
6. В Swagger зарегистрировать пользователя с email в формате `surname@email.com`.
7. Выполнить логин и скопировать JWT.
8. Отправить боту команду `/token <jwt>`.
9. Отправить обычное текстовое сообщение.
10. Убедиться, что в RabbitMQ появилась активность, а бот вернул итоговый ответ.

## Материалы для сдачи

Нужно подготовить:

1. Скриншот Swagger с успешной регистрацией: [screenshots/01_auth_register.png](screenshots/01_auth_register.png)
2. Скриншот Swagger с успешным логином: [screenshots/02_auth_login.png](screenshots/02_auth_login.png)
3. Скриншот Swagger с успешным `/auth/me`: [screenshots/03_auth_me.png](screenshots/03_auth_me.png)
4. Скриншот ответа бота на `/start`: [screenshots/04_bot_start.png](screenshots/04_bot_start.png)
5. Скриншот подтверждения сохранения JWT после `/token <jwt>`: [screenshots/05_bot_token_saved.png](screenshots/05_bot_token_saved.png)
6. Скриншот итогового ответа бота на LLM-запрос: [screenshots/06_bot_llm_reply.png](screenshots/06_bot_llm_reply.png)
7. Скриншот очередей RabbitMQ: [screenshots/07_rabbitmq_queues.png](screenshots/07_rabbitmq_queues.png)
8. Скриншот RabbitMQ с consumers: [screenshots/08_rabbitmq_consumers.png](screenshots/08_rabbitmq_consumers.png)
9. Скриншот подтверждения ключа в Redis: [screenshots/09_redis_token_key.png](screenshots/09_redis_token_key.png)
10. Скриншот или лог успешного тестирования Auth Service: [screenshots/10_auth_tests.png](screenshots/10_auth_tests.png)
11. Скриншот или лог успешного тестирования Bot Service: [screenshots/11_bot_tests.png](screenshots/11_bot_tests.png)
12. Скриншот worker-лога с `received`, `200 OK`, `succeeded`: [screenshots/12_worker_log_success.png](screenshots/12_worker_log_success.png)

Все имена файлов уже зарезервированы в папке [screenshots](screenshots).

Подробная инструкция по подготовке этих материалов приведена в финальном отчете агента.
