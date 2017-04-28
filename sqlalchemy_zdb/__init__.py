from typing import List

from sqlalchemy.sql.elements import BindParameter, TextClause
from sqlalchemy.sql.expression import (
    BooleanClauseList, BinaryExpression, FunctionElement, UnaryExpression, ColumnElement)
from sqlalchemy.sql.annotation import AnnotatedColumn
from sqlalchemy.orm.query import Query
from sqlalchemy import Column, and_, func, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.scoping import scoped_session, Session

from sqlalchemy_zdb.types import ZdbColumn, ZdbScore


class ZdbQuery(Query):
    def __init__(self, entities, session=None):
        if isinstance(session, scoped_session):
            session = session()
        elif not isinstance(session, Session):
            raise Exception("Invalid session object")

        super(ZdbQuery, self).__init__(entities, session=session)
        self._zdb_data = {
            "filter": [],
            "order": [],
            "offset": 0,
            "limit": None
        }

    def _zdb_check_session(self):
        if not self.session:
            raise Exception("Session not set")

    def _zdb_compile(self):
        self = self._zdb_make_query()
        return self.statement.compile(dialect=postgresql.dialect())

    @staticmethod
    def _zdb_clauses_by_column(clauses: List[ColumnElement]):
        """Filters a list of expressions based on column types"""
        _rtn = {"zdb": [], "sqla": []}
        if not clauses: return _rtn

        for expr in clauses:
            if isinstance(expr, ZdbScore):
                # LIMIT with ZdbScore
                _rtn["zdb"].append(expr)
                continue
            elif isinstance(expr, UnaryExpression):
                # regular ORDER_BY/DISTINCT
                _columns = expr.element.base_columns
            else:
                # regular expression (no, not regex ;)
                _columns = expr.left.base_columns

            if type(next(iter(_columns))) == ZdbColumn:
                _rtn["zdb"].append(expr)
            else:
                _rtn["sqla"].append(expr)
        return _rtn

    @staticmethod
    def _zdb_reflect(clauses: list, _data=None):
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
                _data = ZdbQuery._zdb_reflect(c, _data)
            elif isinstance(c, Column):
                raise Exception(
                    "ColumnClause not supported")  # return compile_column_clause(c, compiler, tables, format_args)
        return _data

    def _zdb_make_query(self):
        had_zdb_order = False
        exprs = self._zdb_clauses_by_column(self._zdb_reflect(self._zdb_data["filter"]))
        order = self._zdb_clauses_by_column(self._zdb_data["order"])

        # insert zdb filters
        if len(exprs.get("zdb", 0)) >= 1:
            _order = {}
            if order.get("zdb"):
                # needed later to ignore sqla limit/offset
                had_zdb_order = True

                # only ORDER_BY on one column in a zdb query
                _order_clause = order["zdb"].pop(0)
                _order = {
                    "order_by": _order_clause,
                    "limit": self._zdb_data["limit"],
                    "offset": self._zdb_data["offset"]
                }

                # prepend a 'zdb_score()' to sqla ORDER_BY when using #limit(_score, ...)
                if isinstance(_order_clause, ZdbScore):
                    table = self.selectable.froms[0].name
                    __order_clause = func.zdb_score(table, text("ctid"))
                    __order_clause = getattr(__order_clause, _order_clause._zdb_direction)()
                    order["sqla"].insert(0, __order_clause)
                else:
                    # prepend regular ORDER_BY to sqla when using #limit(<column_name)
                    order["sqla"].insert(0, _order_clause)

            # append remaining ORDER clauses to sqla
            if order.get("zdb"):
                order.get("sqla").append(*order["zdb"])

            self = super(ZdbQuery, self).filter(zdb_raw_query(*exprs.get("zdb"), **_order))

        # insert remaining sqla filters
        for expr in exprs.get("sqla", []):
            self = super(ZdbQuery, self).filter(expr)

        # insert remaining sqla order_by
        if order.get("sqla"):
            self = super(ZdbQuery, self).order_by(*order["sqla"])

        if not had_zdb_order:
            # insert sqla limit/offset
            if self._zdb_data.get("limit"):
                self = super(ZdbQuery, self).limit(self._zdb_data.get("limit"))
            if self._zdb_data.get("offset"):
                self = super(ZdbQuery, self).offset(self._zdb_data.get("offset"))

        return self

    def filter(self, *criterion):
        if criterion:
            self._zdb_data["filter"].append(*criterion)
        return self

    def limit(self, value: int):
        self._zdb_data["limit"] = value
        return self

    def offset(self, value: int):
        self._zdb_data["offset"] = value
        return self

    def order_by(self, *criterion: List[UnaryExpression]):
        for order in criterion:
            self._zdb_data["order"].append(order)
        return self

    def all(self):
        self = self._zdb_make_query()
        return super(ZdbQuery, self).all()


class zdb_score(FunctionElement):
    name = 'zdb_score'


class zdb_raw_query(FunctionElement):
    name = 'zdb_query'

    def __init__(self, *criterion, order_by=None, offset=0, limit=None):
        super(zdb_raw_query, self).__init__(*criterion)
        self._zdb_order_by = order_by
        self._zdb_limit = limit
        self._zdb_offset = offset


from sqlalchemy_zdb.compiler import compile_zdb_query
