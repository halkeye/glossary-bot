import pytest

from unittest import TestCase
from pytest_alembic.config import Config
from pytest_mock_resources import create_postgres_fixture

from sqlalchemy.orm import Session
from gloss.models import Definition, Base, Interaction
from gloss.bot import Bot


pg = create_postgres_fixture(Base)

@pytest.fixture
def alembic_engine(pg):
    return pg

# @pytest.fixture
# def alembic_engine():
#     """Override this fixture to provide pytest-alembic powered tests with a database handle.
#     """
#     db_url = environ.get('TEST_DATABASE_URL', 'postgresql:///glossary-bot-test')
#     if db_url.startswith("postgres://"):
#         db_url = db_url.replace("postgres://", "postgresql://", 1)
#     return create_engine(db_url)

@pytest.fixture
def alembic_config():
    """Override this fixture to configure the exact alembic context setup required.
    """
    return Config()

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
