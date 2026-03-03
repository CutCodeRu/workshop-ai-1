from __future__ import annotations

import logging
from html import escape

from aiogram import Bot
from aiogram.types import User

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, owner_chat_id: int | None) -> None:
        self._owner_chat_id = owner_chat_id

    async def notify_new_application(
        self,
        bot: Bot,
        application_id: int,
        name: str,
        phone: str,
        question: str,
        telegram_user: User | None,
    ) -> None:
        username = (
            f"@{escape(telegram_user.username)}"
            if telegram_user and telegram_user.username
            else "не указан"
        )
        user_id = str(telegram_user.id) if telegram_user else "неизвестен"

        text = (
            "Новая заявка на консультацию\n\n"
            f"ID: {application_id}\n"
            f"Имя: {escape(name)}\n"
            f"Телефон: {escape(phone)}\n"
            f"Вопрос: {escape(question)}\n"
            f"Telegram user_id: {user_id}\n"
            f"Telegram username: {username}"
        )

        if self._owner_chat_id is None:
            logger.warning(
                "OWNER_CHAT_ID не задан. Уведомление о заявке %s пропущено.",
                application_id,
            )
            return

        await bot.send_message(chat_id=self._owner_chat_id, text=text)
