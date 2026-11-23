#!/usr/bin/env python

import json
import logging

from sqlalchemy.orm import Session

from ..db import make_engine
from ..models import Definition, Interaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = make_engine()

results = {"definitions": [], "interactions": []}
with engine.connect() as conn, Session(engine) as session:
    for row in session.query(Definition).order_by(Definition.creation_date.desc()).all():
        results["definitions"].append(
            {
                "id": row.id,
                "creation_date": row.creation_date.isoformat(),
                "term": row.term,
                "definition": row.definition,
                "user_name": row.user_name,
            }
        )

    for row in session.query(Interaction).order_by(Interaction.creation_date.desc()).all():
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
