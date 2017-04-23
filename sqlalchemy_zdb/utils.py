from sqlalchemy.sql import compiler
from psycopg2.extensions import adapt as sqlescape


def query_to_sql(q):
    r"""SQL as string
    :param query: ``sqlalchemy.orm.query``
    :return: SQL as string
    """
    dialect = q.session.bind.dialect
    comp = compiler.SQLCompiler(dialect, query.statement)
    comp.compile()
    params = {}

    if hasattr(comp.params, "items"):
        _items = comp.params.items
    else:
        _items = comp.params.iteritems

    for k, v in _items:
        params[k] = sqlescape(v)
    return comp.string % params
