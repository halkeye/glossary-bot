from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import Integer, DateTime, Unicode

Base = declarative_base()

class Definition(Base):
    ''' Records of term definitions, along with some metadata
    '''
    __tablename__ = 'definitions'
    # Columns
    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(), default=datetime.utcnow)
    term = Column(Unicode(), index=True)
    definition = Column(Unicode())
    user_name = Column(Unicode())
    tsv_search = Column(TSVECTOR)

    def __repr__(self):
        return '<Term: {}, Definition: {}>'.format(self.term, self.definition)

class Interaction(Base):
    ''' Records of interactions with Glossary Bot
    '''
    __tablename__ = 'interactions'
    # Columns
    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(), default=datetime.utcnow)
    user_name = Column(Unicode())
    term = Column(Unicode())
    action = Column(Unicode(), index=True)

    def __repr__(self):
        return '<Action: {}, Date: {}>'.format(self.action, self.creation_date)
