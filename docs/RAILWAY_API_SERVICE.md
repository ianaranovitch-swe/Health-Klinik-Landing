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
| Start Command (если пусто) | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

Variables:
- `DATABASE_URL` = reference на Postgres
- `CORS_ORIGINS` = `https://mrboka.com,https://www.mrboka.com`
