from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import configure_logging, get_settings
from app.rag import load_knowledge


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    stored_count = await load_knowledge(settings.resolve_knowledge_file_path())
    logging.getLogger(__name__).info(
        "Ручная переиндексация завершена. chunks_saved=%s",
        stored_count,
    )


if __name__ == "__main__":
    asyncio.run(main())
