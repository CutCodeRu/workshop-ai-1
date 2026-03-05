from __future__ import annotations

import re

from app.config import Settings
from app.db.repositories import create_lead as create_lead_record
from app.schemas import LeadDraft, LeadRecord

_NON_DIGIT_RE = re.compile(r"\D+")


class InvalidPhoneError(ValueError):
    """Raised when the provided phone number is too short."""


def normalize_phone(phone_raw: str) -> str:
    """Normalize a phone number to a compact international-like format."""
    digits = _NON_DIGIT_RE.sub("", phone_raw)
    if len(digits) < 10:
        raise InvalidPhoneError("Телефон должен содержать минимум 10 цифр.")

    if phone_raw.strip().startswith("+"):
        return f"+{digits}"

    if len(digits) == 11 and digits.startswith("8"):
        return f"+7{digits[1:]}"

    return f"+{digits}"


async def create_lead(
    settings: Settings,
    *,
    telegram_chat_id: int,
    telegram_user_id: int | None,
    telegram_username: str | None,
    customer_name: str,
    phone_raw: str,
    question: str,
) -> LeadRecord:
    """Validate and persist a lead from the FSM form."""
    lead = LeadDraft(
        telegram_chat_id=telegram_chat_id,
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_username,
        customer_name=customer_name.strip(),
        phone_raw=phone_raw.strip(),
        phone_normalized=normalize_phone(phone_raw),
        question=question.strip(),
    )
    return await create_lead_record(settings, lead)
