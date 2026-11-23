#!/usr/bin/env python

import json
import logging
import sys

from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..db import make_engine
from ..models import Definition, Interaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = make_engine()

results = json.load(sys.stdin)

with engine.connect() as conn, Session(engine) as session:
    session.execute(delete(Definition))
    for row in results["definitions"]:
        session.add(Definition(**row))

    session.execute(delete(Interaction))
    for row in results["interactions"]:
        session.add(Interaction(**row))

    session.commit()
