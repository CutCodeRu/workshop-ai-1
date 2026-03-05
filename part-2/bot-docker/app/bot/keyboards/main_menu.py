from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

ASK_QUESTION_TEXT = "Задать вопрос"
BOOK_CONSULTATION_TEXT = "Записаться на консультацию"


def build_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ASK_QUESTION_TEXT)],
            [KeyboardButton(text=BOOK_CONSULTATION_TEXT)],
        ],
        resize_keyboard=True,
    )
