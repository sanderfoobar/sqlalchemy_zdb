import pytest

from tests.models import Products
from tests.conftest import validate_sql
from sqlalchemy_zdb import ZdbQuery
from sqlalchemy_zdb.utils import query_to_sql
from sqlalchemy_zdb.exceptions import InvalidParameterException


def test_between(dbsession):
    # integers
    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price.between(9000, 20000))

    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'price:9000 /to/ 20000'
    """) is True

    results = q.all()
    assert len(results) == 2
    assert results[0].price == 9900
    assert results[1].price == 17000

    # floats

    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price.between(9899.5, 9901.75))

    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'price:9899.5 /to/ 9901.75'
    """) is True

    results = q.all()
    assert len(results) == 1
    assert results[0].price == 9900

    # invalid input

    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price.between(9899.5, "10000"))

    with pytest.raises(InvalidParameterException):
        q.all()
