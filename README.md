# Health Klinik Landing — Människans Resurser

Статический лендинг для Monicor & Alfa. Тексты взяты из `fardig-landningssida-webbcopy.md`.

## Быстрый старт (локально)

Открыть файл в браузере:

```bash
# Windows (PowerShell)
start index.html
```

Или через Docker (как на Railway):

```bash
docker build -t health-klinik-landing .
docker run --rm -p 8080:8080 -e PORT=8080 health-klinik-landing
```

Сайт: [http://localhost:8080](http://localhost:8080)  
Healthcheck: [http://localhost:8080/health](http://localhost:8080/health)

## Переменные окружения

| Переменная | Обязательно | Пример | Описание |
|---|---|---|---|
| `PORT` | да (на Railway задаётся сама) | `8080` | Порт HTTP-сервера (пока Caddy; позже FastAPI) |
| `DATABASE_URL` | да (этап 1) | `postgresql://...` | PostgreSQL на Railway |

Файл-пример: `.env.example`.

## Бронирование (в разработке)

| Этап | Статус | Документация |
|---|---|---|
| 1. База данных | готово | [docs/STAGE1_DATABASE.md](docs/STAGE1_DATABASE.md) |
| 2. FastAPI | готово | [docs/STAGE2_API.md](docs/STAGE2_API.md) |
| 3. Форма на лендинге | готово | [docs/STAGE3_BOOKING_FORM.md](docs/STAGE3_BOOKING_FORM.md) |
| 4. Telegram-бот | готово (деплой) | [docs/STAGE4_TELEGRAM_BOT.md](docs/STAGE4_TELEGRAM_BOT.md) |
| 5. Email (Resend) | готово | [docs/STAGE5_EMAIL.md](docs/STAGE5_EMAIL.md) |
| 6. Деплой Railway (API+бот) | API готов; бот — см. STAGE4 | [docs/STAGE4_TELEGRAM_BOT.md](docs/STAGE4_TELEGRAM_BOT.md) |

## Структура

```
index.html          # страница
style.css           # стили
Dockerfile          # образ для Railway
Caddyfile           # веб-сервер
railway.toml        # настройки деплоя
docs/RUNBOOK.md     # деплой, откат, диагностика
```

## Деплой на Railway (временный URL)

1. Запушить репозиторий в GitHub.
2. На [railway.app](https://railway.app): **New Project → Deploy from GitHub repo**.
3. Выбрать этот репозиторий.
4. Дождаться билда (Dockerfile).
5. **Settings → Networking → Generate Domain**.
6. Открыть `https://<имя>.up.railway.app`.

Подробнее: [docs/RUNBOOK.md](docs/RUNBOOK.md).

## Контакты на сайте

- Telefon: `08-33 49 08`
- E-post: `mail@mr-ab.se`
- Bokning: кнопки ведут на `#boka` / `#kontakt` (онлайн-бронирование подключим позже)

## Что ещё не финально

- Примеры отзывов — заменить на реальные.
- Система бронирования + БД на Railway — отдельный этап.
- Свой домен через DNS (Cloudflare → Railway) — когда домен готов.
