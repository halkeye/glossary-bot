"""Environment configuration helpers for the MCP server."""

import os


def csv_env(name: str) -> list[str]:
    """Return a comma-separated environment variable as a list."""
    raw = os.getenv(name, "")
    return [value.strip() for value in raw.split(",") if value.strip()]


def required_env(name: str) -> str:
    """Return a required environment variable or raise a clear startup error."""
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"{name} must be set")
    return value


def allowed_hosts_from_env() -> list[str]:
    hosts = csv_env("MCP_ALLOWED_HOSTS")
    if not hosts:
        raise RuntimeError(
            "MCP_ALLOWED_HOSTS must list the public hostname(s) that serve /mcp"
        )
    return hosts


def allowed_origins_from_env() -> list[str]:
    return csv_env("MCP_ALLOWED_ORIGINS")


def auth_token_from_env() -> str:
    return required_env("MCP_AUTH_TOKEN")
