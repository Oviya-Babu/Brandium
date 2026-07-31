from src.config import Settings, get_settings


def test_settings_load_with_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.environment == "local"
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
