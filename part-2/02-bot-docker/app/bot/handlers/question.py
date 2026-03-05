from aiogram import F, Router
from aiogram.types import Message

from app.bot.keyboards import ASK_QUESTION_TEXT, build_main_menu
from app.bot.texts import LOW_CONFIDENCE_TEXT
from app.config import Settings, SystemPrompt
from app.use_cases import answer_company_question

router = Router(name="question")


@router.message(F.text.casefold() == ASK_QUESTION_TEXT.casefold())
async def prompt_for_question(message: Message) -> None:
    await message.answer(
        "Напишите ваш вопрос, и я постараюсь ответить по базе знаний.",
        reply_markup=build_main_menu(),
    )


@router.message(F.text)
async def handle_question(
    message: Message,
    settings: Settings,
    system_prompt: SystemPrompt,
) -> None:
    question = message.text.strip()
    if not question:
        return

    try:
        answer = await answer_company_question(settings, system_prompt, question)
    except Exception:
        answer = None

    if not answer:
        await message.answer(
            LOW_CONFIDENCE_TEXT,
            reply_markup=build_main_menu(),
        )
        return

    await message.answer(
        answer,
        reply_markup=build_main_menu(),
    )
