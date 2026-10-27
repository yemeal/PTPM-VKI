# Сервис сбора и хранения комментариев с форумов

## быстрый запуск

### через Docker

```bash
docker compose up --build
```

сервис автоматически развернется на [http://localhost:8000](http://localhost:8000).

### локально через `uv`

```bash
# синхронизация виртуального окружения
uv sync

# запуск dev-сервера
uv run uvicorn app.entrypoints.http.main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
```

### локально через `pip`

если `uv` не установлен, запуск возможен через стандартный `pip`:

```bash
# создание и активация виртуального окружения
python -m venv .venv

# для Linux / macOS:
source .venv/bin/activate
# для Windows (PowerShell):
.venv\Scripts\Activate.ps1

# установка зафиксированных зависимостей
pip install -r requirements.txt

# запуск dev-сервера
uvicorn app.entrypoints.http.main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
```

---

## архитектура и ключевые фичи

Проект спроектирован по канонам DDD и Hexagonal Architecture с разделением на независимые слои:

- **Rich Domain Model** — сущность `Comment`, Value Objects `Username` и `MessageText`. Все бизнес-инварианты
  инкапсулированы внутри домена: автонормализация Unicode (NFC), очистка пробелов, валидация длины, таймзоны UTC.
- **OCC (Optimistic Concurrency Control)** — защита от состояния гонки при конкурентном обновлении через
  версионирование, исключающая потерю правок.
- **CQRS** — разделение сценариев на Commands (`AddComment`, `UpdateComment`, `DeleteComment`, `ParsePage`) и Queries (
  `GetComment`, `ListComments`).
- **Мощный парсер форумов** — извлечение комментариев из HTML (4PDA, LOR, Lobsters) и RSS/Atom лент с защитой от циклов,
  обходом блокировок и автодискавери фидов.
- **Dependency Injection** — IoC-контейнер с контролем жизненного цикла зависимостей (`REQUEST`, `APP`).
- **Стек:** Python 3.14, FastAPI, SQLAlchemy 2.0 (async), aiosqlite, Dishka, BeautifulSoup4 + lxml, Pydantic v2.

---

## тестирование

тестовый набор покрывает **94.7%** кодовой базы и насчитывает **159 тестов**:

```bash
# все тесты с кратким выводом
uv run pytest -q

# тесты с отчетом о покрытии (>80% порог)
uv run pytest --cov=src/app

# только быстрые изолированные unit-тесты
uv run pytest -m unit

# только сквозные интеграционные тесты
uv run pytest -m integration
```

подробное описание каждого теста и структура фикстур описаны в [`tests/README.md`](tests/README.md).

---

## контроль качества и Git-хуки

в проекте настроен пайплайн проверок качества:

```bash
# линтинг и проверка форматирования
uv run ruff check --force-exclude
uv run ruff format --check --force-exclude

# статическая проверка типов (strict mode)
uv run ty check --error-on-warning

# полный прогон всех pre-commit проверок
uv run prek run --all-files
```

---

## основные эндпоинты

| Метод    | Эндпоинт                 | Описание                                                         |
|----------|--------------------------|------------------------------------------------------------------|
| `GET`    | `/docs`                  | swagger UI документация                                          |
| `GET`    | `/health/live`           | liveness-проба                                                   |
| `GET`    | `/health/ready`          | readiness-проба                                                  |
| `POST`   | `/api/v1/comments`       | создание комментария вручную                                     |
| `GET`    | `/api/v1/comments/{id}`  | получение комментария по UUID                                    |
| `PATCH`  | `/api/v1/comments/{id}`  | частичное обновление текста с контролем версии                   |
| `PUT`    | `/api/v1/comments/{id}`  | полное обновление текста с контролем версии                      |
| `DELETE` | `/api/v1/comments/{id}`  | удаление комментария                                             |
| `GET`    | `/api/v1/comments`       | выборка комментариев (фильтры `author`, `source_url`, пагинация) |
| `POST`   | `/api/v1/comments/parse` | _идемпотентный_ парсинг ветки форума по URL                      |
