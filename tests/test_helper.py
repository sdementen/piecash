# -*- coding: latin-1 -*-
import os.path
import sys
import pytest
from sqlalchemy_utils import database_exists, drop_database
from piecash import create_book, Account, Commodity

test_folder = os.path.dirname(os.path.realpath(__file__))
book_folder = os.path.join(test_folder, "..", "gnucash_books")
file_template = os.path.join(book_folder, "empty_book.gnucash")
file_for_test = os.path.join(test_folder, "empty_book_for_test.gnucash")
file_template_full = os.path.join(book_folder, "test_book.gnucash")
file_for_test_full = os.path.join(test_folder, "test_book_for_test.gnucash")

if sys.version_info.major==3:
    def run_file(fname):
        with open(fname) as f:
            code = compile(f.read(), fname, 'exec')
            exec(code, {})
else:
    def run_file(fname):
        return execfile(fname, {})

db_sqlite = os.path.join(test_folder, "fooze.sqlite")
if os.environ.get("TRAVIS", False):
    pg_password = ''
else:
    pg_password = os.environ.get("PG_PASSWORD")
db_postgres_uri = "postgresql://postgres:{pwd}@localhost:5432/foo".format(pwd=pg_password)
db_mysql_uri = "mysql+pymysql://travis:@localhost/foo?charset=utf8"
db_sqlite_uri = "sqlite:///{}".format(db_sqlite)

db_config = {
    "postgres" : dict(db_type="postgres", db_name="foo",
                      db_user="postgres", db_password=pg_password,
                      db_host="localhost", db_port=5432),
    "mysql" : dict(db_type="mysql", db_name="foo",
                      db_user="travis", db_password="",
                      db_host="localhost", db_port=3306),
    "sqlite": dict(sqlite_file=db_sqlite),
    "sqlite_in_mem": dict(sqlite_file=None),
}


databases_to_check = [None, db_sqlite_uri]
if os.environ.get("TRAVIS", False):
    databases_to_check.append(db_postgres_uri)
    databases_to_check.append(db_mysql_uri)
elif os.environ.get("PIECASH_DBSERVER_TEST", False):
    databases_to_check.append(db_postgres_uri)
    databases_to_check.append(db_mysql_uri)
    db_config.pop("mysql")
else:
    db_config.pop("mysql")
    db_config.pop("postgres")

@pytest.yield_fixture(params=db_config.items())
def book_db_config(request):
    from piecash.core.session import build_uri

    sql_backend, db_config = request.param
    name = build_uri(**db_config)

    if sql_backend!="sqlite_in_mem" and database_exists(name):
        drop_database(name)

    yield db_config

    if sql_backend!="sqlite_in_mem"  and database_exists(name):
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
    b = create_book(uri_conn=name, keep_foreign_keys=False)
    yield b
    b.session.close()
    if name and database_exists(name):
        drop_database(name)


@pytest.yield_fixture(params=databases_to_check)
def new_book_USD(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)
    b = create_book(uri_conn=name, currency="USD", keep_foreign_keys=False)
    yield b
    b.session.close()
    if name and database_exists(name):
        drop_database(name)

@pytest.yield_fixture(params=databases_to_check)
def book_basic(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)
    # create new book
    b = create_book(uri_conn=name, currency="EUR", keep_foreign_keys=False)
    # create some accounts
    curr = b.currencies[0]
    cdty = Commodity(namespace=u"échange",mnemonic=u"ïoà", fullname=u"Example of unicode déta")
    a = Account(name="asset", type="ASSET", commodity=curr, parent=b.root_account)
    Account(name="broker", type="STOCK", commodity=cdty, parent=a)
    Account(name="exp", type="EXPENSE", commodity=curr, parent=b.root_account)
    Account(name="inc", type="INCOME", commodity=curr, parent=b.root_account)

    b.flush()
    yield b
    b.session.close()
    if name and database_exists(name):
        drop_database(name)
