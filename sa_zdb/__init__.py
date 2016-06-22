import operator

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.annotation import AnnotatedColumn
from sqlalchemy.sql.elements import BinaryExpression, BindParameter, BooleanClauseList, TextClause
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.sql.operators import match_op, like_op


COMPARE_OPERATORS = {
    operator.gt: ' > ',
    operator.lt: ' < ',
    operator.ge: ' >= ',
    operator.le: ' <= ',
    operator.ne: ' != ',
    match_op: ':@',
    like_op: ':~',
    operator.eq: ':',
}


class ZdbPhrase(object):
    def __init__(self, phrase):
        self.phrase = phrase.strip('"')

    def __str__(self):
        return '"%s"' % self.phrase


def compile_binary_clause(c, tables):
    left = c.left
    right = c.right

    _oper = COMPARE_OPERATORS.get(c.operator, None)
    if _oper is None:
        raise ValueError('Unsupported binary operator %s' % c.operator)

    if not isinstance(right, BindParameter):
        raise ValueError('Incorrect right parameter')
    elif not isinstance(left, AnnotatedColumn):
        raise ValueError('Incorrect field')
    elif not isinstance(right.value, (ZdbPhrase, basestring, int)):
        raise ValueError('Incorrect right parameter')

    tables.add(left.table.name)
    return '%s%s%s' % (left.name, _oper, right.value)


def compile_boolean_clause_list(c, tables):
    query = []

    for _c in c.clauses:
        query.append(compile_clause(_c, tables))

    if c.operator == operator.or_:
        _oper = ' or '
    elif c.operator == operator.and_:
        _oper = ' and '
    else:
        raise ValueError('Unsupported boolean clause')

    return '(%s)' % _oper.join(query)


def compile_clause(c, tables):
    if isinstance(c, BindParameter) and isinstance(c.value, basestring):
        return c.value
    elif isinstance(c, TextClause):
        return c.text
    elif isinstance(c, BinaryExpression):
        return compile_binary_clause(c, tables)
    elif isinstance(c, BooleanClauseList):
        return compile_boolean_clause_list(c, tables)

    raise ValueError('Unsupported clause')


class zdb_query(FunctionElement):
    name = 'zdb_query'


@compiles(zdb_query)
def compile_zdb_query(element, compiler, **kw):
    query = []
    tables = set()

    for i, c in enumerate(element.clauses):
        add_to_query = True

        if isinstance(c, BinaryExpression):
            tables.add(c.left.table.name)
        elif isinstance(c, BindParameter):
            if isinstance(c.value, basestring):
                pass
            elif isinstance(c.value, DeclarativeMeta):
                if i > 0:
                    raise ValueError('Table can be specified only as first param')
                tables.add(c.value.__tablename__)
                add_to_query = False
        elif isinstance(c, BooleanClauseList):
            pass
        else:
            raise ValueError('Unsupported filter')

        if add_to_query:
            query.append(compile_clause(c, tables))

    if not tables:
        raise ValueError('No filters passed')
    elif len(tables) > 1:
        raise ValueError('Different tables passed')
    else:
        table = tables.pop()

    return 'zdb(\'%s\', ctid) ==> \'%s\'' % (table, ' and '.join(query))
