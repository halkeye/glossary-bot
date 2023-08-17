import pytest
from os import environ

from unittest import TestCase
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import create_engine

from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from gloss.models import Definition, Interaction
from gloss.bot import Bot

pg = create_postgres_fixture(declarative_base())

@pytest.fixture
def alembic_engine(pg):
    """Override this fixture to provide pytest-alembic powered tests with a database handle.
    """
    if environ.get('TEST_DATABASE_URL'):
        db_url = environ.get('TEST_DATABASE_URL', 'postgresql:///glossary-bot-test')
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        environ['DATABASE_URL'] = db_url
        return create_engine(db_url)
    return pg

# @pytest.fixture
# def alembic_config(alembic_engine):
#     """Override this fixture to configure the exact alembic context setup required.
#     """
#     return Config(
#          config_options={
#              'sqlalchemy.url': alembic_engine.url.render_as_string(hide_password=False)
#          }
#     )

@pytest.fixture
def db_session(alembic_engine, alembic_runner):
    environ['DATABASE_URL'] = alembic_engine.url.render_as_string(hide_password=False)
    alembic_runner.migrate_up_to('heads')

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
