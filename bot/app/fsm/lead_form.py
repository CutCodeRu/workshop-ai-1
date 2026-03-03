from aiogram.fsm.state import State, StatesGroup


class LeadForm(StatesGroup):
    wait_name = State()
    wait_phone = State()
    wait_question = State()
