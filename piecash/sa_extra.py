from __future__ import print_function
from __future__ import division
from copy import deepcopy
from decimal import Decimal
from builtins import zip
from builtins import object
import sys

from sqlalchemy import types, Table, MetaData, ForeignKeyConstraint, Float, cast
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import class_mapper, sessionmaker
import tzlocal
import pytz


if sys.version > '3':
    long = int


@as_declarative()
class DeclarativeBase(object):
    def __deepcopy__(self, memo):
        raise Unsafe
        print("memo", memo)
        pk_keys = set([c.key for c in class_mapper(self.__class__).primary_key])

        dct = {}
        for p in class_mapper(self.__class__).iterate_properties:
            if p.key in pk_keys:
                continue
            if p.key.endswith("guid"):
                continue
            attr = getattr(self, p.key)
            if isinstance(attr, list):
                attr = [deepcopy(sattr, memo) for sattr in attr]
            dct[p.key] = attr

        obj = self.__class__(**dct)
        return obj


tz = tzlocal.get_localzone()
utc = pytz.utc


@compiles(sqlite.DATE, 'sqlite')
def compile_date(element, compiler, **kw):
    return "TEXT(8)"  # % element.__class__.__name__


@compiles(sqlite.DATETIME, 'sqlite')
def compile_date(element, compiler, **kw):
    return "TEXT(14)"  # % element.__class__.__name__


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


def hybrid_property_gncnumeric(num_col, denom_col):
    num_name, denom_name = "_{}".format(num_col.name), "_{}".format(denom_col.name)
    # num_name, denom_name = num_col.name, denom_col.name

    def fset(self, d):
        if d is None:
            num, denom = None, None
        else:
            if isinstance(d, tuple):
                d = Decimal(d[0]) / d[1]
            elif isinstance(d, (float, int, long, str)):
                d = Decimal(d)
            assert isinstance(d, Decimal)

            sign, digits, exp = d.as_tuple()
            denom = 10 ** max(-exp, 0)

            # print num_name, denom,
            denom_basis = getattr(self, "{}_basis".format(denom_name), None)
            if denom_basis is not None:
                # print "got a basis for ", self, denom_basis
                denom = denom_basis
            # print denom
            num = int(d * denom)

        setattr(self, num_name, num)
        setattr(self, denom_name, denom)


    def fget(self):
        num, denom = getattr(self, num_name), getattr(self, denom_name)
        if num:
            return Decimal(num) / denom


    def expr(cls):
        return cast(num_col, Float) / denom_col

    return hybrid_property(
        fget=fget,
        fset=fset,
        expr=expr,
    )


def mapped_to_slot_property(col, slot_name, slot_transform=lambda x: x):
    """Assume the attribute in the class as the same name as the table column with "_" prepended"""
    col_name = "_{}".format(col.name)

    def fget(self):
        return getattr(self, col_name)

    def fset(self, value):
        v = slot_transform(value)
        if v is None:
            if slot_name in self:
                del self[slot_name]
        else:
            self[slot_name] = v

        setattr(self, col_name, value)

    def expr(cls):
        return col

    return hybrid_property(
        fget=fget,
        fset=fset,
        expr=expr,
    )


def get_foreign_keys(metadata, engine):
    """ Retrieve all foreign keys from metadata bound to an engine
    :param metadata:
    :param engine:
    :return:
    """
    reflected_metadata = MetaData()
    for table_name in list(metadata.tables.keys()):
        table = Table(
            table_name,
            reflected_metadata,
            autoload=True,
            autoload_with=engine,
        )

        for constraint in table.constraints:
            if not isinstance(constraint, ForeignKeyConstraint):
                continue
            yield constraint


class CallableList(list):
    def get(self, **kwargs):
        for obj in self:
            for k, v in kwargs.items():
                if getattr(obj, k) != v:
                    break
            else:
                return obj
        else:
            raise KeyError("Could not find object with {} in {}".format(kwargs, self))


Session = sessionmaker(autoflush=False)