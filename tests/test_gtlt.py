from tests.models import Products
from tests.conftest import validate_sql
from sqlalchemy_zdb import ZdbQuery
from sqlalchemy_zdb.utils import query_to_sql


def test_greater(dbsession):
    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price > 8900)

    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'price > 8900'
    """) is True

    results = q.all()
    assert len(results) == 2
    assert results[0].price == 9900
    assert results[1].price == 17000


def test_greater_or_eq(dbsession):
    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price >= 17000)

    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'price >= 17000'
        """) is True

    results = q.all()
    assert len(results) == 1
    assert results[0].price == 17000

    #

    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price >= 1899)
    q = q.filter(Products.inventory_count >= 50)

    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'price >= 1899' AND products.inventory_count >= 50
    """) is True

    results = q.all()
    assert len(results) == 1
    assert results[0].price == 1899


def test_lower(dbsession):
    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price < 8900)
    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'price < 8900'
    """) is True

    results = q.all()
    assert len(results) == 2
    assert results[0].id == 2
    assert results[1].id == 3


def test_lower_than(dbsession):
    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price <= 1500)
    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'price <= 1500'
    """) is True

    results = q.all()
    assert len(results) == 1
    assert results[0].id == 2

    #

    q = ZdbQuery(Products, session=dbsession)

    q = q.filter(Products.price <= 10000)
    q = q.filter(Products.inventory_count <= 50)

    sql = query_to_sql(q)
    assert validate_sql(sql, target="""
SELECT products.id, products.name, products.keywords, products.short_summary, products.long_description, products.price, products.inventory_count, products.discontinued, products.availability_date, products.author
FROM products
WHERE zdb('products', ctid) ==> 'price <= 10000' AND products.inventory_count <= 50
    """) is True

    results = q.all()
    assert len(results) == 2
    assert results[0].id == 1
