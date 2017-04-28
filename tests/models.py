from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Boolean, DateTime
from sqlalchemy import Unicode
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT

from sqlalchemy_zdb.types import PHRASE, FULLTEXT, ZdbColumn

base = declarative_base(name="Model")


class Products(base):
    __tablename__ = "products"

    id = Column(BIGINT, nullable=False, primary_key=True)
    name = Column(Unicode(), nullable=False)
    keywords = Column(ARRAY(Unicode(64)))
    short_summary = ZdbColumn(PHRASE())
    long_description = ZdbColumn(FULLTEXT())
    price = ZdbColumn(BIGINT())
    inventory_count = Column(Integer())
    discontinued = Column(Boolean(), default=False)
    availability_date = Column(DateTime())
    author = ZdbColumn(Unicode(32))
