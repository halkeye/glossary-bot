import pytest

from gloss import mcp_config


def test_allowed_hosts_parses_csv(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", " example.com, example.com:* ,, ")

    assert mcp_config.allowed_hosts_from_env() == ["example.com", "example.com:*"]


def test_allowed_hosts_requires_a_value(monkeypatch):
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)

    with pytest.raises(RuntimeError, match="MCP_ALLOWED_HOSTS"):
        mcp_config.allowed_hosts_from_env()


def test_allowed_origins_default_to_empty(monkeypatch):
    monkeypatch.delenv("MCP_ALLOWED_ORIGINS", raising=False)

    assert mcp_config.allowed_origins_from_env() == []


def test_allowed_origins_parse_csv(monkeypatch):
    monkeypatch.setenv(
        "MCP_ALLOWED_ORIGINS", "https://app.example.com, http://localhost:6274"
    )

    assert mcp_config.allowed_origins_from_env() == [
        "https://app.example.com",
        "http://localhost:6274",
    ]


def test_auth_token_is_required(monkeypatch):
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="MCP_AUTH_TOKEN"):
        mcp_config.auth_token_from_env()


def test_auth_token_is_returned(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "secret")

    assert mcp_config.auth_token_from_env() == "secret"
