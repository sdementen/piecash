# coding=utf-8
from __future__ import unicode_literals

import locale
import sys
from contextlib import contextmanager

import pytest


from piecash import create_book, Account, open_book
from piecash._common import get_system_currency_mnemonic
from piecash.core.session import build_uri
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_db_config

# dummy line to avoid removing unused symbols
a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_db_config


class TestSession_create_book(object):
    def test_create_default(self, book_db_config):
        with create_book(keep_foreign_keys=False, **book_db_config) as b:
            a = Account(commodity=b.currencies(mnemonic="SEK"),
                        parent=b.root_account,
                        name="léviö",
                        type="ASSET")
            assert str(b.uri) == build_uri(**book_db_config)
            b.save()

        # reopen the DB except if sqlite_file is None
        if book_db_config.get("sqlite_file", True):
            with open_book(**book_db_config) as b:
                assert b.accounts(name="léviö").commodity == b.currencies(mnemonic="SEK")

    def test_build_uri(self):
        assert build_uri() == "sqlite:///:memory:"
        assert build_uri(sqlite_file="foo") == "sqlite:///foo"
        assert build_uri(uri_conn="sqlite:///foo") == "sqlite:///foo"
        with pytest.raises(ValueError):
            build_uri(db_name="f")

        with pytest.raises(KeyError):
            build_uri(db_type="pg",
                      db_user="foo",
                      db_password="pp",
                      db_name="pqsd",
                      db_host="qsdqs",
                      db_port=3434)

        assert build_uri(db_type="postgres",
                         db_user="foo",
                         db_password="pp",
                         db_name="pqsd",
                         db_host="qsdqs",
                         db_port=3434) == "postgresql://foo:pp@qsdqs:3434/pqsd"

        assert build_uri(db_type="mysql",
                         db_user="foo",
                         db_password="pp",
                         db_name="pqsd",
                         db_host="qsdqs",
                         db_port=3434) == "mysql+pymysql://foo:pp@qsdqs:3434/pqsd?charset=utf8"

        ### Test duplicate protocol spec. This happens when the open_book is called
        ### from GnuCash reports (.scm), gnucash-utilities.
        sqlite_uri = "sqlite:///some_file"
        uri = "sqlite:///some_file"
        assert build_uri(sqlite_file=uri) == sqlite_uri
        # When run with just the name (without sqlite:// prefix):
        uri = "some_file"
        assert build_uri(sqlite_file=uri) == sqlite_uri


@contextmanager
def locale_ctx(l):
    _l = locale.getlocale()

    locale.setlocale(locale.LC_ALL, l)

    yield

    locale.setlocale(locale.LC_ALL, _l)


if sys.platform == "win32":
    locales = {
        'English_United States.1252': "USD",
        'French_France.1252': "EUR",
    }
else:
    locales = {
        'en_US.UTF-8': "USD",
        'fr_FR.UTF-8': "EUR",
    }


@pytest.yield_fixture(params=locales)
def locale_set(request):
    yield request.param

def test_get_system_currency_mnemonic(locale_set):
    result = locales[locale_set]
    with locale_ctx(locale_set):
        assert get_system_currency_mnemonic() == result
