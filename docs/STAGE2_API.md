# Этап 2 — FastAPI

## Endpoints

| Метод | Путь | Описание |
|---|---|---|
| GET | `/health` | живость |
| GET | `/api/therapists` | активные терапевты |
| GET | `/api/services` | услуги |
| GET | `/api/availability?therapist_id=&date=YYYY-MM-DD` | пн–чт 11–18, пт 11–17 / 30 мин; сб–вс пусто |
| POST | `/api/bookings` | создать запись + deep-link |
| GET | `/api/bookings/therapist/{id}` | записи терапевта |

Документация Swagger: `http://127.0.0.1:8000/docs`

## Запуск локально

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# миграции (включая email терапевта)
alembic upgrade head

# демо-данные
$env:SEED_THERAPIST_TELEGRAM_ID="ТВОЙ_TELEGRAM_ID"
$env:SEED_THERAPIST_EMAIL="mail@mr-ab.se"
python -m scripts.seed_demo

# API
uvicorn app.main:app --reload --port 8000
```

## Пример POST /api/bookings

```json
{
  "name": "Erik Andersson",
  "phone": "0701234567",
  "email": "erik@example.com",
  "therapist_id": 1,
  "service_id": 1,
  "date": "2026-08-10",
  "time": "10:30:00"
}
```

Ответ содержит `telegram_deep_link` вида  
`https://t.me/BOTNAME?start=confirm_<uuid>`.

## Email

Полная интеграция Resend — см. [STAGE5_EMAIL.md](STAGE5_EMAIL.md).  
После `commit` вызывается `notify_booking_created()`; без `RESEND_API_KEY` письма только логируются.

## Переменные

См. `.env.example`: `DATABASE_URL`, `BOT_USERNAME`, `CORS_ORIGINS`, `RESEND_API_KEY`, `EMAIL_FROM`.
