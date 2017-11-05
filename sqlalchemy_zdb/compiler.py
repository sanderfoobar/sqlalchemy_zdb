import re
import inspect
import operator

import sqlalchemy
from sqlalchemy import Column
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.annotation import AnnotatedColumn
from sqlalchemy.sql.elements import (
    BinaryExpression, BindParameter, TextClause, BooleanClauseList, Grouping,
    False_, True_, UnaryExpression, Null)

from sqlalchemy_zdb import zdb_raw_query, zdb_score
from sqlalchemy_zdb.types import ZdbColumn, ZdbScore, ZdbLiteral
from sqlalchemy_zdb.operators import COMPARE_OPERATORS


def escape_tokens(inp):
    # TODO: figure out how to properly escape characters
    # like `'`, they seem to break up the query. For now
    # replace it.
    _escape_tokens = [
       "'", "\"",  ":",  "*",  "~", "?",
       "!",  "%",  "&",  "(",  ")", ",",
       "<",  "=",  ">",  "[",  "]", "^",
       "{",  "}",  " ",  "\r", "\n",
       "\t", "\f"]
    inp = inp.replace("\'", "")
    for escape_token in _escape_tokens:
        inp = inp.replace(escape_token, "\\%s" % escape_token)
    return inp


def compile_binary_clause(c, compiler, tables, format_args):
    left = c.left
    right = c.right

    if not isinstance(left, AnnotatedColumn):
        raise ValueError("Incorrect field")

    _oper = COMPARE_OPERATORS.get(c.operator, None)
    if _oper is None:
        raise ValueError("Unsupported binary operator %s" % c.operator)

    tables.add(left.table.name)

    if inspect.isfunction(_oper):
        return _oper(left, right, c, compiler, tables, format_args)
    else:
        return '%s%s%s' % (left.name, _oper, compile_clause(right, compiler, tables, format_args))


def compile_boolean_clause_list(c, compiler, tables, format_args):
    query = []

    for _c in c.clauses:
        query.append(compile_clause(_c, compiler, tables, format_args))

    if c.operator == operator.or_:
        _oper = " or "
    elif c.operator == operator.and_:
        _oper = " and "
    else:
        raise ValueError("Unsupported boolean clause")

    return "(%s)" % _oper.join(query)


def compile_column_clause(c, compiler, tables, format_args):
    format_args.append("replace(%s, '\"', '')" % compiler.process(c))
    return "\"%%s\""


def compile_grouping(c, compiler, tables, format_args):
    sql = "(%s)"
    values = []
    for elem in c.element:
        if isinstance(elem.value, str):
            val = "\"%s\"" % elem.value
        elif isinstance(elem.value, int):
            val = str(elem.value)
        else:
            raise Exception("Unsupported type for IN")
        values.append(val)

    return sql % ",".join(values)


def compile_limit(offset: int, limit: int, order_by=None):
    """
    Compiles zdb order/limit/offset . Default
    column to ORDER on is _score which represents
    ES result relevance.

        #limit(sort_field asc|desc, offset_val, limit_val)
    """
    if not isinstance(offset, int) or not isinstance(limit, int):
        raise Exception("Expected int for zdb LIMIT offset and/or limit")

    # dirty hack, UnaryExpression doesnt implement boolean clause comparison
    if type(order_by) == type(None):
        raise Exception("Expected UnaryExpression or ZdbScore for zdb LIMIT")
    if isinstance(order_by, ZdbScore):
        column_name = "_score"
        direction = order_by._zdb_direction
    elif isinstance(order_by, UnaryExpression):
        column = next(iter(order_by.element.base_columns))
        column_name = column.name
        direction = "asc" if order_by.modifier == sqlalchemy.sql.operators.asc_op else "desc"

        if not type(column) == ZdbColumn:
            raise Exception("Expected ZdbColumn for zdb LIMIT")
    else:
        raise Exception("Unexpected expression")

    return "#limit(%s %s, %d, %d) " % (column_name, direction, offset, limit)


def compile_clause(c, compiler, tables, format_args):
    if isinstance(c, BindParameter) and isinstance(c.value, (
            str, int, re._pattern_type, ZdbLiteral)):
        if isinstance(c.value, str):
            return "\"%s\"" % escape_tokens(c.value)
        elif isinstance(c.value, re._pattern_type):
            return "\"%s\"" % c.value.pattern
        elif isinstance(c.value, ZdbLiteral):
            return c.value.literal
        else:
            return c.value
    elif isinstance(c, (True_, False_)):
        return str(type(c) == True_).lower()
    elif isinstance(c, TextClause):
        return c.text
    elif isinstance(c, BinaryExpression):
        return compile_binary_clause(c, compiler, tables, format_args)
    elif isinstance(c, BooleanClauseList):
        return compile_boolean_clause_list(c, compiler, tables, format_args)
    elif isinstance(c, Column):
        return compile_column_clause(c, compiler, tables, format_args)
    elif isinstance(c, Grouping):
        return compile_grouping(c, compiler, tables, format_args)
    elif isinstance(c, Null):
        return "NULL"
    raise ValueError("Unsupported clause")


@compiles(zdb_raw_query)
def compile_zdb_query(element, compiler, **kw):
    query = []
    tables = set()
    format_args = []
    limit = ""

    for i, c in enumerate(element.clauses):
        add_to_query = True

        if isinstance(c, BinaryExpression):
            tables.add(c.left.table.name)
        elif isinstance(c, BindParameter):
            if isinstance(c.value, str):
                pass
            elif isinstance(c.value, DeclarativeMeta):
                if i > 0:
                    raise ValueError("Table can be specified only as first param")
                tables.add(c.value.__tablename__)
                add_to_query = False
        elif isinstance(c, BooleanClauseList):
            pass
        elif isinstance(c, Column):
            pass
        else:
            raise ValueError("Unsupported filter")

        if add_to_query:
            query.append(compile_clause(c, compiler, tables, format_args))

    if not tables:
        raise ValueError("No filters passed")
    elif len(tables) > 1:
        raise ValueError("Different tables passed")
    else:
        table = tables.pop()

    if hasattr(element, "_zdb_order_by") and isinstance(element._zdb_order_by, (UnaryExpression, ZdbScore)):
        limit = compile_limit(order_by=element._zdb_order_by,
                              offset=element._zdb_offset,
                              limit=element._zdb_limit)

    sql = "zdb(\'%s\', ctid) ==> " % table
    if format_args and isinstance(format_args, list):
        sql += "\'%sformat(\'%s\', %s)\'" % (
            limit,
            " and ".join(query),
            ", ".join(format_args)
        )
    else:
        sql += "\'%s%s\'" % (
            limit,
            " and ".join(query))
    return sql


@compiles(zdb_score)
def compile_zdb_score(element, compiler, **kw):
    clauses = list(element.clauses)
    if len(clauses) != 1:
        raise ValueError("Incorrect params")

    c = clauses[0]
    if isinstance(c, BindParameter) and isinstance(c.value, DeclarativeMeta):
        return "zdb_score(\'%s\', %s.ctid)" % (c.value.__tablename__, c.value.__tablename__)

    raise ValueError("Incorrect param")
