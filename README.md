SQLAlchemy support for ZomboDb
=============================

**Experimental** support for the ZomboDB query language with SQLAlchemy. Hard fork of [sqla_zdb](https://github.com/xxxbobrxxx/sqlalchemy_zombodb).

Please check out [Query Syntax](https://github.com/skftn/sqlalchemy_zdb/blob/master/QUERY_SYNTAX.md) for an example of supported expressions. 


## What you need

Product       | Version 
---           | ---      
Postgres      | 9.5
Elasticsearch | 1.7.1+ (not 2.0)
Python        | 3.5+
ZomboDB       | 3.1.12


## Quick Example

Example SQL table:

```sql
CREATE TABLE products (
    id SERIAL8 NOT NULL PRIMARY KEY,
    name text NOT NULL,
    keywords varchar(64)[],
    short_summary phrase,
    long_description fulltext, 
    price bigint,
    inventory_count integer,
    discontinued boolean default false,
    availability_date date,
    author varchar(32)
);
```

SQLAlchemy model:

```python
from sqlalchemy_zdb.types import PHRASE, FULLTEXT, ZdbColumn

class Products(base):
    __tablename__ = "products"

    id = Column(BIGINT, nullable=False, primary_key=True)
    name = Column(Unicode(), nullable=False)
    keywords = Column(ARRAY(Unicode(64)))
    short_summary = ZdbColumn(PHRASE())
    long_description = ZdbColumn(FULLTEXT(41))
    price = ZdbColumn(BIGINT())
    inventory_count = Column(Integer())
    discontinued = Column(Boolean(), default=False)
    availability_date = Column(DateTime())
    author = ZdbColumn(Unicode(32))
```

- `ZdbColumn` - Explicitly mark columns that are included in the ZomboDB index
- `FULLTEXT` - A zomboDB specific type
- `PHRASE` - A ZomboDB specific type

`session.metadata.create_all()` correctly creates this table. It also adds the ZomboDB index.

## Querying 

`ZdbQuery` inherits from `sqlalchemy.orm.session.Query` and you may use it as such.

```python
from sqlalchemy_zdb import ZdbQuery
session = scoped_session(sessionmaker(...))

q = ZdbQuery(Products, session=session)
q = q.filter(Products.name == "foo")
q = q.filter(Products.author.like("bar"))
q = q.filter(Products.price.between(5, 10))
q = q.filter(Products.discontinued == False)

results = q.all()
```

```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'author:"bar" and price:5 /to/ 10' AND
products.name = 'foo' AND products.discontinued = false
```

Note that both the `name` and `discontinued` columns were not included in the ZomboDB query, instead they appear as valid PgSQL. This is because they were not of type `ZdbColumn` during query compilation. 

## Word to the wise

This extension is currently in alpha. If you decide to use this package, double check if the SQL queries generated are correct. Upon weird behaviour please submit an issue so I can look into it.

## Syntax

### EQUALS

```python
q = q.filter(Products.author == "foo bar")
```

```sql
SELECT [...] FROM products
WHERE zdb('products', ctid) ==> 'author:"foo bar"'
```

### GT/LT

```python
q = q.filter(Products.price > 5)
```
```sql
SELECT [...] FROM products
WHERE zdb('products', ctid) ==> 'price > 5'
```

### BETWEEN
```python
q = q.filter(Products.price.between(5, 14.5))
```

```sql
SELECT [...] FROM products
WHERE zdb('products', ctid) ==> 'price:5 /to/ 14.5'
```

### LIKE

```python
q = q.filter(Products.author.like("foo"))
```
```sql
SELECT [...] FROM products
WHERE zdb('products', ctid) ==> 'author:"foo bar"'
```

When passed a regex object, produces the expression: `column:~"foo[a-z]"`
```python
q = q.filter(Products.author.like(re.compile("foo[a-z]")))
```
```sql
SELECT [...] FROM products
WHERE zdb('products', ctid) ==> 'author:~"foo[a-z]"'
```

### more_like_this
```python
q = q.filter(Products.author.match("foo"))
```

```sql
SELECT [...] FROM products
WHERE zdb('products', ctid) ==> 'author:@"foo"'
```

### IN
```python
q = q.filter(Products.author.in_(["foo", "bar"]))
```

```sql
SELECT [...] FROM products
WHERE zdb('products', ctid) ==> 'author:("foo","bar")'
```

### #LIMIT

ZomboDB allows you to limit the number of rows that are returned from a text query, which is similar to Postgres' `SQL-level ORDER BY LIMIT OFFSET` clauses, but can be drastically more efficient because less data is being passed around between Elasticsearch and Postgres.

Syntax:

```
#limit(sort_field asc|desc, offset_val, limit_val)
```
E.g:
```sql
SELECT [...] FROM table
    WHERE zdb('table', ctid) ==> '#limit(price asc, 0, 10) ....'
ORDER BY author_name ASC;
```

In order to construct such a query in SQLAlchemy, the query object must receive:


1. A limit using `limit()`
2. A `ZdbColumn` or `ZdbScore` using `order_by()`

Example #1 - using a column marked as `ZdbColumn` (*Products.price*)

```python
q = q.filter(Products.author.in_(["foo", "bar"]))
q = q.order_by(Products.price.desc(),
               Products.availability_date.desc()).limit(1).offset(1)
```

```sql
SELECT [...] FROM products
    WHERE zdb('products', ctid) ==> '#limit(price desc, 1, 1) author:("foo","bar")'
ORDER BY products.price DESC, products.availability_date DESC
```

In other words, if you were previously already using `limit()` in conjunction with `order_by()` in your query building and the subject column is of type `ZdbColumn`, it'll try to bake a proper query for it.

Example #2 - using `ZdbScore`

```python
from sqlalchemy_zdb.types import ZdbScore

q = q.filter(Products.author.in_(["foo", "bar"]))
q = q.order_by(ZdbScore("asc"),
               Products.availability_date.desc(),
               Products.long_description.desc())
q = q.limit(1)
q = q.offset(1)
```

```sql
SELECT [...] FROM products
    WHERE zdb('products', ctid) ==> '#limit(_score asc, 1, 1) author:("foo","bar")'
ORDER BY zdb_score('products', ctid) ASC, products.availability_date DESC, products.long_description DESC
```

More can be read about `#limit` in the [ZomboDB documentation](https://github.com/zombodb/zombodb/blob/master/SYNTAX.md#limitoffset-with-sorting).

## Constructing filters
If you want to have more control over your query, you may use `zdb_raw_query` directly.

Phrase query:

    from sqlalchemy_zdb import zdb_raw_query, ZdbPhrase

    session.query(Post.text)\
        .filter(zdb_raw_query(Post.text == 'hey joe'))


    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'text:"hey joe"'

Boolean query:

    pg_session.query(Post.text)\
        .filter(zdb_raw_query(or_(Post.text == 'foo', and_(Post.text == 'bar', Post.text == 'fuzz'))))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> '(text:"foo" or (text:"bar" and text:"fuzz"))'

more\_like\_this:

    pg_session.query(Post.text)\
        .filter(zdb_raw_query(Post.text.match('foo')))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'text:@foo'

Comparison operations:

    pg_session.query(Post.text)\
        .filter(zdb_raw_query(Post.comments > 1))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'comments > 1'

Raw query:

    pg_session.query(Post.text)\
        .filter(zdb_raw_query(Post, 'text:(sports,box) or long_description:(wooden w/5 away) and comments < 10'))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'text:(sports,box) or long_description:(wooden w/5 away) and comments < 10'
