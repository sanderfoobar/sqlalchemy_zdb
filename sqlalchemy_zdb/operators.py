import operator

from sqlalchemy.sql.operators import match_op, like_op, between_op


def zdb_between_op(left, right, *args, **kwargs):
    """
    (incorrectly) implements the BETWEEN operator for ZomboDB.

    The ZomboDB documentation states:

        `/to/`
        range query, in form of field:START /to/ END

        https://github.com/zombodb/zombodb/blob/master/SYNTAX.md#operators

    Could not get it to work. Instead made it return:

        column >= :value_1 and column <= :value_2
    """
    # @TODO: implement /to/
    sql = ""
    for i, clause in enumerate(right.clauses):
        _oper = [COMPARE_OPERATORS[operator.ge],
                 COMPARE_OPERATORS[operator.le]][i % 2]
        sql += "%s%s%s%s" % (left.name, _oper, clause.value, "" if i % 2 else " and ")
    return sql


COMPARE_OPERATORS = {
    operator.gt: " > ",
    operator.lt: " < ",
    operator.ge: " >= ",
    operator.le: " <= ",
    operator.ne: " != ",
    match_op: ":@",
    like_op: ":~",
    operator.eq: ":",
    between_op: zdb_between_op
}