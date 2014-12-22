from __future__ import print_function
from __future__ import division
from copy import deepcopy
from builtins import object
import sys
import datetime

from sqlalchemy import types, Table, MetaData, ForeignKeyConstraint
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
            assert isinstance(value, datetime.datetime), "value {} is not of type datetime.datetime but type {}".format(value,type(value))
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