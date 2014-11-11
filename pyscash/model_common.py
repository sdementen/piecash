import os
import socket
from sqlalchemy import Column, TEXT, types, Table, VARCHAR, INTEGER, create_engine
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.declarative import as_declarative
import uuid
from sqlalchemy.orm import sessionmaker


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
        return isinstance(other, Address) and all(getattr(other, fld)==getattr(self, fld) for fld in _address_fields)

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

def connect_to_gnucash_book(sqlite_file=None, postgres_conn=None, readonly=True, open_if_lock=False):
    engine = None
    if sqlite_file:
        engine = create_engine("sqlite:///{}".format(sqlite_file))
    elif postgres_conn:
        engine = create_engine(postgres_conn)

    locks = list(engine.execute(gnclock.select()))

    # ensure the file is not locked by GnuCash itself
    if locks and not open_if_lock:
        raise GnucashException, "Lock on the file"
    # else:
    #     engine.execute(gnclock.insert(), Hostname=socket.gethostname(), PID=os.getpid())

    s = sessionmaker(bind=engine)()
    # flush is a "no op" if readonly
    if readonly:
        def new_flush(*args, **kwargs):
            if s.dirty or s.new or s.deleted:
                s.rollback()
                raise GnucashException, "You cannot change the DB, it is locked !"

        s.flush = new_flush

    return s


