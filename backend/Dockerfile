# API-сервис бронирования (FastAPI) для Railway
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway задаёт PORT; нужен shell, иначе "$PORT" уйдёт в uvicorn как текст
ENV PORT=8000
EXPOSE 8000

# Сначала миграции (создают таблицы), потом API
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
