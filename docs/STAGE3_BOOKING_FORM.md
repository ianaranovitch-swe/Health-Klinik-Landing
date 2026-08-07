# Этап 3 — Форма бронирования на лендинге

## Что сделано

- Секция `#boka` заменена на форму: behandlare, tjänst, datum, tid, namn, telefon, e-post
- `booking-form.js` загружает данные из API и отправляет `POST /api/bookings`  
  (старый `booking.js` оставлен как копия; страница подключает `booking-form.js`)
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
3. В `index.html` по умолчанию: `data-api-base="auto"` (не меняй для локалки)  
   - на localhost → `http://127.0.0.1:8000`  
   - на mrboka.com / www → `PROD_API_BASE` в `booking.js` (отдельный Railway API)  
   - другой API-хост только при необходимости: явный `data-api-base="https://…"`
4. Порядок в форме: **сначала tjänst/diagnostik**, затем **behandlare** (только те, кто умеет услугу).  
   EIS → только Viktoria; Monicor/Alfa → Iwona и Viktoria. Если терапевт один — выбирается сам.
4. В `.env` backend:
   ```env
   CORS_ORIGINS=http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:8000,https://mrboka.com
   ```
5. Заполни форму → должна создаться запись и показаться Telegram-кнопка.

## Прод (mrboka.com)

После этапа 6:

1. Оставь `data-api-base="auto"` — на mrboka.com подставится `PROD_API_BASE` из `booking.js`.
2. Если сменится публичный URL API — обнови константу `PROD_API_BASE` в `booking.js` (не `index.html`).
3. Добавь `https://mrboka.com` в `CORS_ORIGINS` на API-сервисе.

## Зависимости

Нужны данные в БД (терапевт + услуги): `python -m scripts.seed_demo`.
