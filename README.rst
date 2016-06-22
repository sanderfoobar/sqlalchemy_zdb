=============================
SqlAlchemy support of ZomboDb
=============================

This extension provides support of ZomboDb query language for python sqlalchemy ORM

ZomboDb project:
https://github.com/zombodb/zombodb

Examples
--------

Phrase query::

    from sa_zdb import zdb_query, ZdbPhrase

    pg_session.query(Post.text)\
        .filter(zdb_query(Post.text == ZdbPhrase('hey joe')))


    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'text:"hey joe"'

Boolean query::

    pg_session.query(Post.text)\
        .filter(zdb_query(or_(Post.text == 'foo', and_(Post.text == 'bar', Post.text == 'fuzz'))))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> '(text:foo or (text:bar and text:fuzz))'

more_like_this::

    pg_session.query(Post.text)\
        .filter(zdb_query(Post.text.match('foo')))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'text:@foo'

Comparison operations::

    pg_session.query(Post.text)\
        .filter(zdb_query(Post.comments > 1))

    SELECT post.text AS post_text
    FROM post
    WHERE zdb('post', ctid) ==> 'comments > 1'

Also, regexp supports through like operation
