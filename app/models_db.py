from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

user_kb = Table(
    'user_kb',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('kb_id', Integer, ForeignKey('knowledge_bases.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    kbs = relationship("KnowledgeBase", secondary=user_kb, back_populates="authorized_users")

class KnowledgeBase(Base):
    __tablename__ = 'knowledge_bases'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), default='')
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User")
    authorized_users = relationship("User", secondary=user_kb, back_populates="kbs")

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    kb_id = Column(Integer, ForeignKey('knowledge_bases.id'))
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)

class QueryLog(Base):
    __tablename__ = 'query_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    kb_id = Column(Integer, ForeignKey('knowledge_bases.id'))
    question = Column(Text)
    answer_snippet = Column(Text)
    time = Column(DateTime, default=datetime.datetime.utcnow)