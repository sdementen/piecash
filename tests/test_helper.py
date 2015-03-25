import os.path
import sys
import pytest
from sqlalchemy_utils import database_exists, drop_database
from piecash import create_book

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
db_postgres_uri = "postgresql://postgres:@localhost:5432/foo"
db_mysql_uri = "mysql+pymysql://travis:@localhost/foo"
db_sqlite_uri = "sqlite:///{}".format(db_sqlite)

databases_to_check = [None, db_sqlite_uri]
if os.environ.get("TRAVIS", False):
    databases_to_check.append(db_postgres_uri)
    databases_to_check.append(db_mysql_uri)

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
    b = create_book(uri_conn=name)
    yield b
    b.session.close()
    if name and database_exists(name):
        drop_database(name)

@pytest.yield_fixture(params=databases_to_check)
def new_book_USD(request):
    name = request.param

    if name and database_exists(name):
        drop_database(name)
    b = create_book(uri_conn=name, currency="USD")
    yield b
    b.session.close()
    if name and database_exists(name):
        drop_database(name)
