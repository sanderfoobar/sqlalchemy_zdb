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
Could not get `field:start /to/ END` work (as per [documentation](https://github.com/zombodb/zombodb/blob/master/SYNTAX.md#operators)), instead made it return:

    column >= 5 and column <= 15

*Warning: Only works on integers.*

```python
q = q.filter(Products.price.between(5, 10))
```

```sql
SELECT [...] FROM products 
WHERE zdb('products', ctid) ==> 'price >= 5 and price <= 10'
```

### LIKE

When passed a string, produces the expression: `column:"foo"`
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
    WHERE zdb('products', ctid) ==> '#limit(price desc, 1, 1) author:("foo","bar")' ORDER BY products.availability_date DESC
```

In other words, if you were previously already using `limit()` in conjunction with `order_by()` in your query building and the subject column is `ZdbColumn`, it'll try to bake a proper query for it.

Example #2 - using `ZdbScore`

```python
from sqlalchemy_zdb.types import ZdbScore

q = q.filter(Products.author.in_(["foo", "bar"]))
q = q.order_by(ZdbScore, 
               Products.availability_date.desc(), 
               Products.long_description.desc()).limit(1).offset(1)
```

`ZdbScore` is still in development.



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
