from __future__ import annotations

import logging
import re

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.bot.keyboards import BOOK_CONSULTATION_BUTTON, build_main_keyboard
from app.db import DatabaseConnectionError
from app.fsm.lead_form import LeadForm
from app.services import LeadService, NotificationService

router = Router(name="lead")
logger = logging.getLogger(__name__)


@router.message(StateFilter(None), F.text == BOOK_CONSULTATION_BUTTON)
async def start_consultation_flow(message: Message, state: FSMContext) -> None:
    await state.set_state(LeadForm.wait_name)
    await message.answer(
        "Давайте оформим заявку. Как вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(LeadForm.wait_name, F.text)
async def collect_name(message: Message, state: FSMContext) -> None:
    name = " ".join(message.text.split()).strip()
    if not name:
        await message.answer("Напишите, пожалуйста, ваше имя.")
        return

    await state.update_data(name=name)
    await state.set_state(LeadForm.wait_phone)
    await message.answer("Укажите, пожалуйста, телефон для связи.")


@router.message(LeadForm.wait_phone, F.text)
async def collect_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not phone:
        await message.answer("Напишите, пожалуйста, телефон для связи.")
        return

    if len(re.sub(r"\D+", "", phone)) < 10:
        await message.answer(
            "Укажите, пожалуйста, корректный телефон. "
            "Номер должен содержать не меньше 10 цифр."
        )
        return

    await state.update_data(phone=phone)
    await state.set_state(LeadForm.wait_question)
    await message.answer("Коротко опишите ваш вопрос или цель консультации.")


@router.message(LeadForm.wait_question, F.text)
async def collect_question(
    message: Message,
    state: FSMContext,
    bot: Bot,
    lead_service: LeadService,
    notification_service: NotificationService,
) -> None:
    question = " ".join(message.text.split()).strip()
    if not question:
        await message.answer("Напишите, пожалуйста, с чем вам нужна консультация.")
        return

    data = await state.get_data()
    name = data.get("name", "")
    phone = data.get("phone", "")
    user_id = message.from_user.id if message.from_user else message.chat.id

    try:
        application_id = await lead_service.create_application(
            name=name,
            phone=phone,
            question=question,
            user_id=user_id,
        )
    except ValueError as exc:
        await message.answer(str(exc))
        return
    except (DatabaseConnectionError, RuntimeError):
        logger.exception("Не удалось сохранить заявку пользователя %s.", user_id)
        await message.answer(
            "Не удалось сохранить заявку из-за ошибки базы данных. "
            "Попробуйте отправить её ещё раз чуть позже."
        )
        return

    try:
        await notification_service.notify_new_application(
            bot=bot,
            application_id=application_id,
            name=name,
            phone=phone,
            question=question,
            telegram_user=message.from_user,
        )
    except Exception:
        logger.exception(
            "Заявка %s сохранена, но уведомление владельцу не отправлено.",
            application_id,
        )
        await state.clear()
        await message.answer(
            "Заявку сохранил, но уведомление владельцу пока не отправлено. "
            "Мы свяжемся с вами позже.",
            reply_markup=build_main_keyboard(),
        )
        return

    await state.clear()
    await message.answer(
        "Спасибо! Заявку принял. Скоро с вами свяжутся.",
        reply_markup=build_main_keyboard(),
    )


@router.message(LeadForm.wait_name)
async def wait_name_text_only(message: Message) -> None:
    await message.answer("Напишите, пожалуйста, имя обычным текстом.")


@router.message(LeadForm.wait_phone)
async def wait_phone_text_only(message: Message) -> None:
    await message.answer("Напишите, пожалуйста, телефон обычным текстом.")


@router.message(LeadForm.wait_question)
async def wait_question_text_only(message: Message) -> None:
    await message.answer("Напишите, пожалуйста, ваш вопрос обычным текстом.")
