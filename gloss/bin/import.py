#!/usr/bin/env python

import json
import logging
import os
import sys

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from ..models import Definition, Interaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database_url = os.environ["DATABASE_URL"]
# SQLAlchemy no longer recognizes postgres:// URLs as "postgresql"
# https://github.com/sqlalchemy/sqlalchemy/issues/6083
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)

results = json.load(sys.stdin)

with engine.connect() as conn:
    with Session(engine) as session:
        session.execute(delete(Definition))
        for row in results["definitions"]:
            session.add(Definition(**row))
        session.execute(delete(Interaction))
        for row in results["interactions"]:
            session.add(Interaction(**row))

        session.commit()
