import pytest
import re

from tests.models import Products
from tests.conftest import validate_sql
from sqlalchemy_zdb import ZdbQuery
from sqlalchemy_zdb.utils import query_to_sql
from sqlalchemy_zdb.exceptions import InvalidParameterException


def test_like(dbsession):
    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.short_summary.like("device"))
    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'short_summary:"device"'
    """) is True

    results = q.all()
    assert len(results) == 1
    assert "device" in results[0].short_summary


def test_like_regexp(dbsession):
    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.long_description.like(re.compile(r"c[a-z]pable")))
    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'long_description:~"c[a-z]pable"'
        """) is True

    results = q.all()
    assert len(results) == 1
    assert "capable" in results[0].long_description
