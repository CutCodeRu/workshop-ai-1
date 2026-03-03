from __future__ import annotations

from app.bootstrap import build_application
from app.bot import setup_bot_commands
from app.db import init_db


async def main() -> None:
    application = build_application()

    await init_db()
    await setup_bot_commands(application.bot)

    try:
        await application.dispatcher.start_polling(
            application.bot,
            lead_service=application.lead_service,
            notification_service=application.notification_service,
            system_prompt=application.system_prompt,
        )
    finally:
        await application.bot.session.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
