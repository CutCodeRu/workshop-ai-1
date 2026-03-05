from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import CANCEL_TEXT, build_main_menu

router = Router(name="cancel")


@router.message(Command("cancel"))
@router.message(F.text.casefold() == CANCEL_TEXT.casefold())
async def cancel_form(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Сейчас нет активной записи.", reply_markup=build_main_menu())
        return

    await state.clear()
    await message.answer("Запись отменена.", reply_markup=build_main_menu())
