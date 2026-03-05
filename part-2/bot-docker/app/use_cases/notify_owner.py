from __future__ import annotations

from aiogram import Bot

from app.bot.texts.owner_notification import render_owner_notification
from app.config import Settings
from app.db.repositories import mark_lead_notified
from app.schemas import LeadRecord


async def notify_owner(bot: Bot, settings: Settings, lead: LeadRecord) -> None:
    """Send a newly created lead to the owner Telegram account."""
    await bot.send_message(
        chat_id=settings.owner_telegram_id,
        text=render_owner_notification(lead),
    )
    await mark_lead_notified(settings, lead.id)
