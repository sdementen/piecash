# coding=utf-8
from __future__ import unicode_literals

from piecash import create_book, Account, open_book
from piecash.core.session import build_uri
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_db_config


# dummy line to avoid removing unused symbols
a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_db_config


class TestSession_create_book(object):
    def test_create_default(self, book_db_config):
        b = create_book(keep_foreign_keys=False, **book_db_config)
        a = Account(commodity=b.currencies(mnemonic="SEK"),
                    parent=b.root_account,
                    name="léviö",
                    type="ASSET")
        assert str(b.uri) == build_uri(**book_db_config)
        b.save()
        b.session.close()

        # reopen the DB except if sqlite_file is None
        if book_db_config.get("sqlite_file", True):
            b = open_book(**book_db_config)
            assert b.accounts(name="léviö").commodity == b.currencies(mnemonic="SEK")
