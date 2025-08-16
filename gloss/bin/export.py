#!/usr/bin/env python

import json
import logging
import os

from sqlalchemy import create_engine
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

results = {"definitions": [], "interactions": []}
with engine.connect() as conn:
    with Session(engine) as session:
        for row in (
            session.query(Definition).order_by(Definition.creation_date.desc()).all()
        ):
            results["definitions"].append(
                {
                    "id": row.id,
                    "creation_date": row.creation_date.isoformat(),
                    "term": row.term,
                    "definition": row.definition,
                    "user_name": row.user_name,
                }
            )

        for row in (
            session.query(Interaction).order_by(Interaction.creation_date.desc()).all()
        ):
            results["interactions"].append(
                {
                    "id": row.id,
                    "creation_date": row.creation_date.isoformat(),
                    "user_name": row.user_name,
                    "term": row.term,
                    "action": row.action,
                }
            )


print(json.dumps(results, indent=2))
