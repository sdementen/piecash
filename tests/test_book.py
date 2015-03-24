import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, drop_database

from piecash import create_book, Account, GnucashException, Book
from piecash.sa_extra import get_foreign_keys, DeclarativeBase

test_folder = os.path.dirname(os.path.realpath(__file__))
db_sqlite = os.path.join(test_folder, "fooze.sqlite")
db_postgres_uri = "postgresql://postgres:@localhost:5432/foo"
db_sqlite_uri = "sqlite:///{}".format(db_sqlite)

databases_to_check = [None, db_sqlite_uri]
if os.environ.get("TRAVIS", False):
    databases_to_check.append(db_postgres_uri)

@pytest.yield_fixture(params=databases_to_check)
def s(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)
    b = create_book(uri_conn=name)
    yield b
    b.session.close()

@pytest.yield_fixture(params=databases_to_check)
def s_USD(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)
    b = create_book(uri_conn=name, currency="USD")
    yield b
    b.session.close()

class TestBook_create_book(object):
    def test_create_default(self, s):

        assert isinstance(s, Book)
        assert isinstance(s.session, Session)
        assert s.uri is None
        assert s.session.bind.name == "sqlite"

        EUR = s.commodities[0]
        assert EUR.mnemonic == "EUR"
        assert EUR.namespace == "CURRENCY"

        # no std account
        assert len(s.accounts) == 0
        # two root accounts
        root_accs = s.query(Account).all()
        assert all([acc.type == "ROOT" for acc in root_accs])
        assert len(root_accs) == 2

        # no slots
        assert len(s.slots) == 0

    def test_create_save_cancel_flush(self, s):

        EUR = s.commodities[0]
        EUR.mnemonic = "foo"
        assert EUR.mnemonic == "foo"
        s.cancel()
        assert EUR.mnemonic == "EUR"

        EUR.mnemonic = "foo"
        assert EUR.mnemonic == "foo"
        s.flush()
        assert EUR.mnemonic == "foo"
        s.cancel()
        assert EUR.mnemonic == "EUR"

        EUR.mnemonic = "foo"
        s.save()
        assert EUR.mnemonic == "foo"

    def test_create_USD_book(self, s_USD):
        CUR = s_USD.commodities[0]
        assert CUR.mnemonic == "USD"
        assert CUR.namespace == "CURRENCY"

    def test_create_specific_currency(self):
        s = create_book(currency="USD")
        CUR = s.commodities[0]
        assert CUR.mnemonic == "USD"
        assert CUR.namespace == "CURRENCY"

        s = create_book(currency="CHF")
        CUR = s.commodities[0]
        assert CUR.mnemonic == "CHF"
        assert CUR.namespace == "CURRENCY"

        with pytest.raises(ValueError):
            s = create_book(currency="ZIE")

    def test_create_named_sqlite_book(self):
        # remove file if left from previous test
        if os.path.exists(db_sqlite):
            os.remove(db_sqlite)

        # assert creation of file
        s = create_book(db_sqlite)
        assert os.path.exists(db_sqlite)
        t = os.path.getmtime(db_sqlite)

        # ensure error if no overwrite
        with pytest.raises(GnucashException):
            s = create_book(db_sqlite)
        assert os.path.getmtime(db_sqlite) == t
        with pytest.raises(GnucashException):
            s = create_book(uri_conn="sqlite:///{}".format(db_sqlite))
        assert os.path.getmtime(db_sqlite) == t
        with pytest.raises(GnucashException):
            s = create_book(db_sqlite, overwrite=False)
        assert os.path.getmtime(db_sqlite) == t

        # if overwrite, DB is recreated
        s = create_book(db_sqlite, overwrite=True)
        assert os.path.getmtime(db_sqlite) > t

        # clean test
        os.remove(db_sqlite)

    def test_create_with_FK(self):
        # create and keep FK
        s = create_book(uri_conn=db_sqlite_uri, keep_foreign_keys=True, overwrite=True)
        s.session.close()

        insp = Inspector.from_engine(create_engine(db_sqlite_uri))
        fk_total = []
        for tbl in insp.get_table_names():
            fk_total.append(insp.get_foreign_keys(tbl))
        assert len(fk_total) == 25

    def test_create_without_FK(self):
        # create without FK
        s = create_book(uri_conn=db_sqlite_uri, keep_foreign_keys=False, overwrite=True, echo=True)
        s.session.close()

        eng = create_engine(db_sqlite_uri)
        # assert list(eng.execute("pragma foreign_key_list('entries');"))==0
        insp = Inspector.from_engine(create_engine(db_sqlite_uri))
        for tbl in insp.get_table_names():
            fk = insp.get_foreign_keys(tbl)
            assert len(fk) == 0
