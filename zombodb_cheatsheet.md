### Create extension

    CREATE EXTENSION zombodb;
    SELECT * FROM pg_extension;


# Index creation
### Index a table
    CREATE INDEX idx_zdb_products 
        ON products 
    USING zombodb(zdb('products', products.ctid), zdb(products))
        WITH (url='http://localhost:9200/', 
              shards=N, 
              replicas=N,
              preference='...',
              options='...');

Options can always be changed at a later point using `ALTER INDEX`:

    ALTER INDEX idxname SET (replicas=3);
    ALTER INDEX idxname RESET (preference);

### Index a table (excluding columns)

Create a [composite type](https://www.postgresql.org/docs/current/static/sql-createtype.html) that describes the fields from your source table that you want to index:

    CREATE TYPE myrowtype AS (id bigint, subject phrase, body fulltext);

Create the INDEX, using a [row constructor](https://www.postgresql.org/docs/current/static/sql-expressions.html#SQL-SYNTAX-ROW-CONSTRUCTORS):

    CREATE INDEX idx 
        ON table 
    USING zombodb (zdb('table', ctid), zdb(ROW(id, subject, body)::myrowtype))
       WITH (url='http://localhost:9200/');

### Index a table (excluding whole rows)

Partial indexes are built-in to Postgres and are not ZomboDB specific:

    CREATE INDEX idxfoo ON table USING zombodb (....) WITH (...) WHERE file_isdir = false;

Postgres will then only insert rows into that index when its predicate evaluates to true.

When you query, you *must* also include that predicate or else Postgres won't know that it can use the partial index:

    SELECT * FROM table WHERE zdb('table', ctid) ==> 'user query' AND file_isdir = false;

You'll only pay a small performance cost when you INSERT or UPDATE records, and save all sorts of time at SELECT.

### Index a table (include a specific nested object within a JSON type)

    CREATE TABLE my_type AS (pkey bigint, title phrase, author text, some_value text, some_object json);
    CREATE INDEX ... USING zombodb(zdb('table', ctid), zdb(ROW (pkey, title, author, json_blob->>'some_value', json_blob->'path'->'to'->'some_object')::my_type)) WITH (...);

[More info](https://github.com/zombodb/zombodb/issues/156)

# Queries
### Basic
    SELECT FROM foo WHERE zdb('foo', foo.ctid) ==> ...;

# Index management
### DROP

    DROP INDEX idxname;
    #curl -XDELETE http://cluster.ip:9200/db.schema.table.index
    curl -XDELETE "http://localhost:9200/db_name.public.files.idx_zdb_files"

### REINDEX
Use Postgres' standard [REINDEX](http://www.postgresql.org/docs/9.5/static/sql-reindex.html) command.  All the various forms of `INDEX`, `TABLE`, and `DATABASE` are supported.

### ALTER

- Adding/removing columns is supported
- Renaming columns is supported but requires a manual `REINDEX`

### VACUUM

- `VACUUM` does the minimum amount of work to remove dead rows from the backing Elastisearch index
- `VACUUM FULL` is the same as running a `REINDEX`

For tables that are frequently UPDATEd, it's important that autovacuum be configured to be as aggressive as I/O can afford.

# Column types

`phrase`, `fulltext`, `fulltext_with_shingles`.

If a column was previously of type `VARCHAR` and you'd like to change it to one of the special zombodb types (but only those that inherit from `text`) - you'll need to cast it too:

    ALTER TABLE table_name 
    ALTER COLUMN column_name 
    TYPE fulltext USING cast(column_name as fulltext);
    
# Operators

Symbol | Description 
---    | ---      
`:`      | field contains term
`=`      | field contains term (same as : )
`<`      | field contains terms less than value 
`<=`     | field contains terms less than or equal to value
`>`      | field contains terms greater than value
`>=`     | field contains terms greater than or equal to value
`!=`     | field does not contain term
`<>`     | field does not contain term (same as != )
`/to/`   | range query, in form of field:START /to/ END
`:~`     | field contains terms matching a [regular expression](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-regexp-query.html#regexp-syntax).  Note that regular expression searches are always **case sensitive**.
`:@`     | ["more like this"](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-mlt-query.html)
`:@~`    | ["fuzzy like this"](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-flt-field-query.html)

