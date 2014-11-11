import uuid

from sqlalchemy import Column, TEXT, types, Table, VARCHAR, INTEGER
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class DeclarativeBase(object):
    pass


class DeclarativeBaseGuid(DeclarativeBase):
    __abstract__ = True
    guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)


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


class _DateTime(types.TypeDecorator):
    """Used to customise the DateTime type for sqlite (ie without the separators as in gnucash
    """
    impl = types.TypeEngine

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return sqlite.DATETIME(
                storage_format="%(year)04d%(month)02d%(day)02d%(hour)02d%(minute)02d%(second)02d",
                regexp=r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})"
            )
        else:
            return types.DateTime()


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


class GnucashException(Exception):
    pass


gnclock = Table(u'gnclock', DeclarativeBase.metadata,
                Column('Hostname', VARCHAR(length=255)),
                Column('PID', INTEGER()),
)
