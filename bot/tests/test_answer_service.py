from __future__ import annotations

import pytest

from app.rag.answer_service import generate_answer


class FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[tuple[str, str]] = []

    async def generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.response


@pytest.mark.asyncio
async def test_generate_answer_returns_llm_result(monkeypatch) -> None:
    async def fake_search(query: str, top_k: int = 3) -> list[str]:
        assert query == "Сколько стоит лендинг?"
        assert top_k == 3
        return ["Лендинг стоит от 60 000 рублей."]

    monkeypatch.setattr("app.rag.answer_service.search", fake_search)

    llm = FakeLLMProvider("Лендинг обычно стоит от 60 000 рублей.")
    answer = await generate_answer(
        question="Сколько стоит лендинг?",
        system_prompt="system",
        llm_provider=llm,
    )

    assert answer == "Лендинг обычно стоит от 60 000 рублей."
    assert len(llm.calls) == 1
    assert "Лендинг стоит от 60 000 рублей." in llm.calls[0][1]


@pytest.mark.asyncio
async def test_generate_answer_returns_honest_message_when_context_not_found(monkeypatch) -> None:
    async def fake_search(query: str, top_k: int = 3) -> list[str]:
        return []

    monkeypatch.setattr("app.rag.answer_service.search", fake_search)

    answer = await generate_answer(
        question="Какая у вас парковка?",
        system_prompt="system",
        llm_provider=FakeLLMProvider("unused"),
    )

    assert "нет точной информации" in answer
