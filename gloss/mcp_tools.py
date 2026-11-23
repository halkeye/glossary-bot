"""Read-only glossary queries used by the MCP server.

These helpers take a SQLAlchemy session so they can be tested without starting
an MCP server. They deliberately reuse :class:`gloss.bot.Bot` for the lookup
and fuzzy-search behavior the Slack bot already uses.
"""

from typing import Literal

from sqlalchemy import func

from .bot import Bot, check_definition_for_alias
from .models import Definition

DEFAULT_SEARCH_LIMIT = 20
DEFAULT_LIST_LIMIT = 50
MAX_LIMIT = 50
MAX_SUGGESTIONS = 10
VALID_SORTS = ("recent", "alphabetical")


def _clamp_limit(limit, default: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, MAX_LIMIT))


def _clamp_offset(offset) -> int:
    try:
        return max(0, int(offset))
    except (TypeError, ValueError):
        return 0


def _definition_payload(entry: Definition) -> dict:
    return {
        "term": entry.term,
        "definition": entry.definition,
        "created_at": entry.creation_date.isoformat() if entry.creation_date else None,
    }


def lookup_term(session, term: str, user_name: str = "mcp") -> dict:
    """Look up one exact term, resolving a single ``see`` / ``see also`` alias.

    On a miss, returns fuzzy suggestions from the same search the Slack bot uses.
    """
    term = (term or "").strip()
    bot = Bot(bot_name="Glossary Bot", session=session)

    entry = bot.query_definition(term) if term else None
    if entry is None:
        if term:
            bot.log_query(term=term, user_name=user_name, action="not_found")
            suggestions = bot.get_matches_for_term(term)[:MAX_SUGGESTIONS]
        else:
            suggestions = []
        return {"found": False, "term": term, "suggestions": suggestions}

    bot.log_query(term=term, user_name=user_name, action="found")

    alias_of = None
    if entry.definition:
        alias_term = check_definition_for_alias(entry.definition)
        if alias_term:
            alias_entry = bot.query_definition(alias_term)
            if alias_entry:
                alias_of = term
                entry = alias_entry

    return {
        "found": True,
        "term": entry.term,
        "definition": entry.definition,
        "alias_of": alias_of,
    }


def search_terms(session, query: str, limit: int = DEFAULT_SEARCH_LIMIT) -> dict:
    """Search term names (substring) and definitions (fuzzy), returning definitions."""
    query = (query or "").strip()
    limit = _clamp_limit(limit, DEFAULT_SEARCH_LIMIT)

    terms = []
    if query:
        bot = Bot(bot_name="Glossary Bot", session=session)
        terms = bot.get_matches_for_term(query)[:limit]

    matches = []
    if terms:
        entries = {
            entry.term: entry
            for entry in session.query(Definition)
            .filter(Definition.term.in_(terms))
            .all()
        }
        for term in terms:
            entry = entries.get(term)
            if entry is not None:
                matches.append({"term": entry.term, "definition": entry.definition})

    return {"query": query, "count": len(matches), "matches": matches}


def list_terms(
    session,
    limit: int = DEFAULT_LIST_LIMIT,
    offset: int = 0,
    sort: Literal["recent", "alphabetical"] = "recent",
) -> dict:
    """List glossary entries, newest first or alphabetically."""
    if sort not in VALID_SORTS:
        raise ValueError(f"sort must be one of {VALID_SORTS}")

    limit = _clamp_limit(limit, DEFAULT_LIST_LIMIT)
    offset = _clamp_offset(offset)

    query = session.query(Definition)
    if sort == "alphabetical":
        query = query.order_by(Definition.term.asc())
    else:
        query = query.order_by(Definition.creation_date.desc())

    total = session.query(func.count(Definition.term)).scalar() or 0
    rows = query.limit(limit).offset(offset).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "sort": sort,
        "terms": [_definition_payload(row) for row in rows],
    }


def glossary_stats(session) -> dict:
    """Return term, definer, and lookup counts."""
    return Bot(bot_name="Glossary Bot", session=session).get_stats_values()
