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


## Manually constructing filters
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
