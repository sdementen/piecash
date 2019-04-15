from __future__ import division, unicode_literals
from __future__ import print_function

import datetime
import logging
import sys
import unicodedata

import pytz
import tzlocal
from sqlalchemy import types, Table, MetaData, ForeignKeyConstraint, event, create_engine
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy.orm import sessionmaker, object_session

# import yaml


def __init__blocked(self, *args, **kwargs):
    raise NotImplementedError("Objects of type {} cannot be created from scratch "
                              "(only read)".format(self.__class__.__name__))


@as_declarative(constructor=__init__blocked)
class DeclarativeBase(object):
    @property
    def book(self):
        """Return the gnc book holding the object
        """
        s = object_session(self)
        return s and s.book

    def object_to_validate(self, change):
        """yield the objects to validate when the object is modified (change="new" "deleted" or "dirty").

        For instance, if the object is a Split, if it changes, we want to revalidate not the split
        but its transaction and its lot (if any). split.object_to_validate should yeild both split.transaction
        and split.lot
        """
        return
        yield

    def on_book_add(self):
        """Call when the object is added to a book"""
        pass

    def validate(self):
        """This must be reimplemented for object requiring validation
        """
        raise NotImplementedError(self)

    def get_all_changes(self):
        try:
            return self.book.session._all_changes[id(self)]
        except KeyError:
            return {"STATE_CHANGES": ["unchanged"],
                    "OBJECT": self}

    def __repr__(self):
        return str(self)


tz = tzlocal.get_localzone()
utc = pytz.utc


@compiles(sqlite.DATE, 'sqlite')
def compile_date(element, compiler, **kw):
    return "TEXT(8)"  # % element.__class__.__name__


@compiles(sqlite.DATETIME, 'sqlite')
def compile_datetime(element, compiler, **kw):
    """ data type for the date field

    note: it went from TEXT(14) in 2.6 to TEXT(19) in 2.8 to accommodate
    for the new ISO format of date in sqlite"""
    return "TEXT(14)"


class _DateTime(types.TypeDecorator):
    """Used to customise the DateTime type for sqlite (ie without the separators as in gnucash
    """
    impl = types.TypeEngine

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return sqlite.DATETIME(
                storage_format="%(year)04d-%(month)02d-%(day)02d %(hour)02d:%(minute)02d:%(second)02d",
                regexp=r"(\d{4})-?(\d{2})-?(\d{2}) ?(\d{2}):?(\d{2}):?(\d{2})",
            )
        else:
            return types.DateTime()

    def process_bind_param(self, value, dialect):
        if value is not None:
            assert isinstance(value, datetime.datetime), "value {} is not of type datetime.datetime but type {}".format(
                value, type(value))
            if value.microsecond != 0:
                logging.warning("A datetime has been given with microseconds which are not saved in the database")

            if not value.tzinfo:
                value = tz.localize(value)

            return value.astimezone(utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is not None:
            return utc.localize(value).astimezone(tz)


class _DateAsDateTime(types.TypeDecorator):
    """Used to customise the DateTime type for sqlite (ie without the separators as in gnucash
    """
    impl = types.TypeEngine

    def __init__(self, neutral_time=True, *args, **kwargs):
        super(_DateAsDateTime, self).__init__(*args, **kwargs)
        self.neutral_time = neutral_time

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return sqlite.DATETIME(
                storage_format="%(year)04d-%(month)02d-%(day)02d %(hour)02d:%(minute)02d:%(second)02d",
                regexp=r"(\d{4})-?(\d{2})-?(\d{2}) ?(\d{2}):?(\d{2}):?(\d{2})",
            )
        else:
            return types.DateTime()

    def process_bind_param(self, value, dialect):
        if value is not None:
            assert isinstance(value, datetime.date) and not isinstance(value, datetime.datetime), \
                "value {} is not of type datetime.date but type {}".format(value, type(value))
            if self.neutral_time:
                result = datetime.datetime.combine(value, datetime.time(10, 59, 0))
            else:
                result = tz.localize(datetime.datetime.combine(value, datetime.time(0, 0, 0))) \
                    .astimezone(utc)
            return result.replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is not None:
            r = utc.localize(value).astimezone(tz).date()
            return r


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


def pure_slot_property(slot_name, slot_transform=lambda x: x,
                       ignore_invalid_slot=False):
    """
    Create a property (class must have slots) that maps to a slot

    :param slot_name: name of the slot
    :param slot_transform: transformation to operate before assigning value
    :param ignore_invalid_slot: True if incorrect values (usually due to deleted data)
        should be converted to None
    :return:
    """

    def fget(self):
        # return None if the slot does not exist. alternative could be to raise an exception
        try:
            return self[slot_name].value
        except KeyError:
            return None
        except orm_exc.NoResultFound:
            if ignore_invalid_slot:
                return None
            else:
                raise

    def fset(self, value):
        v = slot_transform(value)
        if v is None:
            if slot_name in self:
                del self[slot_name]
        else:
            self[slot_name] = v

    return hybrid_property(
        fget=fget,
        fset=fset,
    )


def kvp_attribute(name, to_gnc=lambda v: v, from_gnc=lambda v: v, default=None):
    def getter(self):
        try:
            return from_gnc(self[name].value)
        except KeyError:
            return default

    def setter(self, value):
        if value == default:
            try:
                del self[name]
            except KeyError:
                pass
        else:
            self[name] = to_gnc(value)

    return property(getter, setter)


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


Session = sessionmaker(autoflush=False)


def create_piecash_engine(uri_conn, **kwargs):
    eng = create_engine(uri_conn, **kwargs)

    if eng.name == "sqlite":
        # add proper isolation code for sqlite engine
        @event.listens_for(eng, "connect")
        def do_connect(dbapi_connection, connection_record):
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            # print("=========================== in DO CONNECT")
            # dbapi_connection.isolation_level = "IMMEDIATE"
            # dbapi_connection.isolation_level = "EXCLUSIVE"
            pass

        @event.listens_for(eng, "begin")
        def do_begin(conn):
            # emit our own BEGIN
            # print("=========================== in DO BEGIN")
            # conn.execute("BEGIN EXCLUSIVE")
            pass

    return eng


class ChoiceType(types.TypeDecorator):
    impl = types.INTEGER()

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        try:
            return [k for k, v in self.choices.items() if v == value][0]
        except IndexError:
            # print("Value '{}' is not in [{}]".format(", ".join(self.choices.values())))
            raise ValueError("Value '{}' is not in choices [{}]".format(value, ", ".join(self.choices.values())))

    def process_result_value(self, value, dialect):
        return self.choices[value]
