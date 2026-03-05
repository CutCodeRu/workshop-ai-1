from __future__ import annotations

import re

from app.repositories.lead_repository import insert_application


class LeadService:
    async def create_application(
        self,
        name: str,
        phone: str,
        question: str,
        user_id: int,
    ) -> int:
        cleaned_name = " ".join(name.split()).strip()
        cleaned_phone = phone.strip()
        cleaned_question = " ".join(question.split()).strip()

        if not cleaned_name:
            raise ValueError("Имя не может быть пустым.")

        if not self._looks_like_phone(cleaned_phone):
            raise ValueError("Телефон заполнен в неверном формате.")

        if not cleaned_question:
            raise ValueError("Вопрос не может быть пустым.")

        return await insert_application(
            name=cleaned_name,
            phone=cleaned_phone,
            question=cleaned_question,
            user_id=user_id,
        )

    @staticmethod
    def _looks_like_phone(phone: str) -> bool:
        digits = re.sub(r"\D+", "", phone)
        return len(digits) >= 10
