from sqlalchemy.sql.elements import BindParameter, TextClause
from sqlalchemy.sql.expression import (
    BooleanClauseList, BinaryExpression, FunctionElement)
from sqlalchemy.sql.annotation import AnnotatedColumn
from sqlalchemy.orm.query import Query
from sqlalchemy import Column, and_

from sqlalchemy.orm.scoping import scoped_session, Session
from sqlalchemy_zdb.utils import print_sql


class ZdbQuery(Query):
    def __init__(self, entities, session=None):
        if isinstance(session, scoped_session):
            session = session()
        elif not isinstance(session, Session):
            raise Exception("Invalid session object")

        super(ZdbQuery, self).__init__(entities, session=session)
        self._zdb_expressions = []
        self._zdb_limit = None
        self._zdb_offset = None

    def _zdb_check_session(self):
        if not self.session:
            raise Exception("Session not set")

    @staticmethod
    def _zdb_get_columns(expressions, column_type):
        return [expr for expr in expressions if \
                type(next(iter(expr.left.base_columns))) == column_type]

    def _zdb_reflect_query(self, clauses, _data=None):
        if not _data:
            _data = []

        for i, c in enumerate(clauses):
            if isinstance(c, zdb_raw_query):
                raise Exception("ZdbQuery not compatible with direct "
                                "useage of zdb_raw_query()")
            elif isinstance(c, BindParameter) and isinstance(c.value, str):
                raise Exception("BindParameter ... ehh")  # return c.value
            elif isinstance(c, TextClause):
                raise Exception("TextClause not supported")  # return c.text
            elif isinstance(c, BinaryExpression):
                if not isinstance(c.left, AnnotatedColumn):
                    raise Exception("Unsupported clause")
                _data.append(c)
            elif isinstance(c, BooleanClauseList):
                _data = self._zdb_reflect_query(c, _data)
            elif isinstance(c, Column):
                raise Exception(
                    "ColumnClause not supported")  # return compile_column_clause(c, compiler, tables, format_args)
        return _data

    def _zdb_make_query(self):
        exprs = self._zdb_reflect_query(self._zdb_expressions)
        expr_zdb = self._zdb_get_columns(exprs, ZdbColumn)
        expr_sqla = self._zdb_get_columns(exprs, Column)

        # insert zdb filters
        if len(expr_zdb) >= 1:
            self = super(ZdbQuery, self).filter(zdb_raw_query(*expr_zdb))

        # insert sqla filters
        for expr in expr_sqla:
            self = super(ZdbQuery, self).filter(expr)

        # insert limit/offset
        if self._zdb_limit:
            self = super(ZdbQuery, self).limit(self._zdb_limit)
        if self._zdb_offset:
            self = super(ZdbQuery, self).offset(self._zdb_offset)

        return self

    def filter(self, *criterion):
        for criter in criterion:
            self._zdb_expressions.append(criter)
        return self

    def limit(self, value):
        self._zdb_limit = value
        return self

    def offset(self, value):
        self._zdb_offset = value
        return self

    def all(self):
        self = self._zdb_make_query()
        return super(ZdbQuery, self).all()


class ZdbColumn(Column):
    def __init__(self, *args, **kwargs):
        super(ZdbColumn, self).__init__(*args, **kwargs)


class zdb_score(FunctionElement):
    name = 'zdb_score'


class zdb_raw_query(FunctionElement):
    name = 'zdb_query'


class ZdbPhrase(object):
    def __init__(self, phrase):
        self.phrase = phrase.strip('"')

    def __str__(self):
        return '"%s"' % self.phrase

from sqlalchemy_zdb.compiler import compile_zdb_query
