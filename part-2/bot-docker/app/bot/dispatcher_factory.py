from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import cancel_router, lead_router, question_router, start_router
from app.config import Settings, SystemPrompt


def create_dispatcher(settings: Settings, system_prompt: SystemPrompt) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.workflow_data.update(
        settings=settings,
        system_prompt=system_prompt,
    )
    dispatcher.include_router(start_router)
    dispatcher.include_router(cancel_router)
    dispatcher.include_router(lead_router)
    dispatcher.include_router(question_router)
    return dispatcher
