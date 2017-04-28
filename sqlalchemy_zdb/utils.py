from __future__ import print_function
from sqlalchemy.sql import compiler
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
