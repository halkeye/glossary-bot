from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column
from sqlalchemy.types import Integer, DateTime, Unicode, UnicodeText

Base = declarative_base()

class Definition(Base):
    ''' Records of term definitions, along with some metadata
    '''
    __tablename__ = 'definitions'
    # Columns
    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(), default=datetime.utcnow)
    term = Column(Unicode(255), index=True)
    definition = Column(UnicodeText)
    user_name = Column(Unicode(255))

    def __repr__(self):
        return '<Term: {}, Definition: {}>'.format(self.term, self.definition)

class Interaction(Base):
    ''' Records of interactions with Glossary Bot
    '''
    __tablename__ = 'interactions'
    # Columns
    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(), default=datetime.utcnow)
    user_name = Column(Unicode(255))
    term = Column(Unicode(255))
    action = Column(UnicodeText, index=True)

    def __repr__(self):
        return '<Action: {}, Date: {}>'.format(self.action, self.creation_date)
