from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

ASK_QUESTION_BUTTON = "Задать вопрос"
BOOK_CONSULTATION_BUTTON = "Записаться на консультацию"


def build_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ASK_QUESTION_BUTTON)],
            [KeyboardButton(text=BOOK_CONSULTATION_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
