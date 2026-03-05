from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class LeadDraft:
    telegram_chat_id: int
    telegram_user_id: int | None
    telegram_username: str | None
    customer_name: str
    phone_raw: str
    phone_normalized: str
    question: str


@dataclass(slots=True, frozen=True)
class LeadRecord(LeadDraft):
    id: int
    status: str = "new"
