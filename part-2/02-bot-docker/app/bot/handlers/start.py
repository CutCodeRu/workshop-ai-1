from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import build_main_menu

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Здравствуйте! Я бот-помощник.\n"
        "Вы можете задать вопрос или оставить заявку на консультацию.",
        reply_markup=build_main_menu(),
    )
