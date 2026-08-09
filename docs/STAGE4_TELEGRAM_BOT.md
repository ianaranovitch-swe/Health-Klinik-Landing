# Этап 4 — Telegram-бот (aiogram, long polling)

## Что делает бот

1. Клиент бронирует на mrboka.com.
2. В письме / на сайте кнопка **Bekräfta i Telegram** ведёт на  
   `https://t.me/<BOT_USERNAME>?start=confirm_<token>`
3. Бот ставит бронь в статус `confirmed` и отвечает клиенту.
4. Терапевту уходит сообщение в Telegram (если у него реальный `telegram_id` в БД).

### Staff-меню (актуальные брони)

Пользователи из таблицы `staff_members`:

| Кто | Что видит |
|---|---|
| Viktoria, Iwona (`therapist`) | **только свои** брони |
| Boris, Jan (`superuser`) | **все** брони, группы по behandlare |

1. `/start` → приветствие + **Visa aktuella bokningar** + **Radera bokning**
2. Список: сначала `confirmed` (✅), затем `pending` (⏳), ещё не прошедшие
3. Кнопки всегда: **Telegram** + **E-post**  
   (если у клиента нет Telegram — кнопка объясняет это во всплывающем окне)
4. **Radera bokning** → выбрать кнопкой → подтвердить → строка **удаляется из БД**  
   (therapist — только свои; superuser — любые актуальные)

### Автонапоминания (24 h и 2 h)

Фоновый цикл в процессе бота (раз в ~60 с, Europe/Stockholm):

- Брони `pending` и `confirmed` (в тексте статус явно)
- За **≤ 24 ч** (и ещё **> 2 ч**) → напоминание всем активным staff + клиенту (если есть `telegram_id`)
- За **≤ 2 ч** → второе напоминание
- Флаги `reminder_24h_sent_at` / `reminder_2h_sent_at` на `bookings` — без дублей
- `telegram_id` клиента сохраняется при **Bekräfta i Telegram**

Миграция: `20260809_0005` (деплой API с alembic).

### Подтверждение без Telegram (e-post)

В письме клиенту две кнопки:
- **Bekräfta i Telegram**
- **Bekräfta via e-post** → `GET {PUBLIC_API_BASE}/api/bookings/confirm/{token}`  
  (тот же токен, статус `confirmed` в БД + HTML-страница)

На API нужен `PUBLIC_API_BASE` (публичный URL сервиса API).

Сиды staff: `python -m scripts.seed_demo`.
Миграция `staff_members` — при деплое API.

## Локальный запуск

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# В .env: BOT_TOKEN, DATABASE_URL, BOT_USERNAME
python -m bot.main
```

Тесты staff-форматирования:

```powershell
cd backend
python -m pytest tests/test_staff_bookings.py -q
```

## Переменные

| Переменная | Где | Описание |
|---|---|---|
| `BOT_TOKEN` | сервис бота | токен от @BotFather |
| `BOT_USERNAME` | сервис бота **и** API | username без `@` (для deep-link на сайте) |
| `DATABASE_URL` | сервис бота | `${{Postgres.DATABASE_URL}}` |
| `SEED_BORIS_TELEGRAM_ID` | API (seed) | суперпользователь бота |
| `SEED_JAN_TELEGRAM_ID` | API (seed) | суперпользователь бота |
| `PUBLIC_API_BASE` | API | публичный URL API для e-post-подтверждения |

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
- `SEED_BORIS_TELEGRAM_ID` / `SEED_JAN_TELEGRAM_ID` (+ имена) для seed
- те же `SEED_VIKTORIA_*` / `SEED_IWONA_*`

### 5. После деплоя API
1. Redeploy API (миграция `staff_members`)
2. В API Console: `python -m scripts.seed_demo`
3. Redeploy бота

### 6. Проверка
1. Логи бота: `Бот запущен: @...`
2. Тестовая бронь на сайте → **Bekräfta i Telegram**
3. Бот отвечает «Din bokning är bekräftad»
4. Терапевт (с реальным telegram_id) получает уведомление
5. `/start` от Jan/Boris/Viktoria/Iwona → кнопка списка броней

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
