import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
from sqlalchemy.engine.url import URL
import os
import dsnparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

SqlAlchemyBase = dec.declarative_base()

__factory = None
r = dsnparse.parse_environ('POSTGRES_CONN')
DATABASE = {
    'drivername': 'postgresql+psycopg2',
    'host': f'{r.hostloc.split(":")[0]}',
    'port': f'{r.hostloc.split(":")[1]}',
    'username': f'{r.username}',
    'password': f'{r.password}',
    'database': f'{r.paths[0]}',
    'query': {}
}

engine = sa.create_engine(URL(**DATABASE))

def global_init():
    global __factory

    if __factory:
        return
    
    
    __factory = orm.sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    from data import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()