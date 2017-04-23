from __future__ import print_function
from sqlalchemy.sql import compiler
from psycopg2.extensions import adapt as sqlescape


def query_to_sql(q):
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


def print_sql(q):
    r"""Print SQL for the query object
    :param q: ``sqlalchemy.orm.query``
    :return:
    """
    print("\n\n%s\n\n" % query_to_sql(q))
