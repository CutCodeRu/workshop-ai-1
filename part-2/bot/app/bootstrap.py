from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot import setup_routers
from app.config import Settings, configure_logging, get_settings
from app.services import LeadService, NotificationService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Application:
    settings: Settings
    bot: Bot
    dispatcher: Dispatcher
    lead_service: LeadService
    notification_service: NotificationService
    system_prompt: str


def build_application() -> Application:
    settings = get_settings()
    configure_logging(settings.log_level)

    if settings.owner_chat_id is None:
        logger.warning(
            "OWNER_CHAT_ID не задан. Бот запустится без уведомлений владельцу."
        )

    system_prompt_path = settings.resolve_system_prompt_path()
    try:
        system_prompt = system_prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Не найден файл системного промпта: {system_prompt_path}"
        ) from exc

    if not system_prompt:
        raise RuntimeError(f"Системный промпт пуст: {system_prompt_path}")

    logger.info("Системный промпт загружен из %s", system_prompt_path)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(setup_routers())

    return Application(
        settings=settings,
        bot=bot,
        dispatcher=dispatcher,
        lead_service=LeadService(),
        notification_service=NotificationService(
            owner_chat_id=settings.owner_chat_id
        ),
        system_prompt=system_prompt,
    )
