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

## Деплой на Railway (отдельный сервис)

### 1. BotFather
1. [@BotFather](https://t.me/BotFather) → `/newbot`
2. Сохрани **token** и **username** (например `mr_bokning_bot`)

### 2. Новый сервис
1. Railway → тот же проект → **New** → **GitHub Repo** (тот же репозиторий)
2. Имя: например `telegram-bot`
3. **Settings**:
   - **Root Directory** = `backend`
   - **Dockerfile path** = `Dockerfile.bot`  
     (или Builder Dockerfile и файл `Dockerfile.bot`)
   - **Custom Start Command** (если нужно): `python -m bot.main`
4. Публичный домен **не нужен** (long polling)

### 3. Variables у `telegram-bot`
- `BOT_TOKEN` = токен
- `BOT_USERNAME` = username без `@`
- `DATABASE_URL` = Variable Reference → Postgres → `DATABASE_URL`

### 4. Variables у API (`industrious-exploration`)
- `BOT_USERNAME` = тот же username  
  (иначе кнопка ведёт на `t.me/BOT_USERNAME`)

### 5. Redeploy API после смены `BOT_USERNAME`

### 6. Проверка
1. Логи бота: `Бот запущен: @...`
2. Тестовая бронь на сайте → **Bekräfta i Telegram**
3. Бот отвечает «Din bokning är bekräftad»
4. Терапевт (с реальным telegram_id) получает уведомление

## Важно про telegram_id терапевтов

Заглушка `SEED_IWONA_TELEGRAM_ID=2000000001` **не** получит сообщения  
(бот явно пропускает известные placeholder-id).  
Нужен настоящий ID из [@userinfobot](https://t.me/userinfobot) → seed снова.
