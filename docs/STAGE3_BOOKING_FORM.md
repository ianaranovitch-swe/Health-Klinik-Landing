# Этап 3 — Форма бронирования на лендинге

## Что сделано

- Секция `#boka` заменена на форму: behandlare, tjänst, datum, tid, namn, telefon, e-post
- `booking.js` загружает данные из API и отправляет `POST /api/bookings`
- После успеха — экран с кнопкой **Bekräfta i Telegram** (deep-link из ответа)
- Стили в `style.css` на существующих CSS-переменных

## Локальный тест

1. Запусти API:
   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```
2. Открой лендинг (Live Server / просто `index.html`).
3. В `index.html` по умолчанию: `data-api-base="auto"`  
   - на localhost форма ходит на `http://127.0.0.1:8000`  
   - на mrboka.com — на тот же origin (когда API отдаёт сайт)  
   - для отдельного API-хоста: `data-api-base="https://YOUR-API.up.railway.app"`
4. В `.env` backend:
   ```env
   CORS_ORIGINS=http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000,https://mrboka.com
   ```
5. Заполни форму → должна создаться запись и показаться Telegram-кнопка.

## Прод (mrboka.com)

Пока API не задеплоен, форма на проде не подключится к backend. После этапа 6:

1. Если FastAPI отдаёт и лендинг, и `/api` — оставь `data-api-base="auto"`.
2. Если API на другом URL — укажи его явно в `data-api-base`.
3. Добавь `https://mrboka.com` в `CORS_ORIGINS` на API-сервисе.

## Зависимости

Нужны данные в БД (терапевт + услуги): `python -m scripts.seed_demo`.
