SQLAlchemy support for ZomboDb
=============================

This extension provides **very experimental** support for the ZomboDB query language with the SQLAlchemy ORM.

ZomboDb project: <https://github.com/zombodb/zombodb>

## How to Use It

Usage is really quite simple. Take this example table:

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

The SQLAlchemy equivalent would be:

```python
from sqlalchemy_zdb import ZdbColumn
from sqlalchemy_zdb.types import PHRASE, FULLTEXT

class Products(base):
    __tablename__ = "products"

    id = Column(BIGINT, nullable=False, primary_key=True)
    name = Column(Unicode(), nullable=False)
    keywords = Column(ARRAY(Unicode(64)))
    short_summary = ZdbColumn(PHRASE())
    long_description = ZdbColumn(FULLTEXT(41))
    price = Column(BIGINT())
    inventory_count = Column(Integer()),
    discontinued = Column(Boolean(), default=False)
    availability_date = Column(DateTime())
    author = ZdbColumn(Unicode(32))
```

Any column explicitly marked with `ZdbColumn` will end up in ElasticSearch.

Please note the 2 ZomboDB specific types: `PHRASE` and `FULLTEXT`.

## Querying 
Simply pass the `zdb_make_query` function a SQLAlchemy query object and it will convert it to [ZomboDB syntax](https://github.com/zombodb/zombodb/blob/master/SYNTAX.md).
```python
from sqlalchemy_zdb import zdb_make_query
q = session.query(Products)
q = q.filter(...)
q = zdb_make_query(q)
results = q.all()
```
### Equals

```python
q = q.filter(Products.author == "foo bar")
q = zdb_make_query(q)
```

```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'author:"foo bar"'
```

### gt/lt

```python
q = q.filter(Products.price > 5)
q = zdb_make_query(q)
```
```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'price > 5'
```

### Between
Could not get `field:start /to/ END` work (as per [documentation](https://github.com/zombodb/zombodb/blob/master/SYNTAX.md#operators)), instead made it return:

    column >= 5 and column <= 15

*Warning: Only works on integers.*

```python
q = q.filter(Products.price.between(5, 10))
q = zdb_make_query(q)
```

```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'price >= 5 and price <= 10'
```

### Like

When passed a string, produces the expression: `column:"foo"`
```python
q = q.filter(Products.author.like("foo"))
q = zdb_make_query(q)
```
```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'author:"foo bar"'
```

When passed a regex object, produces the expression: `column:~"foo[a-z]"`
```python
q = q.filter(Products.author.like(re.compile("foo[a-z]")))
q = zdb_make_query(q)
```
```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'author:~"foo[a-z]"'
```

### more_like_this
```python
q = q.filter(Products.author.match("foo"))
q = zdb_make_query(q)
```

```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'author:@"foo"'
```

### Combining filters

Combining multiple filters between regular columns and `ZdbColumn` works as expected:

```python
q = q.filter(Products.name == "foo")
q = q.filter(Products.author.like("bar"))
q = q.filter(Products.price.between(5, 10))
q = q.filter(Products.discontinued == False)
q = zdb_make_query(q)
```

```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'author:"bar" and price >= 5 and price <= 10' AND
products.name = 'foo' AND products.discontinued = false
```

If it does not, please let me know.

## Manually constructing filters
If you want to have more control over your query, you may use `zdb_query` directly.

Phrase query:

    from sqlalchemy_zdb import zdb_query, ZdbPhrase

    session.query(Post.text)\
        .filter(zdb_query(Post.text == 'hey joe'))


    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'text:"hey joe"'

Boolean query:

    pg_session.query(Post.text)\
        .filter(zdb_query(or_(Post.text == 'foo', and_(Post.text == 'bar', Post.text == 'fuzz'))))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> '(text:"foo" or (text:"bar" and text:"fuzz"))'

more\_like\_this:

    pg_session.query(Post.text)\
        .filter(zdb_query(Post.text.match('foo')))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'text:@foo'

Comparison operations:

    pg_session.query(Post.text)\
        .filter(zdb_query(Post.comments > 1))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'comments > 1'

Raw query:

    pg_session.query(Post.text)\
        .filter(zdb_query(Post, 'text:(sports,box) or long_description:(wooden w/5 away) and comments < 10'))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'text:(sports,box) or long_description:(wooden w/5 away) and comments < 10'

## Roadmap

I'm aware that `zdb_make_query` is hacky, if anyone wants to jump in do things the proper way, please do.

As for the roadmap, I'm planning on implementing the following:

- Automatic ZomboDB `CREATE INDEX` and `CREATE TYPE` during `metadata.create_all()`
- Cover more functionality currently present in the ZomboDB API
- Unit tests

## Authors

- Владислав Пискунов for writing `zdb_query` and [sa_zdb](https://github.com/xxxbobrxxx/sqlalchemy_zombodb) in general.
- Sander Ferdinand
