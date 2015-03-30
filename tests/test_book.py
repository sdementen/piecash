import glob
import os

import pytest
from sqlalchemy import create_engine

from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

from piecash import create_book, Account, GnucashException, Book, open_book
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri
from piecash.core import Version

# dummy line to avoid removing unused symbols
a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri

class TestBook_create_book(object):
    def test_create_default(self, new_book):
        assert isinstance(new_book, Book)
        assert isinstance(new_book.session, Session)
        assert new_book.uri is not None
        assert new_book.session.bind.name in ["sqlite", "postgresql", "mysql"]
        assert repr(new_book.query(Version).filter_by(table_name='commodities').one()) == "Version<commodities=1>"

        EUR = new_book.commodities[0]
        assert EUR.mnemonic == "EUR"
        assert EUR.namespace == "CURRENCY"

        # no std account
        assert len(new_book.accounts) == 0
        # two root accounts
        root_accs = new_book.query(Account).all()
        assert all([acc.type == "ROOT" for acc in root_accs])
        assert len(root_accs) == 2

        # no slots
        assert len(new_book.slots) == 0

    def test_create_save_cancel_flush(self, new_book):
        EUR = new_book.commodities[0]
        EUR.mnemonic = "foo"
        assert EUR.mnemonic == "foo"
        new_book.cancel()
        assert EUR.mnemonic == "EUR"

        EUR.mnemonic = "foo"
        assert EUR.mnemonic == "foo"
        new_book.flush()
        assert EUR.mnemonic == "foo"
        new_book.cancel()
        assert EUR.mnemonic == "EUR"

        EUR.mnemonic = "foo"
        new_book.save()
        assert EUR.mnemonic == "foo"

    def test_create_USD_book(self, new_book_USD):
        CUR = new_book_USD.commodities[0]
        assert CUR.mnemonic == "USD"
        assert CUR.namespace == "CURRENCY"

    def test_create_specific_currency(self):
        b = create_book(currency="USD")
        CUR = b.commodities[0]
        assert CUR.mnemonic == "USD"
        assert CUR.namespace == "CURRENCY"

        b = create_book(currency="CHF")
        CUR = b.commodities[0]
        assert CUR.mnemonic == "CHF"
        assert CUR.namespace == "CURRENCY"

        with pytest.raises(ValueError):
            b = create_book(currency="ZIE")

    def test_create_named_sqlite_book(self):
        # remove file if left from previous test
        if os.path.exists(db_sqlite):
            os.remove(db_sqlite)

        # assert error if both sqlite_file and uri_conn are defined
        with pytest.raises(ValueError):
            b = create_book(db_sqlite, db_sqlite_uri)

        # assert creation of file
        b = create_book(db_sqlite)
        assert os.path.exists(db_sqlite)
        t = os.path.getmtime(db_sqlite)

        # ensure error if no overwrite
        with pytest.raises(GnucashException):
            b = create_book(db_sqlite)
        assert os.path.getmtime(db_sqlite) == t
        with pytest.raises(GnucashException):
            b = create_book(uri_conn="sqlite:///{}".format(db_sqlite))
        assert os.path.getmtime(db_sqlite) == t
        with pytest.raises(GnucashException):
            b = create_book(db_sqlite, overwrite=False)
        assert os.path.getmtime(db_sqlite) == t

        # if overwrite, DB is recreated
        b = create_book(db_sqlite, overwrite=True)
        assert os.path.getmtime(db_sqlite) > t

        # clean test
        os.remove(db_sqlite)

    def test_create_with_FK(self):
        # create and keep FK
        b = create_book(uri_conn=db_sqlite_uri, keep_foreign_keys=True, overwrite=True)
        b.session.close()

        insp = Inspector.from_engine(create_engine(db_sqlite_uri))
        fk_total = []
        for tbl in insp.get_table_names():
            fk_total.append(insp.get_foreign_keys(tbl))
        assert len(fk_total) == 25

    def test_create_without_FK(self):
        # create without FK
        b = create_book(uri_conn=db_sqlite_uri, keep_foreign_keys=False, overwrite=True, echo=True)
        b.session.close()

        insp = Inspector.from_engine(create_engine(db_sqlite_uri))
        for tbl in insp.get_table_names():
            fk = insp.get_foreign_keys(tbl)
            assert len(fk) == 0


class TestBook_open_book(object):
    def test_open_noarg(self):
        with pytest.raises(ValueError):
            open_book()

    def test_open_default(self, book_uri):
        # open book that does not exists
        with pytest.raises(GnucashException):
            b = open_book(uri_conn=book_uri)

        # create book
        with create_book(uri_conn=book_uri):
            pass

        # assert error if both sqlite_file and uri_conn are defined on open_book
        with pytest.raises(ValueError):
            b = open_book(db_sqlite, db_sqlite_uri)

        # open book that exists
        with open_book(uri_conn=book_uri) as b:
            # try to save (raise as RO per default)
            with pytest.raises(GnucashException):
                b.save()

            # read default currency (to check reading)
            assert b.default_currency.mnemonic == "EUR"

    def test_open_RW_backup(self, book_uri):
        # create book
        with create_book(uri_conn=book_uri) as b:
            engine_type = b.session.bind.name

        # open book with readonly = False (ie RW)
        if engine_type == "postgres":
            # raise an exception as try to do a backup on postgres which is not supported yet
            with pytest.raises(GnucashException):
                b = open_book(uri_conn=book_uri, readonly=False)

        elif engine_type == "sqlite":
            # delete all potential existing backup files
            url = book_uri[len("sqlite:///"):]
            for fn in glob.glob("{}.[0-9]*.gnucash".format(url)):
                os.remove(fn)

            # open file in RW without a backup creation
            with open_book(uri_conn=book_uri, readonly=False, do_backup=False) as b:
                pass

            # check no backup file creation
            assert len(glob.glob("{}.[0-9]*.gnucash".format(url))) == 0

            # open file in RW without a backup creation
            with open_book(uri_conn=book_uri, readonly=False) as b:
                pass

            # check backup file creation
            assert len(glob.glob("{}.[0-9]*.gnucash".format(url))) == 1

    def test_open_lock(self, book_uri):
        # create book and set a lock
        with create_book(uri_conn=book_uri) as b:
            b.session.create_lock()
            b.save()

        # try to open locked book
        with pytest.raises(GnucashException):
            b = open_book(uri_conn=book_uri)

        # open book specifying open_if_lock as True
        with open_book(uri_conn=book_uri, open_if_lock=True) as b:
            pass

        # open book specifying open_if_lock as True and RW to delete lock
        with open_book \
                        (uri_conn=book_uri, open_if_lock=True, readonly=False, do_backup=False) as b:
            b.session.delete_lock()
            b.save()

        # open book specifying open_if_lock as False as lock has been removed
        with open_book(uri_conn=book_uri, open_if_lock=False) as b:
            pass


class TestBook_access_book(object):
    def test_book_options(self, new_book):
        assert new_book.use_trading_accounts == False
        assert new_book.use_split_action_field == False
        assert new_book.RO_threshold_day == 0

        assert len(new_book.slots) == 0

        new_book.use_trading_accounts = True
        assert new_book["options"].value == {'Accounts': {'Use Trading Accounts': 't'}}

        new_book.use_split_action_field = True
        assert new_book["options"].value == {
            'Accounts': {'Use Split Action Field for Number': 't', 'Use Trading Accounts': 't'}}

        new_book.RO_threshold_day = 50
        assert new_book["options"].value == {'Accounts': {'Day Threshold for Read-Only Transactions (red line)': 50.0,
                                                          'Use Split Action Field for Number': 't',
                                                          'Use Trading Accounts': 't'}}

        new_book.RO_threshold_day = 0
        assert new_book["options"].value == {'Accounts': {'Day Threshold for Read-Only Transactions (red line)': 0.0,
                                                          'Use Split Action Field for Number': 't',
                                                          'Use Trading Accounts': 't'}}

        new_book.use_split_action_field = False
        assert new_book["options"].value == {'Accounts': {'Day Threshold for Read-Only Transactions (red line)': 0.0,
                                                          'Use Split Action Field for Number': 'f',
                                                          'Use Trading Accounts': 't'}}
