from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings, SystemPrompt, load_settings, load_system_prompt
from app.db import init_db


@dataclass(slots=True, frozen=True)
class AppContainer:
    settings: Settings
    system_prompt: SystemPrompt


async def bootstrap_application() -> AppContainer:
    """Load runtime dependencies required by the application."""
    settings = load_settings()
    system_prompt = load_system_prompt(settings.system_prompt_path)
    await init_db(settings)
    return AppContainer(settings=settings, system_prompt=system_prompt)
