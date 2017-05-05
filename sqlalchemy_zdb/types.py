from sqlalchemy import Column
from sqlalchemy.types import UserDefinedType


class _ZdbDomain(UserDefinedType):
    """
    phrases/fulltext/fulltext_with_shingles are postgres DOMAIN's
    that sits on top of the standard text datatype. As far as
    Postgres is concerned, it is functionally no different than
    the text datatype, however they have special meaning to
    ZomboDB when indexing and searching. In brief, they indicate
    that such fields should be analyzed.
    """
    def __init__(self, *args):
        self._args = args

    def convert_bind_param(self, value, engine):
        return value

    def convert_result_value(self, value, engine):
        return value

    @property
    def python_type(self):
        return str


class PHRASE(_ZdbDomain):
    def __init__(self, *args):
        super(PHRASE, self).__init__(*args)

    def get_col_spec(self):
        return "phrase"

    def is_mutable(self):
        return True


class FULLTEXT(_ZdbDomain):
    def __init__(self, *args):
        super(FULLTEXT, self).__init__(*args)

    def get_col_spec(self):
        return "fulltext"

    def is_mutable(self):
        return True


class FULLTEXT_SHINGLES(_ZdbDomain):
    def __init__(self, *args):
        super(FULLTEXT_SHINGLES, self).__init__(*args)

    def get_col_spec(self):
        return "fulltext_with_shingles"

    def is_mutable(self):
        return True


class ZdbColumn(Column):
    def __init__(self, *args, **kwargs):
        super(ZdbColumn, self).__init__(*args, **kwargs)


class ZdbPhrase(object):
    def __init__(self, phrase: str):
        self.phrase = phrase.strip('"')

    def __str__(self):
        return '"%s"' % self.phrase


class ZdbLiteral(object):
    def __init__(self, literal):
        self.literal = literal


class ZdbScore(Column):
    def __init__(self, direction="asc"):
        super(ZdbScore, self)
        if not direction in ("asc", "desc"):
            raise Exception("Invalid parameter for direction")
        self._zdb_direction = direction
