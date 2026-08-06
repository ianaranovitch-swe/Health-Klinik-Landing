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
- `DATABASE_URL` = reference на Postgres
- `CORS_ORIGINS` = `https://mrboka.com,https://www.mrboka.com`
