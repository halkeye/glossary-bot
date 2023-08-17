import pytest

from unittest import TestCase
from pytest_mock_resources import create_postgres_fixture

from sqlalchemy.orm import Session
from gloss.models import Definition, Interaction, Base
from gloss.bot import Bot

alembic_engine = create_postgres_fixture(Base)

@pytest.fixture
def alembic_config(alembic_engine):
    """Override this fixture to configure the exact alembic context setup required.
    """
    return { 'sqlalchemy.url': alembic_engine.url.render_as_string(hide_password=False) }

@pytest.fixture
def db_session(alembic_engine):
    session = Session(alembic_engine)
    session.query(Interaction).delete()
    session.query(Definition).delete()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def bot(db_session):
    return Bot(bot_name="Glossary Bot", session=db_session)

@pytest.fixture
def handle_glossary(bot):
    def call_handle(text):
        return bot.handle_glossary(text=text, user_name="testuser", slash_command="/test_bot")

    return call_handle

@pytest.fixture
def testcase():
    tc = TestCase()
    tc.maxDiff = None
    return tc
