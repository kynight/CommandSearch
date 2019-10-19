from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, text, Index
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Command(Base):
    __tablename__ = 'command'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    code = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    author = Column(String(20), nullable=False, server_default="admin")
    category = Column(String(20), nullable=False, server_default="undefined")
    time = Column(DateTime, server_default=text('NOW()'), onupdate=text('NOW()'))

    __table_args__ = (
        Index("ix_category", "category"),
        {
        'mysql_engine': 'MyISAM',
        'mysql_charset': 'utf8mb4'
        })
