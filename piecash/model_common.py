import uuid
import decimal

from sqlalchemy import Column, TEXT, types, Table, VARCHAR, INTEGER, BIGINT, cast, Float, inspect
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session


@as_declarative()
class DeclarativeBase(object):
    pass


class DeclarativeBaseGuid(DeclarativeBase):
    __abstract__ = True
    guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)

    def __init__(self, **kwargs):
        """A simple constructor that allows initialization from kwargs.

        Sets attributes on the constructed instance using the names and
        values in ``kwargs``.

        Only keys that are present as
        attributes of the instance's class are allowed. These could be,
        for example, any mapped columns or relationships.
        """
        cls_ = type(self)
        key_rel = {rel.key: rel.mapper.class_ for rel in inspect(cls_).relationships}

        for k, v in kwargs.iteritems():
            attr = getattr(cls_, k)
            # if the field is a relation and the value is a string, replace the string by the lookup
            if isinstance(v, str) and k in key_rel:
                v = key_rel[k].lookup(v)
            setattr(self, k, v)

        try:
            # if there is an active session, add the object to it
            get_active_session().add(self)
        except GncNoActiveSession:
            pass

    @classmethod
    def lookup(cls, name):
        try:
            s = get_active_session()
        except GncNoActiveSession:
            raise GncNoActiveSession, "No active session is available to lookup a {} = '{}'. Please use a 'with book:' block to set an active session".format(cls.__name__, name)

        return s.query(cls).filter(cls.lookup_key == name).one()

    def get_session(self):
        # return the sa session of the object
        return object_session(self)


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

class GncNoActiveSession(GnucashException):
    pass


gnclock = Table(u'gnclock', DeclarativeBase.metadata,
                Column('Hostname', VARCHAR(length=255)),
                Column('PID', INTEGER()),
)


def dict_decimal(field):
    """Create a dictionnary that can be added to the locals() of a declarative base that models
    - two BIGINT() fields with name field_denom and field_num
    - a Decimal field linked to the two previous fields and that is the one to use in python

    :param field:
    :return:
    """

    def fset(self, d):
        _, _, exp = d.as_tuple()
        self.value_denom = denom = int(d.radix() ** (-exp))
        self.value_num = int(d * denom)

    return {
        field + '_denom': Column(field + '_denom', BIGINT(), nullable=False),
        field + '_num': Column(field + '_num', BIGINT(), nullable=False),
        field: hybrid_property(
            fget=lambda self: decimal.Decimal(self.value_num) / decimal.Decimal(self.value_denom),
            fset=fset,
            expr=lambda cls: cast(cls.value_num, Float) / cls.value_denom,
        )
    }

# module variable to be used with the context manager "with book:"
# this variable can then be used in the code to retrieve the "active" session
_default_session = []

def is_active_session():
    return len(_default_session)!=0


def get_active_session():
    # return the active session enabled thanks to a 'with book' context manager
    # throw an exception if no active session
    try:
        return _default_session[-1]
    except IndexError:
        raise GncNoActiveSession, "No active session is available. Please use a 'with book:' block to set an active session"
