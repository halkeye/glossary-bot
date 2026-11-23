import os

from sqlalchemy import create_engine


def normalize_database_url(database_url: str) -> str:
    """Return a SQLAlchemy URL that uses the driver this project installs.

    SQLAlchemy no longer recognizes postgres:// URLs as "postgresql"
    (https://github.com/sqlalchemy/sqlalchemy/issues/6083), and newer releases
    default bare postgresql:// URLs to psycopg 3. This project depends on
    psycopg2, so make the driver explicit. URLs that already name a driver are
    left alone.
    """
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )
    return database_url.replace("ssl-mode=", "ssl_mode=", 1)


def database_url_from_env() -> str:
    """Return DATABASE_URL normalized for SQLAlchemy."""
    return normalize_database_url(os.environ["DATABASE_URL"])


def make_engine(url: str | None = None, **kwargs):
    """Create a SQLAlchemy engine for the glossary database."""
    return create_engine(
        url or database_url_from_env(),
        echo=False,
        pool_recycle=3600,
        pool_pre_ping=True,
        **kwargs,
    )
