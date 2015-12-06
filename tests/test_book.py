import glob
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session
from piecash import create_book, Account, GnucashException, Book, open_book, Commodity
from piecash.core import Version
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_transactions

# dummy line to avoid removing unused symbols
a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_transactions


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
        assert len(new_book.slots) == 1

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
        b = create_book(uri_conn=db_sqlite_uri, keep_foreign_keys=False, overwrite=True)
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
        if engine_type != "sqlite":
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

        new_book.use_trading_accounts = False
        new_book.use_split_action_field = False
        new_book.RO_threshold_day = 0

        assert new_book.use_trading_accounts == False
        assert new_book.use_split_action_field == False
        assert new_book.RO_threshold_day == 0

        assert len(new_book.slots) == 1

        with pytest.raises(KeyError):
            new_book["options"]

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
        assert new_book["options"].value == {'Accounts': {'Use Split Action Field for Number': 't',
                                                          'Use Trading Accounts': 't'}}

        new_book.use_split_action_field = False
        assert new_book["options"].value == {'Accounts': {'Use Trading Accounts': 't'}}

        del new_book["options"]
        with pytest.raises(KeyError):
            new_book["options"]

        assert new_book.control_mode == []

    def test_book_trading_accounts(self, new_book):
        assert len(new_book.accounts) == 0
        assert len(new_book.currencies) == 1

        # get (and create on the fly) the trading account for the default currency
        ncur = new_book.currencies(mnemonic="USD")
        cur = new_book.default_currency

        ta = new_book.trading_account(ncur)
        new_book.flush()
        assert len(new_book.currencies) == 2
        assert len(new_book.accounts) == 3
        acc = new_book.root_account.children[0]
        assert acc.name == "Trading"
        assert acc.commodity == cur
        acc = acc.children[0]
        assert acc.name == cur.namespace
        assert acc.commodity == cur
        acc = acc.children[0]
        assert acc.name == ncur.mnemonic
        assert acc.commodity == ncur

        ncur = new_book.currencies(mnemonic="CAD")
        ta = new_book.trading_account(ncur)
        new_book.flush()
        assert len(new_book.accounts) == 4
        assert len(new_book.currencies) == 3

        ncur = new_book.currencies(mnemonic="USD")
        ta = new_book.trading_account(ncur)
        assert len(new_book.accounts) == 4
        assert len(new_book.currencies) == 3

    def test_book_transactions(self, new_book):
        ncur = new_book.currencies(mnemonic="CAD")
        new_book.flush()
        assert len(new_book.currencies) == 2
        assert not new_book.is_saved
        new_book.cancel()
        assert new_book.is_saved
        assert len(new_book.currencies) == 1
        nncur = new_book.currencies(mnemonic="USD")
        new_book.flush()
        assert not new_book.is_saved
        assert len(new_book.currencies) == 2
        new_book.save()
        assert new_book.is_saved
        assert len(new_book.currencies) == 2
        new_book.delete(nncur)
        assert not new_book.is_saved
        assert len(new_book.currencies) == 1
        new_book.save()
        assert new_book.is_saved
        assert len(new_book.currencies) == 1
        nncur = new_book.currencies(mnemonic="USD")
        new_book.flush()
        assert len(new_book.currencies) == 2
        assert not new_book.is_saved

    def test_book_getters(self, new_book):
        cur = new_book.currencies[0]
        assert cur == new_book.get(Commodity, mnemonic=cur.mnemonic)

        with pytest.raises(ValueError):
            new_book.get(Commodity, mnemonic="FOO")

        with pytest.raises(ValueError):
            new_book.get(Commodity, mnemonic="CAD")

        assert new_book.get(Commodity).all() == [cur]

        assert new_book.accounts == []
        assert new_book.transactions == []
        assert new_book.commodities == [cur]
        assert new_book.currencies == [cur]
        assert new_book.prices == []
        assert new_book.customers == []
        assert new_book.vendors == []
        assert new_book.employees == []
        assert new_book.taxtables == []

    def test_splits_df(self, book_transactions):
        df = book_transactions.splits_df().reset_index()

        # remove guid columns as not comparable from run to run
        for col in df.columns:
            if "guid" in col:
                del df[col]

        # converte datetime to date as different tzone in CI environments
        df["transaction.post_date"] = df["transaction.post_date"].dt.date

        df_to_string = """    value quantity transaction.post_date transaction.currency.mnemonic account.fullname account.commodity.mnemonic
0   -1000    -1000            2015-10-21                           EUR              inc                        EUR
1    1000     1000            2015-10-21                           EUR            asset                        EUR
2    -100     -100            2015-10-25                           EUR            asset                        EUR
3      20       20            2015-10-25                           EUR              exp                        EUR
4      80       80            2015-10-25                           EUR              exp                        EUR
5    -200     -200            2015-10-29                           EUR            asset                        EUR
6      15       15            2015-10-29                           EUR              exp                        EUR
7     185        6            2015-10-29                           EUR     asset:broker               GnuCash Inc.
8    -200     -200            2015-10-30                           EUR            asset                        EUR
9     200      135            2015-10-30                           EUR    foreign asset                        USD
10   -135     -135            2015-10-31                           USD    foreign asset                        USD
11    135      215            2015-10-31                           USD            asset                        EUR"""

        assert df_to_string == df.to_string()

    def test_prices_df(self, book_transactions):
        df = book_transactions.prices_df().reset_index()

        # remove guid columns as not comparable from run to run
        for col in df.columns:
            if "guid" in col:
                del df[col]

        # converte datetime to date as different tzone in CI environments
        df["date"] = df["date"].dt.date

        df_to_string = """   index        date         type      value commodity.mnemonic currency.mnemonic
0      0  2015-10-31  transaction   0.627907                EUR               USD
1      1  2015-10-29  transaction  30.833333       GnuCash Inc.               EUR
2      2  2015-11-01      unknown       1.23       GnuCash Inc.               USD
3      3  2015-11-02      unknown       2.34       GnuCash Inc.               EUR
4      4  2015-11-04      unknown       1.27       GnuCash Inc.               USD
5      5  2015-10-30  transaction   1.481481                USD               EUR"""

        assert df_to_string == df.to_string()
