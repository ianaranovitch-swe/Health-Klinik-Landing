# Этап 1 — База данных

## Что сделано

- SQLAlchemy 2.x модели: `therapists`, `clients`, `services`, `bookings`
- Alembic-миграция `20260731_0001`
- Сырой SQL: `sql/001_schema.sql`
- Подключение через `DATABASE_URL` (`backend/app/config.py`, `backend/app/db.py`)

## Как это работает (просто)

1. Railway даёт адрес базы — строку `DATABASE_URL`.
2. Python читает её и открывает «трубу» к PostgreSQL.
3. Модели — это описание таблиц на языке Python.
4. Alembic применяет это описание к реальной базе (создаёт таблицы).

## Локальная проверка

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Скопируй .env.example → .env в корне проекта и вставь DATABASE_URL из Railway
copy ..\.env.example ..\.env

# Проверка соединения
python -m scripts.check_db

# Применить миграции
alembic upgrade head
```

## Вручную в Railway

1. Создай проект (или открой существующий).
2. **New → Database → PostgreSQL**.
3. Открой Postgres → **Variables** → скопируй `DATABASE_URL`.
4. Положи его в локальный `.env` (не коммить!).
5. Выполни `alembic upgrade head` из папки `backend`.

## Сиды (вручную после миграции)

```sql
INSERT INTO therapists (telegram_id, name, email, specialization, active)
VALUES (ТВОЙ_TELEGRAM_ID, 'Anna Svensson', 'mail@mr-ab.se', 'Monicor & Alfa', TRUE);

INSERT INTO services (name, duration_minutes, price) VALUES
('Monicor-session', 90, 1500.00),
('Monicor + Alfa', 120, 2000.00);
```

Или удобнее: `python -m scripts.seed_demo` (см. этап 2).

Миграция `20260731_0002` добавляет колонку `therapists.email`.

`telegram_id` узнаёшь у [@userinfobot](https://t.me/userinfobot) в Telegram.
