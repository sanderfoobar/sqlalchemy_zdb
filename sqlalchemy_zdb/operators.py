import re
import operator

from sqlalchemy.sql.operators import match_op, like_op, between_op


def zdb_between_op(left, right, *args, **kwargs):
    r"""(incorrectly) implement the BETWEEN operator.

    The ZomboDB documentation states:

        `/to/`
        range query, in form of field:START /to/ END

        https://github.com/zombodb/zombodb/blob/master/SYNTAX.md#operators

    Could not get it to work. Instead made it return::

        column >= 5 and column <= 15

    E.g.::

        stmt = select([sometable]).\
            where(sometable.c.column.between(5, 15))

    Only works on integers.
    @TODO: implement /to/
    """
    sql = ""
    for i, clause in enumerate(right.clauses):
        if not isinstance(clause.value, int):
            raise Exception("Unsupported use of BETWEEN, only integers allowed")

        _oper = [COMPARE_OPERATORS[operator.ge],
                 COMPARE_OPERATORS[operator.le]][i % 2]
        sql += "%s%s%d%s" % (left.name, _oper, int(clause.value), "" if i % 2 else " and ")
    return sql


def zdb_like_op(left, right, c, compiler, tables, format_args):
    r"""Implement the ``like`` operator.

    In a normal context, produces the expression::

        column:"foo"

    E.g.::

        stmt = select([sometable]).\
            where(sometable.c.column.like("foo"))


    In a regex context, produces the expression::

        column:~"foo[a-z]"

    E.g.::

        stmt = select([sometable]).\
            where(sometable.c.column.like(re.compile("foo[a-z]")))
    """
    from sqlalchemy_zdb.compiler import compile_clause

    if isinstance(right.value, re._pattern_type):
        _oper = ":~"
        right.value = right.value.pattern
    else:
        _oper = ":"

    return "%s%s%s" % (left.name, _oper, compile_clause(right, compiler, tables, format_args))

COMPARE_OPERATORS = {
    operator.gt: " > ",
    operator.lt: " < ",
    operator.ge: " >= ",
    operator.le: " <= ",
    operator.ne: " != ",
    match_op: ":@",
    like_op: zdb_like_op,
    operator.eq: ":",
    between_op: zdb_between_op
}