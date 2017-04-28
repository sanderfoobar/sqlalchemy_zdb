from sqlalchemy.orm.session import Session

from tests.models import Products
from tests.conftest import validate_sql
from sqlalchemy_zdb import ZdbQuery
from sqlalchemy_zdb.utils import query_to_sql


def test_db_essentials(dbsession):
    assert isinstance(dbsession, Session)
    q = ZdbQuery(Products, session=dbsession)
    assert isinstance(q, ZdbQuery)


def test_equals_1(dbsession):
    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.author == "foo")

    sql = query_to_sql(q)
    assert validate_sql(sql=sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'author:foo'
    """) is True

    results = q.all()
    assert len(results) == 2
    assert results[0].author == "foo"
