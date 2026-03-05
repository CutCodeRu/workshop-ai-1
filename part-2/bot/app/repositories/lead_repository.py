from __future__ import annotations

from app.db import save_application


async def insert_application(
    name: str,
    phone: str,
    question: str,
    user_id: int,
) -> int:
    return await save_application(
        name=name,
        phone=phone,
        question=question,
        user_id=user_id,
    )
