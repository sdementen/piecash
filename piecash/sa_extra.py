import re
import datetime

from sqlalchemy import types, Table, MetaData, ForeignKeyConstraint, DATE, DATETIME, TIME
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import as_declarative
import tzlocal
import pytz


@as_declarative()
class DeclarativeBase(object):
    pass


tz = tzlocal.get_localzone()
utc = pytz.utc

@compiles(sqlite.DATE, 'sqlite')
def compile_date(element, compiler, **kw):
    return "TEXT(8)" #% element.__class__.__name__

@compiles(sqlite.DATETIME, 'sqlite')
def compile_date(element, compiler, **kw):
    return "TEXT(14)" #% element.__class__.__name__


class _DateTime(types.TypeDecorator):
    """Used to customise the DateTime type for sqlite (ie without the separators as in gnucash
    """
    impl = types.TypeEngine

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return sqlite.DATETIME(
            storage_format="%(year)04d%(month)02d%(day)02d%(hour)02d%(minute)02d%(second)02d",
                regexp=r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})",
            )
        else:
            return types.DateTime()

    def process_bind_param(self, value, engine):
        if value is not None:
            if value.tzinfo is None:
                value = tz.localize(value)
            return value.astimezone(utc)

    def process_result_value(self, value, engine):
        if value is not None:
            return utc.localize(value).astimezone(tz)


class _Date(types.TypeDecorator):
    """Used to customise the DateTime type for sqlite (ie without the separators as in gnucash
    """
    impl = types.TypeEngine
    is_sqlite = False

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return sqlite.DATE(
                storage_format="%(year)04d%(month)02d%(day)02d",
                regexp=r"(\d{4})(\d{2})(\d{2})"
            )
        else:
            return types.Date()


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