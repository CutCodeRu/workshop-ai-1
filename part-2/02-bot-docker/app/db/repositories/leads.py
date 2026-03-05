from __future__ import annotations

from dataclasses import asdict

from app.config import Settings
from app.db.connection import connect
from app.schemas import LeadDraft, LeadRecord


async def create_lead(settings: Settings, lead: LeadDraft) -> LeadRecord:
    """Persist a new lead and return its stored representation."""
    conn = await connect(settings)
    try:
        lead_id = await conn.fetchval(
            """
            INSERT INTO leads (
                telegram_chat_id,
                telegram_user_id,
                telegram_username,
                customer_name,
                phone_raw,
                phone_normalized,
                question
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id;
            """,
            lead.telegram_chat_id,
            lead.telegram_user_id,
            lead.telegram_username,
            lead.customer_name,
            lead.phone_raw,
            lead.phone_normalized,
            lead.question,
        )
    finally:
        await conn.close()

    return LeadRecord(id=int(lead_id), **asdict(lead))


async def mark_lead_notified(settings: Settings, lead_id: int) -> None:
    """Mark a lead as already sent to the owner."""
    conn = await connect(settings)
    try:
        await conn.execute(
            """
            UPDATE leads
            SET notified_at = NOW()
            WHERE id = $1;
            """,
            lead_id,
        )
    finally:
        await conn.close()
