from datetime import datetime

import pytest

from gloss import mcp_tools
from gloss.models import Definition, Interaction

from . import conftest  # noqa: F401


def seed(db_session, term, definition, user_name="testuser", created=None):
    db_session.add(
        Definition(
            term=term,
            definition=definition,
            user_name=user_name,
            creation_date=created or datetime(2026, 1, 1),
        )
    )
    db_session.commit()


class TestLookupTerm:
    def test_exact_lookup_is_case_insensitive(self, db_session):
        seed(db_session, "EW", "Eligibility Worker")

        result = mcp_tools.lookup_term(db_session, "ew")

        assert result == {
            "found": True,
            "term": "EW",
            "definition": "Eligibility Worker",
            "alias_of": None,
        }
        interaction = db_session.query(Interaction).one()
        assert interaction.term == "ew"
        assert interaction.user_name == "mcp"
        assert interaction.action == "found"

    def test_alias_resolves_to_canonical_term(self, db_session):
        seed(db_session, "Glossary Bot", "A Slack bot that maintains a glossary.")
        seed(db_session, "GB", "see Glossary Bot")

        result = mcp_tools.lookup_term(db_session, "GB")

        assert result["found"] is True
        assert result["term"] == "Glossary Bot"
        assert result["definition"] == "A Slack bot that maintains a glossary."
        assert result["alias_of"] == "GB"

    def test_alias_to_missing_term_returns_alias_entry(self, db_session):
        seed(db_session, "GB", "see Glossary Bot")

        result = mcp_tools.lookup_term(db_session, "GB")

        assert result["found"] is True
        assert result["term"] == "GB"
        assert result["definition"] == "see Glossary Bot"
        assert result["alias_of"] is None

    def test_miss_returns_suggestions_and_logs_not_found(self, db_session):
        seed(db_session, "abglosscd", "a cool thing")
        seed(db_session, "standard gloss", "a good resource")

        result = mcp_tools.lookup_term(db_session, "gloss")

        assert result["found"] is False
        assert result["term"] == "gloss"
        assert "abglosscd" in result["suggestions"]
        assert "standard gloss" in result["suggestions"]
        interaction = db_session.query(Interaction).one()
        assert interaction.user_name == "mcp"
        assert interaction.action == "not_found"

    def test_empty_term_returns_no_suggestions(self, db_session):
        seed(db_session, "EW", "Eligibility Worker")

        result = mcp_tools.lookup_term(db_session, "   ")

        assert result == {"found": False, "term": "", "suggestions": []}
        assert db_session.query(Interaction).count() == 0


class TestSearchTerms:
    def test_search_matches_definition_text(self, db_session):
        seed(db_session, "TAY", "Transitional Age Youth")
        seed(db_session, "WIB", "Workforce Investment Board")

        result = mcp_tools.search_terms(db_session, "youth")

        assert result["query"] == "youth"
        assert result["count"] >= 1
        assert "TAY" in [match["term"] for match in result["matches"]]
        for match in result["matches"]:
            assert "definition" in match

    def test_search_matches_term_substring(self, db_session):
        seed(db_session, "CalWIN", "A statewide system")
        seed(db_session, "TAY", "Transitional Age Youth")

        result = mcp_tools.search_terms(db_session, "cal")

        assert "CalWIN" in [match["term"] for match in result["matches"]]

    def test_search_limit_is_clamped(self, db_session):
        seed(db_session, "EW", "Eligibility Worker")

        result = mcp_tools.search_terms(db_session, "eligibility", limit=0)

        assert result["count"] <= 1
        result = mcp_tools.search_terms(db_session, "eligibility", limit=999)
        assert len(result["matches"]) <= mcp_tools.MAX_LIMIT

    def test_empty_query_returns_no_matches(self, db_session):
        seed(db_session, "EW", "Eligibility Worker")

        result = mcp_tools.search_terms(db_session, "")

        assert result == {"query": "", "count": 0, "matches": []}


class TestListTerms:
    def test_recent_order_and_total(self, db_session):
        seed(db_session, "OLD", "oldest", created=datetime(2026, 1, 1))
        seed(db_session, "NEW", "newest", created=datetime(2026, 1, 3))
        seed(db_session, "MID", "middle", created=datetime(2026, 1, 2))

        result = mcp_tools.list_terms(db_session)

        assert result["total"] == 3
        assert result["sort"] == "recent"
        assert [entry["term"] for entry in result["terms"]] == ["NEW", "MID", "OLD"]
        assert result["terms"][0]["created_at"] == "2026-01-03T00:00:00"

    def test_alphabetical_order_and_pagination(self, db_session):
        seed(db_session, "B", "bravo", created=datetime(2026, 1, 1))
        seed(db_session, "A", "alpha", created=datetime(2026, 1, 2))
        seed(db_session, "C", "charlie", created=datetime(2026, 1, 3))

        result = mcp_tools.list_terms(db_session, limit=1, offset=1, sort="alphabetical")

        assert result["total"] == 3
        assert result["offset"] == 1
        assert result["limit"] == 1
        assert [entry["term"] for entry in result["terms"]] == ["B"]

    def test_limit_is_clamped(self, db_session):
        seed(db_session, "EW", "Eligibility Worker")

        result = mcp_tools.list_terms(db_session, limit=999)

        assert result["limit"] == mcp_tools.MAX_LIMIT

    def test_unknown_sort_raises(self, db_session):
        with pytest.raises(ValueError):
            mcp_tools.list_terms(db_session, sort="random")


class TestGlossaryStats:
    def test_counts_terms_definers_and_lookups(self, db_session):
        seed(db_session, "EW", "Eligibility Worker", user_name="alice")
        seed(db_session, "TAY", "Transitional Age Youth", user_name="bob")
        mcp_tools.lookup_term(db_session, "EW", user_name="mcp")

        assert mcp_tools.glossary_stats(db_session) == {
            "terms": 2,
            "definers": 2,
            "lookups": 1,
        }


def test_mcp_tools_expose_no_write_paths():
    for name in (
        "set_definition",
        "delete_definition",
        "set_definition_and_get_response",
    ):
        assert not hasattr(mcp_tools, name)
