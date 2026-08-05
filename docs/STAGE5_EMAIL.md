# Этап 5 — Email через Resend

## Что сделано

- Зависимость `resend` в `backend/requirements.txt`
- `backend/app/services/email_service.py`:
  - `send_email(to, subject, html)` → `resend.Emails.send()`
  - ключ из `os.environ["RESEND_API_KEY"]`
  - отправитель: `info@mrboka.com` (константа `SENDER_EMAIL`)
  - HTML-шаблоны клиенту и терапевту
- Вызов из `POST /api/bookings` после `commit` (через `notify_booking_created`)
- Ошибка Resend **не отменяет** создание записи

## Что сделать вручную в Resend

1. Зарегистрируйся на [resend.com](https://resend.com).
2. **Domains** → добавь `mrboka.com` (DNS-записи по инструкции Resend, часто через Cloudflare).
3. Дождись статуса **Verified**.
4. **API Keys** → создай ключ `re_...`.
5. В Railway (сервис API) и/или локальном `.env`:
   ```env
   RESEND_API_KEY=re_xxxxxxxx
   ```
6. Проверь: создай тестовую запись через Swagger `POST /api/bookings` — письма должны уйти клиенту и на email терапевта из БД.

## Письма

| Кому | Содержание |
|---|---|
| Клиент | терапевт, услуга, дата/время + кнопка **Bekräfta i Telegram** |
| Терапевт | имя, телефон, email клиента + детали записи |

## Важно

Пока API только локально / на Railway backend — письма уходят при вызове `POST /api/bookings`.  
Форма на лендинге (этап 3) ещё не подключена — тестируй через `/docs`.
