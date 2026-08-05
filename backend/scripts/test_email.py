"""
Тест отправки email через Resend.

Использует тот же app.services.email_service.send_email(), что и продакшен
(POST /api/bookings). From: Människans Resurser <info@mrboka.com>.

Запуск (из папки backend):
  python -m scripts.test_email your@email.com
  # или: python scripts/test_email.py your@email.com

Нужен RESEND_API_KEY в .env (корень проекта или backend/) и верифицированный
домен mrboka.com в Resend.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# При запуске как файл (python scripts/test_email.py) корень backend
# не всегда в sys.path — добавляем до импорта app.*.
# При python -m scripts.test_email путь уже корректен.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import resend
from dotenv import load_dotenv

from app.services.email_service import SENDER_EMAIL, SENDER_NAME, send_email


def _load_env() -> None:
    """Загрузить .env до чтения RESEND_API_KEY (не при импорте модуля)."""
    load_dotenv(_BACKEND_ROOT.parent / ".env")
    load_dotenv(_BACKEND_ROOT / ".env")


def main() -> None:
    _load_env()

    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Ошибка: укажи email получателя.")
        print("Использование: python -m scripts.test_email your@email.com")
        sys.exit(1)

    to_email = sys.argv[1].strip()

    if not os.environ.get("RESEND_API_KEY"):
        print("❌ Failed to send email")
        print("Ошибка: переменная RESEND_API_KEY не задана (проверь .env).")
        sys.exit(1)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = "Testmail från mrboka.com"
    html = f"""
    <h2>Testmail från mrboka.com</h2>
    <p>Resend-integrationen fungerar.</p>
    <p>Skickat: <strong>{now}</strong></p>
    <p>From: {SENDER_NAME} &lt;{SENDER_EMAIL}&gt;</p>
    <p>Detta mail skickades via <code>app.services.email_service.send_email()</code>.</p>
    """

    # Перехватываем ответ/ошибку Resend, не меняя email_service.py
    captured_response: dict[str, Any] = {}
    captured_errors: list[str] = []
    original_send = resend.Emails.send

    def _send_and_capture(params: Any) -> Any:
        try:
            result = original_send(params)
            captured_response["result"] = result
            return result
        except Exception as exc:
            captured_errors.append(repr(exc))
            raise

    class _LogCapture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.exc_info:
                captured_errors.append(
                    logging.Formatter().formatException(record.exc_info)
                )
            elif record.levelno >= logging.ERROR:
                captured_errors.append(record.getMessage())

    handler = _LogCapture()
    email_logger = logging.getLogger("app.services.email_service")
    email_logger.addHandler(handler)
    email_logger.setLevel(logging.DEBUG)

    resend.Emails.send = _send_and_capture  # type: ignore[method-assign]
    try:
        print(f"Отправляю тест на {to_email} от {SENDER_NAME} <{SENDER_EMAIL}> ...")
        ok = send_email(to=to_email, subject=subject, html=html)
    finally:
        resend.Emails.send = original_send  # type: ignore[method-assign]
        email_logger.removeHandler(handler)

    if ok:
        result = captured_response.get("result")
        email_id = getattr(result, "id", None)
        if email_id is None and isinstance(result, dict):
            email_id = result.get("id")
        if email_id:
            print(f"email id: {email_id}")
        print("✅ Email sent successfully")
        sys.exit(0)

    print("❌ Failed to send email")
    if captured_errors:
        print("Полный текст ошибки:")
        print("\n".join(captured_errors))
    else:
        print("Ошибка: отправка не удалась (проверь RESEND_API_KEY и домен в Resend).")
    sys.exit(1)


if __name__ == "__main__":
    main()
