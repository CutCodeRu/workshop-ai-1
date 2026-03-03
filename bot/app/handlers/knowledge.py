from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.bot.keyboards import build_main_keyboard
from app.db.connection import DatabaseConnectionError
from app.rag.answer_service import generate_answer

router = Router(name="knowledge")


@router.message(StateFilter(None), F.text)
async def handle_text_question(message: Message, system_prompt: str) -> None:
    question = message.text.strip()
    if not question:
        await message.answer(
            "Напишите, пожалуйста, вопрос текстом.",
            reply_markup=build_main_keyboard(),
        )
        return

    try:
        answer = await generate_answer(question=question, system_prompt=system_prompt)
    except (DatabaseConnectionError, RuntimeError):
        await message.answer(
            "Сейчас не получается обратиться к базе знаний. Попробуйте ещё раз чуть позже.",
            reply_markup=build_main_keyboard(),
        )
        return

    await message.answer(answer, reply_markup=build_main_keyboard())
