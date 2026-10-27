# 1. сборка виртуального окружения через uv
FROM python:3.14-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# устанавливаем зависимости отдельным слоем для эффективного кэширования
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

# копируем исходный код приложения и завершаем синхронизацию
COPY src/ src/
RUN uv sync --frozen --no-dev

# 2. минимальный легковесный рантайм
FROM python:3.14-slim-bookworm AS runner

WORKDIR /app

# создаем непривилегированного пользователя для безопасного запуска
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app appuser

# копируем готовое виртуальное окружение и исходный код из билдера
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# создаем директорию для SQLite БД с правами записи для appuser
RUN mkdir -p /app/data && chown -R appuser:appgroup /app

# настройка переменных окружения рантайма
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL="sqlite+aiosqlite:////app/data/comments.db" \
    HOST="0.0.0.0" \
    PORT=8000

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')" || exit 1

CMD ["uvicorn", "app.entrypoints.http.main:app", "--host", "0.0.0.0", "--port", "8000"]
