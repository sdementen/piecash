# -*- coding: utf-8 -*-
import collections
import datetime

import pytest
import pytz
from sqlalchemy import create_engine, Column, TEXT
from sqlalchemy.orm import sessionmaker, composite

import piecash._common as mc
from piecash._declbase import DeclarativeBaseGuid
from piecash.business.person import Address
from piecash.sa_extra import _Date, _DateTime


def session():
    engine = create_engine("sqlite://")

    metadata = mc.DeclarativeBase.metadata
    metadata.bind = engine
    metadata.create_all()

    s = sessionmaker(bind=engine)()

    return s


class TestModelCommon(object):
    # @parametrize('helparg', ['-h', '--help'])
    def test_guid_on_declarativebase(self):
        class A(DeclarativeBaseGuid):
            __tablename__ = "a_table"

            def __init__(self):
                pass

        s = session()
        a = A()
        s.add(a)
        assert a.guid is None
        s.flush()
        assert a.guid

    def test_addr_composite(self):
        flds = "name addr1 addr2 addr3 addr4 email fax phone".split()

        class B(DeclarativeBaseGuid):
            __tablename__ = "b_table"

            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

        l = []
        for fld in flds:
            col = Column(fld, TEXT())
            setattr(B, fld, col)
            l.append(col)
        B.addr = composite(Address, *l)

        s = session()
        a = B(addr1="foo")
        assert a.addr
        a.addr.fax = "baz"
        assert a.addr1 == "foo"
        assert a.addr.addr1 == "foo"
        assert a.addr.fax == "baz"
        s.add(a)
        s.flush()

    def test_date(self):
        class C(DeclarativeBaseGuid):
            __tablename__ = "c_table"
            day = Column(_Date)

            def __init__(self, day):
                self.day = day

        s = session()
        a = C(day=datetime.date(2010, 4, 12))
        s.add(a)
        s.flush()
        assert a.day

        assert str(list(s.bind.execute("select day from c_table"))[0][0]) == "20100412"

    def test_datetime(self):
        class C(DeclarativeBaseGuid):
            __tablename__ = "d_table"
            time = Column(_DateTime)

            def __init__(self, time):
                self.time = time

        s = session()
        a = C(time=datetime.datetime(2010, 4, 12, 3, 4, 5, tzinfo=pytz.utc))
        s.add(a)
        s.flush()
        assert a.time

        assert str(list(s.bind.execute("select time from d_table"))[0][0]) == "2010-04-12 03:04:05"

    def test_float_in_gncnumeric(self):
        Mock = collections.namedtuple('Mock', 'name')
        sqlcolumn_mock = Mock('')
        numeric = mc.hybrid_property_gncnumeric(sqlcolumn_mock, sqlcolumn_mock)
        with pytest.raises(TypeError) as excinfo:
            numeric.fset(None, 4020.19)
        assert ("Received a floating-point number 4020.19 where a decimal is expected. " +
                "Use a Decimal, str, or int instead") == str(excinfo.value)

    def test_weird_type_in_gncnumeric(self):
        Mock = collections.namedtuple('Mock', 'name')
        sqlcolumn_mock = Mock('')
        numeric = mc.hybrid_property_gncnumeric(sqlcolumn_mock, sqlcolumn_mock)
        with pytest.raises(TypeError) as excinfo:
            numeric.fset(None, dict())
        assert ("Received an unknown type dict where a decimal is expected. " +
                "Use a Decimal, str, or int instead") == str(excinfo.value)
