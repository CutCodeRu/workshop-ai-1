from __future__ import annotations

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.bot.keyboards import build_main_keyboard

router = Router(name="fallback")


@router.message(StateFilter(None))
async def handle_unsupported_message(message: Message) -> None:
    await message.answer(
        "Пока я понимаю только текстовые сообщения. "
        "Вы можете задать вопрос или оставить заявку на консультацию.",
        reply_markup=build_main_keyboard(),
    )
