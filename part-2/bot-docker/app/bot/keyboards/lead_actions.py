from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

CANCEL_TEXT = "Отмена"


def build_lead_actions_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=CANCEL_TEXT)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
