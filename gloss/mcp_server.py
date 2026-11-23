"""Read-only MCP server exposing the glossary over Streamable HTTP.

Run with ``python -m gloss.mcp_server``. The Slack bot in ``app.py`` is a
separate process; both share the same database.
"""

import logging
import os
from contextlib import asynccontextmanager
from threading import BoundedSemaphore
from typing import Literal

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from sqlalchemy.orm import Session
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from . import __version__, mcp_tools
from .db import make_engine
from .mcp_auth import BearerAuthMiddleware
from .mcp_config import (
    allowed_hosts_from_env,
    allowed_origins_from_env,
    auth_token_from_env,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sync tools run in the SDK's thread pool (~40 threads) while SQLAlchemy's
# default pool is 5 + 10 overflow. Cap concurrent DB work below the pool size so
# bursts of searches wait for a permit instead of exhausting the pool.
MAX_CONCURRENT_DB_CALLS = 10
_db_limiter = BoundedSemaphore(MAX_CONCURRENT_DB_CALLS)

engine = make_engine()
MCP_USER_NAME = os.getenv("MCP_USER_NAME", "mcp")

mcp = MCPServer(
    "glossary-bot",
    version=__version__,
    instructions=(
        "Read-only glossary of terms maintained by the Glossary Bot Slack app. "
        "Definitions may be aliases ('see X'); search is fuzzy."
    ),
)


@mcp.tool()
def lookup_term(term: str) -> dict:
    """Look up an exact glossary term (case-insensitive).

    Follows 'see' / 'see also' aliases and returns the canonical definition.
    If the term is not found, returns fuzzy suggestions.
    """
    with _db_limiter, Session(engine) as session:
        return mcp_tools.lookup_term(session, term, user_name=MCP_USER_NAME)


@mcp.tool()
def search_terms(query: str, limit: int = 20) -> dict:
    """Search the glossary by term name (substring) and definition text (fuzzy).

    Returns matching terms with their definitions. ``limit`` is capped at 50.
    """
    with _db_limiter, Session(engine) as session:
        return mcp_tools.search_terms(session, query, limit=limit)


@mcp.tool()
def list_terms(
    limit: int = 50,
    offset: int = 0,
    sort: Literal["recent", "alphabetical"] = "recent",
) -> dict:
    """List glossary entries, newest first (``recent``) or alphabetically.

    Supports limit/offset pagination; ``limit`` is capped at 50.
    """
    with _db_limiter, Session(engine) as session:
        return mcp_tools.list_terms(session, limit=limit, offset=offset, sort=sort)


@mcp.tool()
def glossary_stats() -> dict:
    """Return the number of terms, distinct definers, and total lookups."""
    with _db_limiter, Session(engine) as session:
        return mcp_tools.glossary_stats(session)


async def health(request):
    return JSONResponse({"status": "ok"})


def create_app():
    mcp_app = mcp.streamable_http_app(
        streamable_http_path="/mcp",
        transport_security=TransportSecuritySettings(
            allowed_hosts=allowed_hosts_from_env(),
            allowed_origins=allowed_origins_from_env(),
        ),
    )

    @asynccontextmanager
    async def lifespan(app):
        # Mounting suppresses the MCP app's own lifespan, so start the session
        # manager here.
        async with mcp.session_manager.run():
            yield

    host = Starlette(
        routes=[
            Route("/healthz", health, methods=["GET"]),
            Mount("/", app=mcp_app),
        ],
        lifespan=lifespan,
    )
    return BearerAuthMiddleware(
        host, token=auth_token_from_env(), exempt_paths={"/healthz"}
    )


app = create_app()


def main():
    port = int(os.getenv("PORT") or os.getenv("MCP_PORT") or "8080")
    logger.info("Starting glossary MCP server on port %s", port)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips=os.getenv("FORWARDED_ALLOW_IPS", "*"),
    )


if __name__ == "__main__":
    main()
