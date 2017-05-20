from sqlalchemy import event, DDL
from sqlalchemy_zdb.utils import get_zdb_columns_as_ddl, has_type, has_index, verify_type, verify_index


def before_create(model):
    type_name = "type_%s" % model.name.lower()
    event.listen(
        model,
        "before_create",
        DDL("""
            CREATE TYPE %s AS (%s);
            """ % (type_name, get_zdb_columns_as_ddl(model))
        ).execute_if(
            callable_=lambda *args, **kwargs:  not has_type(type_name, connection=args[2])
        )
    )


def after_create(model):
    from sqlalchemy_zdb import ES_HOST, ZdbColumn
    table_name = model.name
    index_name = "idx_zdb_%s" % table_name.lower()
    type_name = "type_%s" % table_name.lower()
    event.listen(
        model,
        "after_create",
        DDL("""
            CREATE INDEX %s ON %s
            USING zombodb(
                zdb('%s', ctid),
                zdb(ROW(%s)::%s))
            WITH (url='%s');
        """ % (index_name, table_name, table_name,
               ", ".join([column.name for column in model.columns if isinstance(column, ZdbColumn)]),
               type_name, ES_HOST)
        ).execute_if(
            callable_=lambda *args, **kwargs: not has_index(table_name=table_name, index_name=index_name, connection=args[2])
        )
    )
