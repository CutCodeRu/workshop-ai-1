from __future__ import annotations

import asyncio

from app.bot import create_bot, create_dispatcher, run_polling, run_webhook
from app.bootstrap import bootstrap_application
from app.logging import configure_logging


async def run() -> None:
    container = await bootstrap_application()
    configure_logging(container.settings.log_level)
    bot = create_bot(container.settings)
    dispatcher = create_dispatcher(container.settings, container.system_prompt)

    if container.settings.app_env == "prod":
        await run_webhook(bot, dispatcher, container.settings)
        return

    await run_polling(bot, dispatcher)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
