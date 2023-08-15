import json
import pytest
from os import environ

from unittest import TestCase
from pytest_alembic.config import Config
from pytest_mock_resources import create_postgres_fixture
from sqlalchemy import MetaData, Select, create_engine, select, text

from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from gloss.models import Definition, Base, Interaction
from gloss.bot import Bot

alembic_engine = create_postgres_fixture(declarative_base())

# @pytest.fixture
# def alembic_engine(pg):
#     return pg

# @pytest.fixture
# def alembic_engine():
#     """Override this fixture to provide pytest-alembic powered tests with a database handle.
#     """
#     db_url = environ.get('TEST_DATABASE_URL', 'postgresql:///glossary-bot-test')
#     if db_url.startswith("postgres://"):
#         db_url = db_url.replace("postgres://", "postgresql://", 1)
#     environ['DATABASE_URL'] = db_url
#     return create_engine(db_url)

@pytest.fixture
def alembic_config(alembic_engine):
    """Override this fixture to configure the exact alembic context setup required.
    """
    return Config(
         config_options={
             'sqlalchemy.url': alembic_engine.url.render_as_string(hide_password=False)
         }
    )

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


# set up a hook to be able to check if a test has failed
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield

    rep = outcome.get_result()

    if rep.failed:
        if item.funcargs.get('alembic_engine'):
            with item.funcargs['alembic_engine'].begin() as conn:
                meta = MetaData()
                meta.reflect(bind=conn)
                result = {}
                for table in meta.sorted_tables:
                    result[table.name] = []
                    rs = conn.execute(text(f'SELECT * FROM {table.name}'))
                    for row in rs:
                        result[table.name].append(repr(row))

                with open(f"{item.name}.json", "w") as write_file:
                    json.dump(result, write_file, indent=4)

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
