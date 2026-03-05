from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards import BOOK_CONSULTATION_TEXT, build_lead_actions_keyboard, build_main_menu
from app.bot.states import LeadForm
from app.config import Settings
from app.use_cases import InvalidPhoneError, create_lead, normalize_phone, notify_owner

router = Router(name="lead")


@router.message(F.text.casefold() == BOOK_CONSULTATION_TEXT.casefold())
async def start_lead_collection(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.wait_name)
    await state.update_data(source_message_id=message.message_id)
    await message.answer(
        "Как вас зовут?",
        reply_markup=build_lead_actions_keyboard(),
    )


@router.message(LeadForm.wait_name, F.text)
async def collect_name(message: Message, state: FSMContext) -> None:
    customer_name = message.text.strip()
    if not customer_name:
        await message.answer(
            "Имя не должно быть пустым. Напишите, как к вам обращаться.",
            reply_markup=build_lead_actions_keyboard(),
        )
        return

    await state.update_data(customer_name=customer_name)
    await state.set_state(LeadForm.wait_phone)
    await message.answer(
        "Укажите ваш телефон.",
        reply_markup=build_lead_actions_keyboard(),
    )


@router.message(LeadForm.wait_phone, F.text)
async def collect_phone(message: Message, state: FSMContext) -> None:
    raw_phone = message.text.strip()
    try:
        normalize_phone(raw_phone)
    except InvalidPhoneError:
        await message.answer(
            "Не удалось распознать телефон. Отправьте номер в формате +79991234567 или 89991234567.",
            reply_markup=build_lead_actions_keyboard(),
        )
        return

    await state.update_data(phone_raw=raw_phone)
    await state.set_state(LeadForm.wait_question)
    await message.answer(
        "Коротко опишите ваш вопрос или тему консультации.",
        reply_markup=build_lead_actions_keyboard(),
    )


@router.message(LeadForm.wait_question, F.text)
async def collect_question(
    message: Message,
    state: FSMContext,
    settings: Settings,
) -> None:
    question = message.text.strip()
    if not question:
        await message.answer(
            "Опишите вопрос хотя бы в одном предложении.",
            reply_markup=build_lead_actions_keyboard(),
        )
        return

    data = await state.get_data()
    lead = await create_lead(
        settings,
        telegram_chat_id=message.chat.id,
        telegram_user_id=message.from_user.id if message.from_user else None,
        telegram_username=message.from_user.username if message.from_user else None,
        customer_name=data["customer_name"],
        phone_raw=data["phone_raw"],
        question=question,
    )
    await notify_owner(message.bot, settings, lead)
    await state.clear()
    await message.answer(
        "Спасибо, заявку получил. Скоро с вами свяжутся.",
        reply_markup=build_main_menu(),
    )
