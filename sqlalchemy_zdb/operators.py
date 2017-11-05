import re
import operator

from sqlalchemy.sql.operators import match_op, like_op, between_op, in_op, isnot

from sqlalchemy_zdb.exceptions import InvalidParameterException


def zdb_between_op(left, right, *args, **kwargs):
    r"""Implement the ``BETWEEN`` operator.

    E.g.::

        stmt = select([sometable]).\
            where(sometable.c.column.between(5, 14.5))
    """
    between = []
    for i, clause in enumerate(right.clauses):
        if not isinstance(clause.value, (int, float)):
            raise InvalidParameterException("Numbers only")
        between.append(clause.value)
    return "{}:{} /to/ {}".format(left.name, *between)


def zdb_like_op(left, right, c, compiler, tables, format_args):
    r"""Implement the ``LIKE`` operator.

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
    else:
        _oper = ":"

    return "%s%s%s" % (left.name, _oper, compile_clause(right, compiler, tables, format_args))


def zdb_in_op(left, right, c, compiler, tables, format_args):
    r"""Implement the ``IN`` operator."""
    from sqlalchemy_zdb.compiler import compile_clause

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
    between_op: zdb_between_op,
    in_op: zdb_in_op,
    isnot: " != "
}
