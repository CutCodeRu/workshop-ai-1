from __future__ import annotations

from html import escape

from app.schemas import LeadRecord


def render_owner_notification(lead: LeadRecord) -> str:
    """Render the owner-facing text for a new lead."""
    username = f"@{lead.telegram_username}" if lead.telegram_username else "не указан"
    return (
        "<b>Новая заявка на консультацию</b>\n\n"
        f"<b>ID:</b> {lead.id}\n"
        f"<b>Имя:</b> {escape(lead.customer_name)}\n"
        f"<b>Телефон:</b> {escape(lead.phone_raw)}\n"
        f"<b>Нормализованный:</b> {escape(lead.phone_normalized)}\n"
        f"<b>Username:</b> {escape(username)}\n"
        f"<b>Telegram user ID:</b> {lead.telegram_user_id or 'не указан'}\n"
        f"<b>Chat ID:</b> {lead.telegram_chat_id}\n"
        f"<b>Вопрос:</b>\n{escape(lead.question)}"
    )
