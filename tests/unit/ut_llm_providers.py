"""Tests for centralized LLM provider configuration."""
import pytest
from config.llm_providers import (
    LLMProviderConfig, LOCAL, OPENAI, ANTHROPIC, MISTRAL, HUGGINGFACE,
    PROVIDERS, DEFAULT, DEFAULT_PROVIDER_NAME,
)


class TestProviderConfigs:
    def test_all_providers_defined(self):
        assert set(PROVIDERS.keys()) == {"local", "openai", "anthropic", "mistral", "huggingface"}

    def test_local_uses_openai_adapter(self):
        assert LOCAL.adapter_type == "openai"
        assert LOCAL.api_key_env is None
        assert LOCAL.is_free is True

    def test_remote_providers_have_api_key_env(self):
        for name in ("openai", "anthropic", "mistral"):
            assert PROVIDERS[name].api_key_env is not None, f"{name} missing api_key_env"

    def test_default_is_local(self):
        assert DEFAULT_PROVIDER_NAME == "local"
        assert DEFAULT is LOCAL

    def test_provider_config_is_frozen(self):
        with pytest.raises(AttributeError):
            LOCAL.model = "something-else"

    def test_invalid_provider_env_falls_back(self, monkeypatch):
        """Verify graceful fallback on bad LLM_PROVIDER."""
        monkeypatch.setenv("LLM_PROVIDER", "nonexistent")
        import importlib
        import config.llm_providers as mod
        importlib.reload(mod)
        assert mod.DEFAULT_PROVIDER_NAME == "local"
        assert mod.DEFAULT is mod.LOCAL
        # Restore
        monkeypatch.delenv("LLM_PROVIDER")
        importlib.reload(mod)
