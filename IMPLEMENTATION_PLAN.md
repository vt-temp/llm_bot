# План реализации проекта

## Цель

Реализовать систему из двух логически независимых сервисов в одном репозитории:

- `Auth Service` на FastAPI для регистрации, логина и выпуска JWT
- `Bot Service` на aiogram/FastAPI для Telegram-взаимодействия, валидации JWT и асинхронной работы с LLM через Celery, RabbitMQ, Redis и OpenRouter

Рекомендуемая схема реализации для этого ТЗ:

- JWT создается только в `Auth Service`
- `Bot Service` только валидирует токен
- для учебного варианта используется `HS256` с общим `JWT_SECRET`
- Redis хранит привязку `Telegram user_id -> JWT`
- Celery worker сам отправляет итоговый ответ в Telegram
- RabbitMQ и Redis реально участвуют в обработке, а не присутствуют формально

## Архитектурные принципы

1. `Auth Service` и `Bot Service` должны быть технически и логически независимыми.
2. `Auth Service` не должен содержать логики Telegram-бота.
3. `Bot Service` не должен содержать регистрации, логина, хранилища пользователей и прямого доступа к БД `Auth Service`.
4. Запросы к LLM не должны выполняться напрямую в Telegram-хэндлерах.
5. Все длительные LLM-запросы должны проходить через очередь задач.
6. После каждого изменения кода нужно прогонять Ruff.

## Фаза 1. Подготовка структуры проекта

### Задачи

1. Перестроить текущий минимальный каркас проекта в двухсервисную структуру:
   - `auth_service/`
   - `bot_service/`
   - при необходимости `docker/` или `infra/` для инфраструктурных файлов
2. Оставить корень проекта как организационный уровень:
   - общий `README.md`
   - общий файл плана
   - при необходимости корневые вспомогательные скрипты
3. Перестать использовать текущий [main.py](/Users/vt/Documents/!Dev/Python/MEPHI/llm_bot/main.py) как реальную точку входа приложения.
4. Подготовить для каждого сервиса собственные:
   - `pyproject.toml`
   - `.env` или `.env.example`
   - `pytest.ini`
   - структуру `app/`
5. Зафиксировать использование уже созданного `.venv` как среды по умолчанию для `uv`.

### Результат фазы

В репозитории появляется корректная двухсервисная структура, на которую уже можно безопасно накладывать код сервисов, тесты и инфраструктуру.

## Фаза 2. Реализация Auth Service

### Цель

Собрать отдельный FastAPI-сервис, который отвечает только за:

- регистрацию пользователя
- логин пользователя
- выпуск JWT
- получение профиля по JWT

### Рекомендуемая последовательность реализации

1. `auth_service/app/core/config.py`
   - описать `settings` через `pydantic-settings`
   - добавить `APP_NAME`, `ENV`, `JWT_SECRET`, `JWT_ALG`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `SQLITE_PATH` или `DATABASE_URL`
2. `auth_service/app/db/base.py`
   - объявить единый `DeclarativeBase`
3. `auth_service/app/db/session.py`
   - настроить `create_async_engine`
   - создать `async_sessionmaker`
4. `auth_service/app/db/models.py`
   - реализовать модель `User`
   - поля: `id`, `email`, `password_hash`, `role`, `created_at`
   - добавить уникальность по `email`
5. `auth_service/app/schemas/auth.py`
   - `RegisterRequest`
   - `TokenResponse`
6. `auth_service/app/schemas/user.py`
   - `UserPublic` без `password_hash`
7. `auth_service/app/repositories/users.py`
   - `get_by_id`
   - `get_by_email`
   - `create`
8. `auth_service/app/core/security.py`
   - `hash_password()`
   - `verify_password()`
   - `create_access_token()`
   - `decode_token()`
   - токен должен содержать `sub`, `role`, `iat`, `exp`
9. `auth_service/app/core/exceptions.py`
   - `BaseHTTPException`
   - `UserAlreadyExistsError`
   - `InvalidCredentialsError`
   - `InvalidTokenError`
   - `TokenExpiredError`
   - `UserNotFoundError`
   - `PermissionDeniedError`
10. `auth_service/app/usecases/auth.py`
    - `register()`
    - `login()`
    - `me()`
11. `auth_service/app/api/deps.py`
    - `get_db()`
    - фабрики репозиториев и usecase
    - `get_current_user_id()`
    - `get_current_user()`
12. `auth_service/app/api/routes_auth.py`
    - `POST /auth/register`
    - `POST /auth/login`
    - `GET /auth/me`
13. `auth_service/app/api/router.py`
    - собрать роутеры
14. `auth_service/app/main.py`
    - собрать FastAPI-приложение
    - подключить роутеры
    - добавить `/health`

### Требования к реализации

- никакого SQL в роутерах
- никакой генерации JWT в роутерах
- никакой бизнес-логики в моделях и схемах
- пароль хранится только в виде хеша
- `Bot Service` не должен зависеть от БД этого сервиса

### Результат фазы

Готов отдельный Auth Service с рабочими endpoint-ами регистрации, логина и получения профиля по JWT.

## Фаза 3. Тестирование Auth Service

### Unit-тесты

Проверить:

1. что хеш пароля не равен исходному паролю
2. что правильный пароль проходит `verify_password()`
3. что неправильный пароль не проходит `verify_password()`
4. что `create_access_token()` создает токен с `sub`, `role`, `iat`, `exp`
5. что `decode_token()` корректно декодирует валидный токен
6. что невалидный или истекший токен корректно обрабатывается

### Integration-тесты

Проверить через HTTP:

1. `POST /auth/register`
2. `POST /auth/login` через `OAuth2PasswordRequestForm`
3. `GET /auth/me` с `Authorization: Bearer <token>`
4. повторную регистрацию с тем же email -> `409`
5. логин с неправильным паролем -> `401`
6. запрос `/auth/me` без токена -> `401`
7. запрос `/auth/me` с неправильным токеном -> `401`

### Технический подход

- использовать `httpx` и `ASGITransport`
- подменять БД на in-memory SQLite
- не обращаться к внешним сервисам

### Результат фазы

Auth Service подтвержден тестами как на уровне чистой логики, так и на уровне HTTP-сценариев.

## Фаза 4. Реализация Bot Service

### Цель

Собрать отдельный сервис Telegram-бота, который:

- принимает JWT от пользователя
- хранит токен в Redis
- валидирует токен локально
- ставит LLM-задачи в очередь RabbitMQ через Celery
- получает результат работы LLM через worker и отправляет ответ пользователю

### Рекомендуемая последовательность реализации

1. `bot_service/app/core/config.py`
   - `BOT_TOKEN`
   - `JWT_SECRET`
   - `JWT_ALG`
   - `REDIS_URL`
   - `RABBITMQ_URL`
   - настройки OpenRouter
2. `bot_service/app/core/jwt.py`
   - `decode_and_validate(token: str) -> dict`
   - проверка подписи
   - проверка `exp`
   - проверка наличия `sub`
3. `bot_service/app/infra/redis.py`
   - единая точка получения Redis-клиента
4. `bot_service/app/services/openrouter_client.py`
   - клиент на `httpx`
   - формирование payload
   - заголовки
   - обработка сетевых ошибок
   - обработка неуспешных HTTP-ответов
5. `bot_service/app/infra/celery_app.py`
   - создать `celery_app`
   - задать broker и backend
   - зарегистрировать tasks
6. `bot_service/app/tasks/llm_tasks.py`
   - задача `llm_request`
   - вызов OpenRouter
   - отправка ответа пользователю в Telegram
7. `bot_service/app/bot/dispatcher.py`
   - собрать `Bot` и `Dispatcher`
   - зарегистрировать хэндлеры
8. `bot_service/app/bot/handlers.py`
   - реализовать `/token <jwt>`
   - реализовать обработку обычного текста
   - при валидном токене вызывать `llm_request.delay(...)`
   - при отсутствии или невалидности токена возвращать отказ и инструкцию авторизоваться
9. `bot_service/app/main.py`
   - при необходимости сделать FastAPI-приложение с `/health`

### Ключевое проектное решение

Основной путь: Celery worker сам отправляет ответ в Telegram.

Причины:

1. это проще, чем сохранять результат в Redis и строить отдельный цикл доставки
2. это полностью соответствует ТЗ
3. это сохраняет асинхронность и отзывчивость бота

### Требования к реализации

- токен не создается в `Bot Service`
- бот не обращается к базе `Auth Service`
- запрос к LLM не уходит напрямую из handler
- Redis и RabbitMQ должны участвовать в реальном runtime-сценарии

### Результат фазы

Готов `Bot Service`, который принимает токен, проверяет его и асинхронно обрабатывает пользовательские запросы через очередь.

## Фаза 5. Тестирование Bot Service

### Unit-тесты

Проверить:

1. успешную валидацию корректного JWT
2. отказ на мусорной строке вместо токена
3. отказ на истекшем токене

### Mock-тесты обработчиков

Проверить:

1. команда `/token <jwt>` сохраняет токен в Redis
2. если токена нет, обычное сообщение не вызывает Celery и пользователь получает отказ
3. если токен есть и валиден, вызывается `llm_request.delay(...)`
4. в очередь передаются корректные аргументы

### Технический подход

- использовать `fakeredis`
- патчить `get_redis` именно в `app.bot.handlers`
- мокать `llm_request.delay` через `pytest-mock`
- не подключаться к реальному Redis и RabbitMQ в unit/mock тестах

### Integration-тесты

Проверить клиента OpenRouter:

1. замокать `POST https://openrouter.ai/api/v1/chat/completions` через `respx`
2. вернуть тестовый JSON
3. убедиться, что клиент правильно извлек текст ответа
4. подтвердить, что HTTP-вызов действительно был сделан

### Результат фазы

Bot Service подтвержден тестами JWT-логики, handler-логики и интеграции с OpenRouter-клиентом без внешнего интернета.

## Фаза 6. Инфраструктура RabbitMQ и Redis

### Цель

Развернуть инфраструктуру в Docker на удаленном сервере `192.168.1.98` и подключить локальный проект к этим удаленным сервисам.

### Задачи

1. Подготовить Docker-конфигурацию для:
   - RabbitMQ
   - Redis
2. Развернуть контейнеры именно на удаленном хосте `192.168.1.98`
3. Проверить доступность:
   - RabbitMQ broker port
   - RabbitMQ management UI
   - Redis port
4. Настроить переменные окружения сервисов так, чтобы они подключались по IP `192.168.1.98`, а не к локальному `localhost`
5. Проверить, что:
   - Celery публикует задачи в RabbitMQ
   - worker забирает задачи
   - Redis хранит токены

### Важные замечания

- инфраструктура должна быть реальной, а не формальной
- наличие Docker-сервисов без участия в обработке не засчитывается
- доступность по сети и корректные URL нужно считать частью acceptance criteria

### Результат фазы

RabbitMQ и Redis развернуты на удаленном сервере и реально используются приложением.

## Фаза 7. Организация запуска

### Нужно обеспечить запуск минимум следующих компонентов

1. `Auth Service` API
2. `Bot Service` bot process или bot-side runtime
3. `Celery worker`
4. Docker-инфраструктура с `RabbitMQ` и `Redis`

### Что должно быть описано

1. команды установки зависимостей через `uv`
2. команды запуска каждого сервиса
3. команды запуска тестов
4. команды Ruff-проверки
5. порядок ручной демонстрации сценария

### Результат фазы

Проект можно поднять и проверить по понятной инструкции без ручного восстановления контекста.

## Фаза 8. README и подтверждающие материалы

### README должен содержать

1. описание архитектуры
2. назначение каждого сервиса
3. используемый стек
4. переменные окружения
5. инструкции по запуску
6. инструкции по тестированию
7. пользовательский сценарий
8. пояснение, как задействованы RabbitMQ и Redis

### Обязательные подтверждения для сдачи

1. скриншоты Swagger Auth Service:
   - регистрация
   - логин
   - `/auth/me`
2. скриншоты работы Telegram-бота
3. скриншоты интерфейса RabbitMQ с очередями и consumers
4. скриншоты или логи успешного прохождения тестов

### Результат фазы

Проект не только реализован, но и подготовлен к приемке по критериям ТЗ.

## Карта ожидаемых файлов

### Auth Service

- `auth_service/app/main.py`
- `auth_service/app/core/config.py`
- `auth_service/app/core/security.py`
- `auth_service/app/core/exceptions.py`
- `auth_service/app/db/base.py`
- `auth_service/app/db/session.py`
- `auth_service/app/db/models.py`
- `auth_service/app/schemas/auth.py`
- `auth_service/app/schemas/user.py`
- `auth_service/app/repositories/users.py`
- `auth_service/app/usecases/auth.py`
- `auth_service/app/api/deps.py`
- `auth_service/app/api/routes_auth.py`
- `auth_service/app/api/router.py`
- `auth_service/tests/`
- `auth_service/pytest.ini`
- `auth_service/pyproject.toml`

### Bot Service

- `bot_service/app/main.py`
- `bot_service/app/core/config.py`
- `bot_service/app/core/jwt.py`
- `bot_service/app/infra/redis.py`
- `bot_service/app/infra/celery_app.py`
- `bot_service/app/tasks/llm_tasks.py`
- `bot_service/app/services/openrouter_client.py`
- `bot_service/app/bot/dispatcher.py`
- `bot_service/app/bot/handlers.py`
- `bot_service/tests/conftest.py`
- `bot_service/tests/`
- `bot_service/pytest.ini`
- `bot_service/pyproject.toml`

### Общие файлы

- `README.md`
- `IMPLEMENTATION_PLAN.md`
- при необходимости `docker/` или `infra/`

## Проверки готовности

### Проверки Auth Service

1. регистрация работает
2. логин работает
3. JWT создается корректно
4. `/auth/me` работает только с валидным JWT
5. негативные кейсы возвращают корректные ошибки

### Проверки Bot Service

1. бот принимает `/token <jwt>`
2. токен сохраняется в Redis
3. без токена доступ блокируется
4. с валидным токеном задача ставится в очередь
5. worker вызывает OpenRouter
6. пользователь получает итоговый ответ

### Проверки инфраструктуры

1. RabbitMQ показывает очереди и consumers
2. Redis реально используется приложением
3. Celery worker видит задачу `llm_request`
4. бот остается отзывчивым во время выполнения LLM-задач

### Проверки документации и сдачи

1. README заполнен
2. тесты проходят локально без внешних сервисов для unit/mock сценариев
3. собраны скриншоты по требованиям
4. email при демонстрации оформлен в виде `surname@email.com`

## Исключения из scope

В этот план не включаются как обязательные:

- refresh tokens
- сложная RBAC-модель сверх наличия `role` в JWT
- RS256 и управление ключами
- CI/CD
- Kubernetes
- production-observability stack

Это можно добавить позже, но для текущего ТЗ не требуется.

## Итоговый порядок выполнения

1. Разложить проект на `auth_service` и `bot_service`
2. Настроить `uv`, зависимости и базовые конфиги
3. Реализовать `Auth Service`
4. Покрыть `Auth Service` тестами
5. Реализовать `Bot Service`
6. Покрыть `Bot Service` тестами
7. Развернуть RabbitMQ и Redis на `192.168.1.98`
8. Проверить полный пользовательский сценарий
9. Подготовить README и подтверждающие материалы
10. Финально перепроверить Ruff, тесты и соответствие ТЗ
