from sqlalchemy import types, Table, MetaData, ForeignKeyConstraint, cast, String
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.declarative import as_declarative
import tzlocal
import pytz


@as_declarative()
class DeclarativeBase(object):
    pass


tz = tzlocal.get_localzone()
utc = pytz.utc

class _DateTime(types.TypeDecorator):
    """Used to customise the DateTime type for sqlite (ie without the separators as in gnucash
    """
    impl = types.TypeEngine
    is_sqlite = False

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            self.is_sqlite = True
            return sqlite.DATETIME(
                storage_format="%(year)04d%(month)02d%(day)02d%(hour)02d%(minute)02d%(second)02d",
                regexp=r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})",
            )
        else:
            return types.DateTime()

    # def column_expression(self, colexpr):
    #     if self.is_sqlite:
    #         # need to cast otherwise may store a string date as long integer as sqlite sees a number
    #         return cast(colexpr, String)
    #     else:
    #         return colexpr
    #
    def bind_expression(self, colexpr):
        # can be also used in
        if self.is_sqlite:
            # need to cast otherwise may store a string date as long integer as sqlite sees a number
            return cast(colexpr, String)
        else:
            return colexpr

    def process_bind_param(self, value, engine):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=tz)
            return value.astimezone(utc)

    def process_result_value(self, value, engine):
        if value is not None:
            return value.replace(tzinfo=utc).astimezone(tz)


class _Date(types.TypeDecorator):
    """Used to customise the DateTime type for sqlite (ie without the separators as in gnucash
    """
    impl = types.TypeEngine

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return sqlite.DATE(
                storage_format="%(year)04d%(month)02d%(day)02d",
                regexp=r"(\d{4})(\d{2})(\d{2})"
            )
        else:
            return types.Date()

    def bind_expression(self, colexpr):
        # can be also used in
        if self.is_sqlite:
            # need to cast otherwise may store a string date as long integer as sqlite sees a number
            return cast(colexpr, String)
        else:
            return colexpr

_address_fields = "addr1 addr2 addr3 addr4 email fax name phone".split()


class Address(object):
    def __init__(self, *args):
        for fld, val in zip(_address_fields, args):
            setattr(self, fld, val)

    def __composite_values__(self):
        return tuple(self)

    def __eq__(self, other):
        return isinstance(other, Address) and all(getattr(other, fld) == getattr(self, fld) for fld in _address_fields)

    def __ne__(self, other):
        return not self.__eq__(other)


def get_foreign_keys(metadata, engine):
    """ Retrieve all foreign keys from metadata bound to an engine
    :param metadata:
    :param engine:
    :return:
    """
    reflected_metadata = MetaData()
    for table_name in metadata.tables.keys():
        table = Table(
            table_name,
            reflected_metadata,
            autoload=True,
            autoload_with=engine
        )

        for constraint in table.constraints:
            if not isinstance(constraint, ForeignKeyConstraint):
                continue
            yield constraint