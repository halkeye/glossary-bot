from datetime import datetime

import sqlalchemy.types as types
from sqlalchemy import Column
from sqlalchemy.orm import declarative_base


class LimitedLengthUnicode(types.TypeDecorator):
    impl = types.Unicode

    # its okay to be used as a cache key
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value[: self.impl.length]

    def copy(self, **kwargs):
        return LimitedLengthUnicode(self.impl.length)


Base = declarative_base()


class Definition(Base):
    """Records of term definitions, along with some metadata"""

    __tablename__ = "definitions"
    # Columns
    id = Column(types.Integer, primary_key=True)
    creation_date = Column(types.DateTime(), default=datetime.utcnow)
    term = Column(LimitedLengthUnicode(255), index=True)
    definition = Column(types.UnicodeText)
    user_name = Column(types.Unicode(255))

    def __repr__(self):
        return "<Term: {}, Definition: {}>".format(self.term, self.definition)


class Interaction(Base):
    """Records of interactions with Glossary Bot"""

    __tablename__ = "interactions"
    # Columns
    id = Column(types.Integer, primary_key=True)
    creation_date = Column(types.DateTime(), default=datetime.utcnow)
    user_name = Column(types.Unicode(255))
    term = Column(LimitedLengthUnicode(255))
    action = Column(types.UnicodeText, index=True)

    def __repr__(self):
        return "<Action: {}, Date: {}>".format(self.action, self.creation_date)
