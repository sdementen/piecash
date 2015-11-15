# coding=utf-8
from __future__ import unicode_literals
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import pytest
from piecash import Transaction, Split, GncImbalanceError, GncValidationError, Lot, GnucashException, Commodity
from piecash.core import factories
from piecash.core.factories import create_stock_accounts
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic

# dummy line to avoid removing unused symbols

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic


class TestFactories(object):
    def test_create_stock_accounts_simple(self, book_basic):
        with pytest.raises(GnucashException):
            factories.create_stock_accounts(book_basic.default_currency,
                                            broker_account=book_basic.accounts(name="broker"))

        broker = book_basic.accounts(name="broker")
        appl = Commodity(namespace="NMS", mnemonic="AAPL", fullname="Apple")
        acc, inc_accounts = factories.create_stock_accounts(appl,
                                                            broker_account=broker)

        assert inc_accounts == []
        assert broker.children == [acc]

    def test_create_stock_accounts_incomeaccounts(self, book_basic):
        broker = book_basic.accounts(name="broker")
        income = book_basic.accounts(name="inc")

        appl = Commodity(namespace="NMS", mnemonic="AAPL", fullname="Apple")
        appl["quoted_currency"]="USD"
        acc, inc_accounts = factories.create_stock_accounts(appl,
                                                            broker_account=broker,
                                                            income_account=income,
                                                            income_account_types="D")
        assert len(inc_accounts)==1

        acc, inc_accounts = factories.create_stock_accounts(appl,
                                                            broker_account=broker,
                                                            income_account=income,
                                                            income_account_types="CL")
        assert len(inc_accounts)==1
        acc, inc_accounts = factories.create_stock_accounts(appl,
                                                            broker_account=broker,
                                                            income_account=income,
                                                            income_account_types="CS")
        assert len(inc_accounts)==1
        acc, inc_accounts = factories.create_stock_accounts(appl,
                                                            broker_account=broker,
                                                            income_account=income,
                                                            income_account_types="I")
        assert len(inc_accounts)==1
        acc, inc_accounts = factories.create_stock_accounts(appl,
                                                            broker_account=broker,
                                                            income_account=income,
                                                            income_account_types="D/CL/CS/I")
        assert len(income.children)==4
        assert sorted(income.children,key=lambda x:x.guid) == sorted([_acc.parent for _acc in inc_accounts],key=lambda x:x.guid)
        assert broker.children == [acc]


    def test_create_stock_from_symbol(self, book_basic):
        factories.create_stock_from_symbol("AAPL", book_basic)


    def test_create_currency_from_ISO(self, book_basic):
        assert factories.create_currency_from_ISO("CAD").fullname=="Canadian Dollar"

        with pytest.raises(ValueError):
            factories.create_currency_from_ISO("EFR").fullname

    def test_create_currency_from_ISO_web(self, book_basic):
        assert factories.create_currency_from_ISO("CAD", from_web=True).fullname=="Canadian Dollar"