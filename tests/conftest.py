import os

import sqlalchemy_zdb
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import tests.settings as settings
from tests.settings import db_user, db_pass, db_host, db_port, db_name
from tests.models import base
import pytest


cwd = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="session")
def engine():
    return create_engine("postgresql+psycopg2://%s:%s@%s:%d/%s" % (
        db_user, db_pass, db_host, db_port, db_name), echo=True)


@pytest.fixture(scope="session")
def db_extension(engine):
    session = Session(bind=engine.connect())
    db_cleanup(session)

    res = session.execute("""
        SELECT installed_version from pg_available_extensions WHERE name = 'zombodb';
    """).first()

    if not res.installed_version:
        session.execute(text("CREATE EXTENSION zombodb"))
        session.commit()
        session.flush()


@pytest.fixture(scope="session")
def db_composite_type(engine):
    pass


@pytest.yield_fixture(scope="session")
def tables(engine):
    base.metadata.create_all(engine)

    connection = engine.connect()
    session = Session(bind=connection)
    session.execute(text("""COPY products FROM :path"""),
                    params={"path": "%s/data/test-data.dmp" % cwd})
    session.commit()
    session.flush()
    yield
    base.metadata.drop_all(engine)


@pytest.yield_fixture
def dbsession(engine, db_extension, db_composite_type, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    db_cleanup(session)

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()


@pytest.fixture(scope="session")
def db_cleanup(session):
    session.execute(text("""
        DROP SCHEMA public CASCADE;
        CREATE SCHEMA public;
    """
    ))
    session.commit()
    session.flush()


def validate_sql(sql, target):
    sql = sql.strip().replace(" \n", "\n")
    target = target.strip()

    if target == sql:
        return True
