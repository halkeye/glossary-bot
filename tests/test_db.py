import pytest

from gloss.db import normalize_database_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgres://user:pass@host/db",
            "postgresql+psycopg2://user:pass@host/db",
        ),
        (
            "postgresql://user:pass@host/db",
            "postgresql+psycopg2://user:pass@host/db",
        ),
        (
            "postgresql+psycopg://user:pass@host/db",
            "postgresql+psycopg://user:pass@host/db",
        ),
        (
            "postgresql+psycopg2://user:pass@host/db",
            "postgresql+psycopg2://user:pass@host/db",
        ),
        ("mysql://user:pass@host/db", "mysql://user:pass@host/db"),
        ("sqlite://", "sqlite://"),
    ],
)
def test_normalize_database_url(raw, expected):
    assert normalize_database_url(raw) == expected


def test_normalize_database_url_rewrites_ssl_mode():
    assert (
        normalize_database_url("postgresql://host/db?ssl-mode=require")
        == "postgresql+psycopg2://host/db?ssl_mode=require"
    )
