from __future__ import print_function
from __future__ import division, unicode_literals
from pprint import pprint, pformat
import sys
import datetime
import unicodedata

from sqlalchemy import types, Table, MetaData, ForeignKeyConstraint, event, create_engine, inspect
from sqlalchemy.dialects import sqlite
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import sessionmaker, object_session, RelationshipProperty, CompositeProperty, \
    ColumnProperty, Mapper
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.state import AttributeState
import tzlocal
import pytz
from sqlalchemy.orm.base import instance_state

# import yaml

if sys.version > '3':
    long = int
else:
    long = long


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
        yield None

    def validate(self):
        """This must be reimplemented for object requiring validation
        """
        raise NotImplementedError(self)

    def object_beforechange(self):
        return instance_state(self).committed_state

    def __format__(self, format_spec):
        if format_spec != "expl":
            return format(str(self), format_spec)

        def fmt_relation(k):
            return "{} = {!r} [{!r}]\n".format(k, getattr(self, k), getattr(self, k.replace("_guid","")))

        def fmt_field(k):
            return "{} = {!r}\n".format(k, getattr(self, map_sql_orm[k]))

        i = inspect(self.__class__)
        # print(list(i.attrs))
        print(list(i.all_orm_descriptors))
        print(yaml.dump({k:getattr(self,k.key) for k in i.all_orm_descriptors if isinstance(k, InstrumentedAttribute)}))
        fefrezrez
        print([k.key for k in i.mapper.column_attrs]+[k.key for k in i.attrs])
        # print(self.as_dict())
        for k in dir(self):
            if k.startswith("_") or k=="metadata":
                continue
            attr = getattr(self, k)
            if isinstance(attr, classmethod):
                ko
            attr_type = type(attr)
            if isinstance(attr, (int, str, datetime.datetime)):
                print("==>",i.attrs[k])
            print(k, type(attr))
        # print(dir(self))
        fdsfdsfds
        map_sql_orm=({c.columns[0].name:c.key for c in i.mapper.column_attrs})

        cols = [col.name for col in self.__table__.columns]

        res = ""
        for col in cols:
            if "_guid" in col:
                res += fmt_relation(col)
            else:
                res += fmt_field(col)
        res += "slots = {}\n".format(pformat(self.slots))
        return res
        print(cols)
        fdsfds
        fields = []
        relations = []
        pk = None
        # print(list(inspect(self).attrs))
        # print(self.__class__.__dict__)
        # fdsfds
        # print(inspect(self.__class__).all_orm_descriptors.keys())
        # fdfdsqfdsq
        for k in inspect(self.__class__).all_orm_descriptors:
            if isinstance(k, Mapper):continue
            print(k, type(k), dir(k))
            if isinstance(k, hybrid_property):
                print(k)
            elif k.key.startswith("_"):
                continue

            if isinstance(k, RelationshipProperty):
                # skip relationships as we get them from foreign_keys
                pass
            elif isinstance(k, CompositeProperty):
                # skip composite (like Address)
                pass
            elif isinstance(k, ColumnProperty):
                assert len(k.columns) == 1
                sql_col = k.columns[0]
                if sql_col.primary_key:
                    pk = k.key
                elif sql_col.foreign_keys:
                    relations.append((k.key, k.key.split("_")[0]))
                else:
                    fields.append(k.key)
            elif isinstance(k, InstrumentedAttribute):
                pass
            elif isinstance(k, hybrid_property):
                print(k.fget(self))
                # print(k.key, k.value)
                # fields.append(k.key)
            else:
                raise ValueError("Unknown type of property '{}' for key '{}'".format(type(k), k))

        def fmt(k):
            if isinstance(k, tuple):
                return "{} = {!r} [{}]\n".format(k[1], getattr(self, k[1]), getattr(self, k[0]))
            elif k:
                return "{} = {!r}\n".format(k, getattr(self, k))
            else:
                return ""

        res = fmt_field(pk) + "".join(map(fmt_field, fields)) + "".join(map(fmt_field, relations)) + fmt_field("slots")

        return res

    if sys.version > '3':
        def __str__(self):
            return self.__unirepr__()

        def __repr__(self):
            return self.__unirepr__()

    else:
        def __str__(self):
            return unicodedata.normalize('NFKD', self.__unirepr__()).encode('ascii', 'ignore')

        def __repr__(self):
            return self.__unirepr__().encode('ascii', errors='backslashreplace')

    def __unicode__(self):
        return self.__unirepr__()


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
            assert isinstance(value, datetime.datetime), "value {} is not of type datetime.datetime but type {}".format(
                value, type(value))
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


def pure_slot_property(slot_name, slot_transform=lambda x: x):
    """
    Create a property (class must have slots) that maps to a slot

    :param slot_name: name of the slot
    :param slot_transform: transformation to operate before assigning value
    :return:
    """

    def fget(self):
        # return None if the slot does not exist. alternative could be to raise an exception
        try:
            return self[slot_name].value
        except KeyError:
            return None

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

def kvp_attribute(name, to_gnc, from_gnc, default=None):
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


