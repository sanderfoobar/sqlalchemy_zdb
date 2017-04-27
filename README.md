SQLAlchemy support for ZomboDb
=============================

**Experimental** support for the ZomboDB query language with SQLAlchemy. Hard fork of [sqla_zdb](https://github.com/xxxbobrxxx/sqlalchemy_zombodb) written by Владислав Пискунов.

Using `sqlalchemy_zdb.ZdbQuery`, queries will be reflected and transformed into SQL that contain the ZomboDB query syntax. 

Please check out [Query Syntax](https://github.com/skftn/sqlalchemy_zdb/blob/master/QUERY_SYNTAX.md) for  an example of supported expressions. 


## Example

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
    price = Column(BIGINT())
    inventory_count = Column(Integer()),
    discontinued = Column(Boolean(), default=False)
    availability_date = Column(DateTime())
    author = ZdbColumn(Unicode(32))
```

- `ZdbColumn` - Explicitly mark columns that are included in the ZomboDB index
- `FULLTEXT` - A zomboDB specific type
- `PHRASE` - A ZomboDB specific type

`session.metadata.create_all()` correctly creates this table.

The actual ZomboDB index will not be created, this functionality is currently being worked on. For now you'll have to do it manually. See [ZomboDB Cheatsheet](https://github.com/skftn/sqlalchemy_zdb/blob/master/zombodb_cheatsheet.md)

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
WHERE zdb('products', ctid) ==> 'author:"bar" and price >= 5 and price <= 10' AND
products.name = 'foo' AND products.discontinued = false
```

Note that both the `name` and `discontinued` columns were not included in the ZomboDB syntax, instead they appear as valid PgSQL. This is because they are not of type `ZdbColumn`. 

## Word to the wise

This extension is currently in alpha. If you decide to use this package, double check if the SQL queries generated are correct. Upon weird behaviour please submit an issue so I can look into it.

Known issues:

- ZomboDB `CREATE INDEX` and/or `CREATE TYPE` not implemented yet
- No unit tests as of this moment
