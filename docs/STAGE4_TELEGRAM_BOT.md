# Этап 4 — Telegram-бот (aiogram, long polling)

## Что делает бот

1. Клиент бронирует на mrboka.com.
2. В письме / на сайте кнопка **Bekräfta i Telegram** ведёт на  
   `https://t.me/<BOT_USERNAME>?start=confirm_<token>`
3. Бот ставит бронь в статус `confirmed` и отвечает клиенту.
4. Терапевту уходит сообщение в Telegram (если у него реальный `telegram_id` в БД).

## Локальный запуск

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# В .env: BOT_TOKEN, DATABASE_URL, BOT_USERNAME
python -m bot.main
```

## Переменные

| Переменная | Где | Описание |
|---|---|---|
| `BOT_TOKEN` | сервис бота | токен от @BotFather |
| `BOT_USERNAME` | сервис бота **и** API | username без `@` (для deep-link на сайте) |
| `DATABASE_URL` | сервис бота | `${{Postgres.DATABASE_URL}}` |

`CORS_ORIGINS` боту **не нужен** (это только для FastAPI). Можно удалить с сервиса бота или оставить — на бота не влияет. Localhost в CORS на API можно оставить для локальной разработки.

## Деплой на Railway (отдельный сервис)

### Важно: не запускай API-команды на боте

Если в логах бота видно `Uvicorn running` / `alembic` — сервис читает `railway.toml` (API).  
Для бота нужен файл **`railway.bot.toml`**.

### 1. BotFather
1. [@BotFather](https://t.me/BotFather) → `/newbot`
2. Сохрани **token** и **username** (например `mr_bokning_bot`)

### 2. Настройки сервиса `telegram-bot`
1. **Root Directory** = `backend`
2. **Config-as-code / Config File Path** = `/backend/railway.bot.toml`  
   (абсолютный путь от корня репо; **не** `railway.toml`!)
3. После сохранения — **Redeploy**
4. В логах должно быть: `Бот запущен: @...`  
   **Не** должно быть: `Uvicorn running`

Если поля Config File нет в UI, можно так:
- Variable `RAILWAY_DOCKERFILE_PATH` = `Dockerfile.bot`
- и в Deploy Start Command = `python -m bot.main`  
  (Start Command сейчас серый, потому что его задаёт API-`railway.toml` — после смены Config File Path поле разблокируется / берётся из `railway.bot.toml`.)

### 3. Variables у `telegram-bot`
- `BOT_TOKEN` = токен
- `BOT_USERNAME` = username без `@`
- `DATABASE_URL` = Variable Reference → Postgres → `DATABASE_URL`
- `CORS_ORIGINS` — не обязателен, можно удалить

### 4. Variables у API (`industrious-exploration`)
- `BOT_USERNAME` = тот же username  
  (иначе кнопка ведёт на `t.me/BOT_USERNAME`)

### 5. Redeploy API после смены `BOT_USERNAME`

### 6. Проверка
1. Логи бота: `Бот запущен: @...`
2. Тестовая бронь на сайте → **Bekräfta i Telegram**
3. Бот отвечает «Din bokning är bekräftad»
4. Терапевт (с реальным telegram_id) получает уведомление

## Если бот молчит (открывается, но не отвечает)

1. Есть ли отдельный сервис бота (не только API)? Статус **Online**.
2. **Deploy Logs** бота: строка `Бот запущен: @...`  
   - Если uvicorn / Caddy — всё ещё используется API-`railway.toml`. Поставь Config File = `railway.bot.toml`.
3. Variables у **бота**:
   - `BOT_TOKEN`  
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`  
   - `BOT_USERNAME`
4. У **API** тот же `BOT_USERNAME`.
5. На телефоне deep-link часто показывает только `/start`, но внутри есть `confirm_...`.

## Важно про telegram_id терапевтов

Заглушка `SEED_IWONA_TELEGRAM_ID=2000000001` **не** получит сообщения  
(бот явно пропускает известные placeholder-id).  
Нужен настоящий ID из [@userinfobot](https://t.me/userinfobot) → seed снова.
