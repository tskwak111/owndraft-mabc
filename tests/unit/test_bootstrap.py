from owndraft.core.settings import Settings


def test_settings_uses_upstage_compatible_defaults(monkeypatch):
    monkeypatch.setenv("UPSTAGE_API_KEY", "test-key")
    settings = Settings()

    assert settings.upstage_base_url == "https://api.upstage.ai/v1"
    assert settings.upstage_chat_model == "solar-pro4"
    assert settings.max_document_chars == 10_000
    assert settings.max_repair_attempts == 1
