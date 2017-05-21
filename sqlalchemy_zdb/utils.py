from __future__ import print_function
from sqlalchemy.sql import compiler
from sqlalchemy import text
from sqlalchemy.sql.sqltypes import ARRAY
from sqlalchemy.dialects.postgresql.psycopg2 import PGCompiler_psycopg2
from psycopg2.extensions import adapt as sqlescape


def _query_to_sql(q):
    r"""SQL as string
    :param q: ``sqlalchemy.orm.query``
    :return: SQL as string
    """
    dialect = q.session.bind.dialect
    comp = compiler.SQLCompiler(dialect, q.statement)
    comp.compile()
    params = {}

    if hasattr(comp.params, "items"):
        _items = comp.params.items
    else:
        _items = comp.params.iteritems

    return comp.string


def query_to_sql(q):
    r"""SQL as string
    :param q: Instance of ZdbQuery
    :return: SQL as string
    """
    from sqlalchemy_zdb import ZdbQuery
    compiled = q._zdb_compile()
    return "\n\n%s\n\n" % compiled % compiled.params


def is_zdb_table(model):
    from sqlalchemy_zdb import ZdbColumn
    for column in model.columns:
        if type(column) == ZdbColumn:
            return True


def get_zdb_columns_as_ddl(model):
    from sqlalchemy_zdb import ZdbColumn

    rtn = []
    json = None
    try:
        from sqlalchemy_utils import JSONType
        json = JSONType
    except ImportError:
        pass

    for column in [column for column in model.columns if isinstance(column, ZdbColumn)]:
        if json and isinstance(column.type, json):
            column_type = "JSONB"
        elif isinstance(column.type, ARRAY):
            _type = column.type.item_type.compile()
            column_type = "%s[]" % _type
        else:
            column_type = column.type.compile()

        rtn.append("%s %s" % (column.name, column_type))
    return ",\n\t".join(rtn)


def has_type(type_name, connection):
    """
    Checks for the presence of a given Postgres type
    :param type_name: name of the type
    :param connection:
    :return: A :class:`sqlalchemy.engine.result.RowProxy` instance if found.
    """
    sql = """
    SELECT
      n.nspname AS schema,
      t.typname AS type
    FROM pg_type t
      LEFT JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    WHERE (t.typrelid = 0 OR (SELECT c.relkind = 'c'
                              FROM pg_catalog.pg_class c
                              WHERE c.oid = t.typrelid))
          AND NOT EXISTS(SELECT 1
                         FROM pg_catalog.pg_type el
                         WHERE el.oid = t.typelem AND el.typarray = t.oid)
          AND n.nspname NOT IN ('pg_catalog', 'information_schema')
          AND t.typname=:type_name;"""
    return connection.execute(text(sql), type_name=type_name).fetchone()


def has_index(table_name, index_name, connection):
    """
    Checks for the presence of a given Postgres index
    :param table_name: name of the table
    :param index_name: name of the index
    :param connection:
    :return: A :class:`sqlalchemy.engine.result.RowProxy` instance.
    """
    sql = """
    SELECT schemaname, tablename, indexname, indexdef FROM pg_indexes
    WHERE tablename = :table_name AND indexname = :index_name;"""
    return connection.execute(text(sql), table_name=table_name, index_name=index_name).fetchone()


def verify_type():
    pass


def verify_index():
    pass
