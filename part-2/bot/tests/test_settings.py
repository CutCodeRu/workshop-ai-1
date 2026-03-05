from app.config.settings import Settings


def test_settings_treats_empty_owner_chat_id_as_none(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OWNER_CHAT_ID", "")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/secretary_bot",
    )

    settings = Settings()

    assert settings.owner_chat_id is None
