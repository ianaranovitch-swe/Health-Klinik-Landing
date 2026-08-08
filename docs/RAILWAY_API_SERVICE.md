# Railway: отдельный API-сервис (папка backend)

Лендинг использует корневой `railway.toml` + Caddy.  
API должен смотреть **только в папку `backend`**.

## Где Root Directory в новом UI

1. Открой сервис API (например `industrious-exploration`).
2. Вкладка **Settings**.
3. Вверху в поле **Filter Settings...** напиши: `root`
4. Или справа в меню кликни **Source** / **Build** и прокрути **вверх** — поле **Root Directory** часто над Builder.

Если везде написано *set in /railway.toml* — сначала задай Root Directory = `backend`, тогда подхватится `backend/railway.toml`, а не корневой.

## Что вписать

| Поле | Значение |
|---|---|
| Root Directory | `backend` |
| Start Command (если задаёшь вручную) | `sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'` |
| Или оставь пустым | возьмётся из `backend/railway.toml` / Dockerfile |

Variables:
- `DATABASE_URL` = reference на Postgres (`${{Postgres.DATABASE_URL}}`)
- `CORS_ORIGINS` = `https://mrboka.com,https://www.mrboka.com`
- `PUBLIC_API_BASE` = публичный URL этого API (тот же, что Generate Domain), например  
  `https://industrious-exploration-production-512f.up.railway.app`  
  Нужен для кнопки **Bekräfta via e-post** в письме клиенту.
- `BOT_USERNAME` = username бота без `@`

## Публичный URL (иначе браузер покажет «Not Found / train has not arrived»)

Внутренний healthcheck (`GET /health` в Deploy Logs → 200) ≠ доступ из интернета.  
Сервис по умолчанию **не публичный**.

1. Сервис API → **Settings** → **Networking** (или **Public Networking**).
2. Нажми **Generate Domain**.
3. Скопируй выданный URL (например `https://….up.railway.app`) — он может отличаться от старого имени.
4. Открой в браузере: `https://ТВОЙ-ДОМЕН/health` → должно быть `{"status":"ok"}` (или похожий JSON из FastAPI).

Если видишь страницу Railway «The train has not arrived…» — домена на этом сервисе ещё нет или он привязан к другому сервису.

## Рабочий API (пример)

База (без `/health`):

`https://industrious-exploration-production-512f.up.railway.app`

Проверки:
- `/health` → `{"status":"ok"}`
- `/api/therapists` → JSON-массив (после миграций + seed)
- `/api/services` → JSON-массив

При старте контейнера: `alembic upgrade head`, затем uvicorn.

Один раз заполнить демо-данные (Railway Shell / one-off на API-сервисе):

```bash
python -m scripts.seed_demo
```

Переменные (рекомендуется):
- `SEED_VIKTORIA_TELEGRAM_ID`, `SEED_VIKTORIA_EMAIL`, `SEED_VIKTORIA_NAME`
- `SEED_IWONA_TELEGRAM_ID`, `SEED_IWONA_EMAIL`, `SEED_IWONA_NAME`
- `SEED_BORIS_TELEGRAM_ID`, `SEED_JAN_TELEGRAM_ID` (+ имена) — staff бота
- `PUBLIC_API_BASE` — публичный URL API

Iwona → услуги Alfa + Monicor. Viktoria → Alfa + Monicor + EIS (и пакеты с EIS).

Лендинг: `data-api-base="auto"`; прод-URL API — константа `PROD_API_BASE` в `booking.js`.
