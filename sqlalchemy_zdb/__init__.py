from sqlalchemy.sql.elements import BindParameter, TextClause
from sqlalchemy.sql.expression import (
    BooleanClauseList, BinaryExpression, FunctionElement)
from sqlalchemy.sql.annotation import AnnotatedColumn
from sqlalchemy.orm.query import Query
from sqlalchemy import Column, and_


class ZdbColumn(Column):
    def __init__(self, *args, **kwargs):
        super(ZdbColumn, self).__init__(*args, **kwargs)


def zdb_make_query(q):
    """
    SQLAlchemy query -> SQLAchemy query with zdb
    :param q: ``sqlalchemy.orm.query``
    :return: ``sqlalchemy.orm.query``
    """
    _q = q.session.query(*q.whereclause._from_objects)
    expressions = _zdb_reflect_query(q)

    expr_by_column_type = lambda cls: [expr for expr in expressions \
                                       if isinstance(next(iter(expr.left.base_columns)), cls)]

    _zdb_expressions = expr_by_column_type(cls=ZdbColumn)
    if len(_zdb_expressions) == 1:
        _q = _q.filter(zdb_query(_zdb_expressions[0]))
    elif len(_zdb_expressions) > 1:
        _q = _q.filter(zdb_query(and_(*_zdb_expressions)))
    else:
        pass  # @TODO: perhaps give out a warning

    for expr in expr_by_column_type(cls=Column):
        _q = _q.filter(expr)

    return _q


def _zdb_reflect_query(q, _data=[]):
    """
    SQLAchemy query reflector. Parses expressions.
    :param q: ``sqlalchemy.orm.query``
    :param _data:
    :return: list of expressions
    """
    if isinstance(q, BooleanClauseList):
        clauses = q
    elif isinstance(q, Query):
        if q.whereclause is None:
            return []

        clauses = q.whereclause.clauses
    else:
        raise Exception("Unsupported query")

    for i, c in enumerate(clauses):
        if isinstance(c, BindParameter) and isinstance(c.value, str):
            raise Exception("BindParameter ... ehh")  #return c.value
        elif isinstance(c, TextClause):
            raise Exception("TextClause not supported")  #return c.text
        elif isinstance(c, BinaryExpression):
            if not isinstance(c.left, AnnotatedColumn):
                raise Exception("Unsupported clause")
            _data.append(c)
        elif isinstance(c, BooleanClauseList):
            _data = _zdb_reflect_query(c, _data)
        elif isinstance(c, Column):
            raise Exception("ColumnClause not supported")  #return compile_column_clause(c, compiler, tables, format_args)
    return _data


class zdb_score(FunctionElement):
    name = 'zdb_score'


class zdb_query(FunctionElement):
    name = 'zdb_query'


class ZdbPhrase(object):
    def __init__(self, phrase):
        self.phrase = phrase.strip('"')

    def __str__(self):
        return '"%s"' % self.phrase

from sqlalchemy_zdb.compiler import compile_zdb_query
