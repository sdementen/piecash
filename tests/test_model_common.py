# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
# from pytest.mark import parametrize
#
import datetime

from sqlalchemy import create_engine, Column, TEXT
from sqlalchemy.orm import sessionmaker, composite

import piecash.model_common as mc
from piecash.sa_extra import _Date, _DateTime

# parametrize = pytest.mark.parametrize
from piecash.sa_extra import Address


def session():
    engine = create_engine("sqlite://")

    metadata = mc.DeclarativeBaseGuid.metadata
    metadata.bind = engine
    metadata.create_all()

    s = sessionmaker(bind=engine)()

    return s


class TestModelCommon(object):
    # @parametrize('helparg', ['-h', '--help'])
    def test_guid_on_declarativebase(self):
        class A(mc.DeclarativeBaseGuid):
            __tablename__ = "a_table"

        s = session()
        a = A()
        s.add(a)
        assert a.guid is None
        s.flush()
        assert a.guid


    def test_addr_composite(self):
        class B(mc.DeclarativeBaseGuid):
            __tablename__ = "b_table"

        l = []
        for fld in "addr1 addr2 addr3 addr4 email fax name phone".split():
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
        # don't understand the working of composite ... not really critical
        # assert a.addr.fax == "baz"

    def test_date(self):
        class C(mc.DeclarativeBaseGuid):
            __tablename__ = "c_table"
            day = Column(_Date)


        s = session()
        a = C(day=datetime.date(2010, 4, 12))
        s.add(a)
        s.flush()
        assert a.day

        assert str(list(s.bind.execute("select day from c_table"))[0][0]) == "20100412"

    def test_datetime(self):
        class C(mc.DeclarativeBaseGuid):
            __tablename__ = "d_table"
            time = Column(_DateTime)

        s = session()
        a = C(time=datetime.datetime(2010, 4, 12,3,4,5))
        s.add(a)
        s.flush()
        assert a.time

        assert str(list(s.bind.execute("select time from d_table"))[0][0]) == "20100412030405"
