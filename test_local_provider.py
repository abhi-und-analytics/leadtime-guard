"""Local / on-premise model settings: no cloud key needed, server address is configurable."""
import importlib

import pytest

from leadtime_guard.llm import client


def _settings(monkeypatch, **env):
    for k in ("LTG_PROVIDER", "LTG_MODEL", "OLLAMA_BASE_URL", "LTG_BASE_URL", "LTG_MIN_INTERVAL"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    importlib.reload(client)
    return client.provider_settings()


def test_ollama_defaults_to_this_machine(monkeypatch):
    mp = monkeypatch
    p = _settings(mp, LTG_PROVIDER="ollama")
    assert p["base_url"] == "http://localhost:11434/v1" and p["key_env"] is None
    assert client.MIN_INTERVAL_S == 0.0          # no rate limit on your own server


def test_ollama_on_a_company_server(monkeypatch):
    mp = monkeypatch
    p = _settings(mp, LTG_PROVIDER="ollama", OLLAMA_BASE_URL="http://ai-server.internal:11434/v1")
    assert p["base_url"] == "http://ai-server.internal:11434/v1"


def test_local_server_needs_url_and_model(monkeypatch):
    mp = monkeypatch
    with pytest.raises(SystemExit):
        _settings(mp, LTG_PROVIDER="local")
    p = _settings(mp, LTG_PROVIDER="local", LTG_BASE_URL="http://localhost:8000/v1", LTG_MODEL="qwen2.5-7b")
    assert (p["base_url"], p["model"]) == ("http://localhost:8000/v1", "qwen2.5-7b")
