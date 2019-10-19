#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from sqlalchemy import create_engine, MetaData, Table, DateTime, Date, Time
from datetime import datetime as cdatetime, date, time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, class_mapper
from contextlib import contextmanager
from models import Command, Base

engine = create_engine("mysql+pymysql://admin:admin@localhost:3306/sqlalchemy?charset=utf8mb4", encoding="utf-8", echo=False)
Base.metadata.create_all(engine)

class CommandSession(object):

    def __init__(self, engine=engine):
        self.engine = engine
        self.SessionType = scoped_session(sessionmaker(bind=self.engine, expire_on_commit=False))
        self.table = Command

    def getSession(self):
        return self.SessionType()

    def getTable(self, name):
        return Table(name, MetaData(self.engine), autoload=True)

    @contextmanager
    def session_scope(self):
        session = self.getSession()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def getAllCommand(self):
        with self.session_scope() as session:
            # orm 方式, 无论什么情况，使用 ORM 查询都要慢得多
            # result =  session.query(self.table).all()
            # for item in result:
                # yield self.serialize_orm(item)

            # SQLAlchemyCore
            result_proxy = session.execute(self.table.__table__.select())
            return self.serialize_core(result_proxy)

    def insertCommand(self, **kws):
        with self.session_scope() as session:
            # session.add(self.table(**kws))

            # print(self.table.__table__.insert())
            result_proxy = session.execute(self.table.__table__.insert(), kws)
            return result_proxy.lastrowid

    def updateCommand(self, id=None, **columns):
        with self.session_scope() as session:
            # return session.query(self.table).filter(self.table.id == id).update(columns)
            print(id, columns)
            return session.execute(self.table.__table__.update().where(self.table.id == id).values(**columns))

    def deleteCommand(self, id=None):
        with self.session_scope() as session:
            # return session.query(self.table).filter(self.table.id == id).delete()
            return session.execute(self.table.__table__.delete().where(self.table.id == id))

    def deleteAllCommand(self, id=None):
        with self.session_scope() as session:
            # return session.query(self.table).filter().delete()
            return session.execute(self.table.__table__.delete().where())

    def serialize_orm(self, model):
        # print(model.__table__.columns)
        columns = [(col.name, col.type) for col in class_mapper(model.__class__).columns]
        result = {}
        for col_name, col_type in columns:
            if isinstance(col_type, DateTime):
                result[col_name] = self.convert_datetime(getattr(model, col_name))
            else:
                result[col_name] = getattr(model, col_name)
        return result

    def serialize_core(self, result_proxy):
        # print(type(session.table.__table__.columns["time"].type))
        columns = result_proxy.keys()
        for row in result_proxy:
            yield dict(zip(columns, row))

    def convert_datetime(self, value):
        if value:
            if(isinstance(value,(cdatetime,DateTime))):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            elif(isinstance(value,(date,Date))):
                return value.strftime("%Y-%m-%d")
            elif(isinstance(value,(Time,time))):
                return value.strftime("%H:%M:%S")
        else:
            return ""

    def group_by_name(self, col_name):
        with self.session_scope() as session:
            result =  session.query(self.table).group_by(getattr(self.table, col_name)).all()
            for item in result:
                yield self.serialize_orm(item)[col_name]

    def select_by_id(self, id):
        with self.session_scope() as session:
            result =  session.query(self.table).filter(self.table.id == id).first()
            return self.serialize_orm(result)


if __name__ == "__main__":
    session = CommandSession()
    # for row in session.getAllCommand():
    #     print(row)
    lastrowid = session.insertCommand(code="test1", description="test2", author="test3", category="44")
    session.updateCommand(id=lastrowid, code="update_test")
    print(session.select_by_id(id=lastrowid))
    session.deleteCommand(id=lastrowid)
