# -*- coding: latin-1 -*-
import os
import sys
from datetime import datetime
import pytest
from sqlalchemy_utils import database_exists, drop_database
from piecash import create_book, Account, Commodity, Employee, Customer, Vendor, Transaction, Split, Price

test_folder = os.path.dirname(os.path.realpath(__file__))
book_folder = os.path.join(test_folder, "..", "gnucash_books")
file_template = os.path.join(book_folder, "empty_book.gnucash")
file_for_test = os.path.join(test_folder, "empty_book_for_test.gnucash")
file_template_full = os.path.join(book_folder, "test_book.gnucash")
file_for_test_full = os.path.join(test_folder, "test_book_for_test.gnucash")

if sys.version_info.major == 3:
    def run_file(fname):
        with open(fname) as f:
            code = compile(f.read(), fname, 'exec')
            exec (code, {})
else:
    def run_file(fname):
        return execfile(fname, {})

db_sqlite = os.path.join(test_folder, "foozbar.sqlite")

TRAVIS = os.environ.get("TRAVIS", False)
APPVEYOR = os.environ.get("APPVEYOR", False)
LOCALSERVER = os.environ.get("PIECASH_DBSERVER_TEST", False)

db_sqlite_uri = "sqlite:///{}".format(db_sqlite)
databases_to_check = [None,
                      db_sqlite_uri]
db_config = {
    "sqlite": dict(sqlite_file=db_sqlite),
    "sqlite_in_mem": dict(sqlite_file=None),
}

if TRAVIS or LOCALSERVER:
    pg_password = os.environ.get("PG_PASSWORD", "")
    db_user = "travis"
    databases_to_check.append("postgresql://postgres:{pwd}@localhost:5432/foo".format(pwd=pg_password))
    databases_to_check.append("mysql+pymysql://travis:@localhost/foo?charset=utf8")
    db_config.update({
        "postgres": dict(db_type="postgres", db_name="foo",
                         db_user="postgres", db_password=pg_password,
                         db_host="localhost", db_port=5432),
        "mysql": dict(db_type="mysql", db_name="foo",
                      db_user="travis", db_password="",
                      db_host="localhost", db_port=3306),
    })
elif APPVEYOR:
    databases_to_check.append("postgresql://postgres:Password12!@localhost:5432/foo")
    databases_to_check.append("mysql+pymysql://root:Password12!@localhost/foo?charset=utf8")
    db_config.update({
        "postgres": dict(db_type="postgres", db_name="foo",
                         db_user="postgres", db_password="Password12!",
                         db_host="localhost", db_port=5432),
        "mysql": dict(db_type="mysql", db_name="foo",
                      db_user="root", db_password="Password12!",
                      db_host="localhost", db_port=3306),
    })
else:
    pass


@pytest.yield_fixture(params=[Customer, Vendor, Employee])
def Person(request):
    yield request.param


@pytest.yield_fixture(params=db_config.items())
def book_db_config(request):
    from piecash.core.session import build_uri

    sql_backend, db_config = request.param
    name = build_uri(**db_config)

    if sql_backend != "sqlite_in_mem" and database_exists(name):
        drop_database(name)

    yield db_config

    if sql_backend != "sqlite_in_mem" and database_exists(name):
        drop_database(name)


@pytest.yield_fixture(params=databases_to_check[1:])
def book_uri(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)
    yield name

    if name and database_exists(name):
        drop_database(name)


@pytest.yield_fixture(params=databases_to_check)
def new_book(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)

    with create_book(uri_conn=name, keep_foreign_keys=False) as b:
        yield b

    if name and database_exists(name):
        drop_database(name)


@pytest.yield_fixture(params=databases_to_check)
def new_book_USD(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)

    with create_book(uri_conn=name, currency="USD", keep_foreign_keys=False) as b:
        yield b

    if name and database_exists(name):
        drop_database(name)


@pytest.yield_fixture(params=databases_to_check)
def book_basic(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)
    # create new book
    with create_book(uri_conn=name, currency="EUR", keep_foreign_keys=False) as b:
        # create some accounts
        curr = b.currencies[0]
        cdty = Commodity(namespace=u"échange", mnemonic=u"ïoà", fullname=u"Example of unicode déta")
        a = Account(name="asset", type="ASSET", commodity=curr, parent=b.root_account)
        Account(name="broker", type="STOCK", commodity=cdty, parent=a)
        Account(name="exp", type="EXPENSE", commodity=curr, parent=b.root_account)
        Account(name="inc", type="INCOME", commodity=curr, parent=b.root_account)

        yield b

    if name and database_exists(name):
        drop_database(name)


@pytest.yield_fixture(params=databases_to_check)
def book_transactions(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)
    # create new book
    with create_book(uri_conn=name, currency="EUR", keep_foreign_keys=False) as b:
        # create some accounts
        curr = b.default_currency
        other_curr = b.currencies(mnemonic="USD")
        cdty = Commodity(namespace=u"BEL20", mnemonic=u"GnuCash Inc.", fullname=u"GnuCash Inc. stock")
        asset = Account(name="asset", type="ASSET", commodity=curr, parent=b.root_account)
        foreign_asset = Account(name="foreign asset", type="ASSET", commodity=other_curr, parent=b.root_account)
        stock = Account(name="broker", type="STOCK", commodity=cdty, parent=asset)
        expense = Account(name="exp", type="EXPENSE", commodity=curr, parent=b.root_account)
        income = Account(name="inc", type="INCOME", commodity=curr, parent=b.root_account)

        tr1 = Transaction(post_date=datetime(2015, 10, 21),
                          description="my revenue",
                          currency=curr,
                          splits=[
                              Split(account=asset, value=(1000, 1)),
                              Split(account=income, value=(-1000, 1)),
                          ]
                          )
        tr2 = Transaction(post_date=datetime(2015, 10, 25),
                          description="my expense",
                          currency=curr,
                          splits=[
                              Split(account=asset, value=(-100, 1)),
                              Split(account=expense, value=(20, 1), memo="cost of X"),
                              Split(account=expense, value=(80, 1), memo="cost of Y"),
                          ]
                          )
        tr_stock = Transaction(post_date=datetime(2015, 10, 29),
                               description="my purchase of stock",
                               currency=curr,
                               splits=[
                                   Split(account=asset, value=(-200, 1)),
                                   Split(account=expense, value=(15, 1), memo="transaction costs"),
                                   Split(account=stock, value=(185, 1), quantity=(6, 1), memo="purchase of stock"),
                               ]
                               )
        tr_to_foreign = Transaction(post_date=datetime(2015, 10, 30),
                                    description="transfer to foreign asset",
                                    currency=curr,
                                    splits=[
                                        Split(account=asset, value=(-200, 1)),
                                        Split(account=foreign_asset, value=(200, 1), quantity=(135, 1)),
                                    ]
                                    )
        tr_from_foreign = Transaction(post_date=datetime(2015, 10, 31),
                                      description="transfer from foreign asset",
                                      currency=other_curr,
                                      splits=[
                                          Split(account=asset, value=(135, 1), quantity=(215, 1)),
                                          Split(account=foreign_asset, value=(-135, 1)),
                                      ]
                                      )
        Price(commodity=cdty,
              currency=other_curr,
              date=datetime(2015, 11, 1),
              value=(123, 100),
              )
        Price(commodity=cdty,
              currency=other_curr,
              date=datetime(2015, 11, 4),
              value=(127, 100),
              )
        Price(commodity=cdty,
              currency=curr,
              date=datetime(2015, 11, 2),
              value=(234, 100),
              )

        b.save()
        yield b

    if name and database_exists(name):
        drop_database(name)


def is_inmemory_sqlite(book_basic):
    # print book_basic.uri, book_basic.uri.get_dialect(), book_basic.uri.database, type(book_basic.uri), dir(book_basic.uri)
    # print "sqlite" in book_basic.uri and ":memory:" in book_basic.uri
    # fdsfdssfd
    return book_basic.uri.database == ":memory:"


def is_not_on_web():
    return os.environ.get("DONOTGOONWEB", False)
