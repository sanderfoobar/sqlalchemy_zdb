import inspect
import operator

from sqlalchemy import Column
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.annotation import AnnotatedColumn
from sqlalchemy.sql.elements import (
    BinaryExpression, BindParameter, TextClause, BooleanClauseList)

from sqlalchemy_zdb import zdb_query, zdb_score
from sqlalchemy_zdb.operators import COMPARE_OPERATORS


def compile_binary_clause(c, compiler, tables, format_args):
    left = c.left
    right = c.right

    if not isinstance(left, AnnotatedColumn):
        raise ValueError('Incorrect field')

    _oper = COMPARE_OPERATORS.get(c.operator, None)
    if _oper is None:
        raise ValueError('Unsupported binary operator %s' % c.operator)

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
        _oper = ' or '
    elif c.operator == operator.and_:
        _oper = ' and '
    else:
        raise ValueError('Unsupported boolean clause')

    return '(%s)' % _oper.join(query)


def compile_column_clause(c, compiler, tables, format_args):
    format_args.append('replace(%s, \'"\', \'\')' % compiler.process(c))
    return '"%%s"'


def compile_clause(c, compiler, tables, format_args):
    if isinstance(c, BindParameter) and isinstance(c.value, str):
        return c.value
    elif isinstance(c, TextClause):
        return c.text
    elif isinstance(c, BinaryExpression):
        return compile_binary_clause(c, compiler, tables, format_args)
    elif isinstance(c, BooleanClauseList):
        return compile_boolean_clause_list(c, compiler, tables, format_args)
    elif isinstance(c, Column):
        return compile_column_clause(c, compiler, tables, format_args)

    raise ValueError('Unsupported clause')


@compiles(zdb_query)
def compile_zdb_query(element, compiler, **kw):
    query = []
    tables = set()
    format_args = []

    for i, c in enumerate(element.clauses):
        add_to_query = True

        if isinstance(c, BinaryExpression):
            tables.add(c.left.table.name)
        elif isinstance(c, BindParameter):
            if isinstance(c.value, str):
                pass
            elif isinstance(c.value, DeclarativeMeta):
                if i > 0:
                    raise ValueError('Table can be specified only as first param')
                tables.add(c.value.__tablename__)
                add_to_query = False
        elif isinstance(c, BooleanClauseList):
            pass
        elif isinstance(c, Column):
            pass
        else:
            raise ValueError('Unsupported filter')

        if add_to_query:
            query.append(compile_clause(c, compiler, tables, format_args))

    if not tables:
        raise ValueError('No filters passed')
    elif len(tables) > 1:
        raise ValueError('Different tables passed')
    else:
        table = tables.pop()

    if format_args:
        return 'zdb(\'%s\', ctid) ==> format(\'%s\', %s)' % (table, ' and '.join(query), ', '.join(format_args))
    return 'zdb(\'%s\', ctid) ==> \'%s\'' % (table, ' and '.join(query))


@compiles(zdb_score)
def compile_zdb_score(element, compiler, **kw):
    clauses = list(element.clauses)
    if len(clauses) != 1:
        raise ValueError('Incorrect params')

    c = clauses[0]
    if isinstance(c, BindParameter) and isinstance(c.value, DeclarativeMeta):
        return 'zdb_score(\'%s\', %s.ctid)' % (c.value.__tablename__, c.value.__tablename__)

    raise ValueError('Incorrect param')



