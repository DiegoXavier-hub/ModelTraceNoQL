from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.core.config import settings
from app.core.utils import utcnow


def smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def outbox_path() -> Path:
    configured = Path(settings.local_store_path)
    return configured.parent / "email_outbox.jsonl"


def send_transactional_email(to_email: str, subject: str, text: str, html: str | None = None) -> dict:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    if smtp_configured():
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        return {"status": "sent", "transport": "smtp"}

    path = outbox_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": utcnow(),
        "transport": "local_outbox",
        "to": to_email,
        "from": settings.smtp_from,
        "subject": subject,
        "text": text,
        "html": html,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return {"status": "queued", "transport": "local_outbox", "outbox_path": str(path)}
