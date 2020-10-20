# coding=utf-8
from __future__ import unicode_literals

from datetime import datetime
from decimal import Decimal

import pytest
import tzlocal

from piecash import GnucashException, Commodity
from piecash.core import factories
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, needweb

# dummy line to avoid removing unused symbols

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic


class TestFactoriesCommodities(object):
    def test_create_stock_accounts_simple(self, book_basic):
        with pytest.raises(GnucashException):
            factories.create_stock_accounts(
                book_basic.default_currency, broker_account=book_basic.accounts(name="broker")
            )

        broker = book_basic.accounts(name="broker")
        appl = Commodity(namespace="NMS", mnemonic="AAPL", fullname="Apple")
        acc, inc_accounts = factories.create_stock_accounts(appl, broker_account=broker)

        assert inc_accounts == []
        assert broker.children == [acc]

    def test_create_stock_accounts_incomeaccounts(self, book_basic):
        broker = book_basic.accounts(name="broker")
        income = book_basic.accounts(name="inc")

        appl = Commodity(namespace="NMS", mnemonic="AAPL", fullname="Apple")
        appl["quoted_currency"] = "USD"
        acc, inc_accounts = factories.create_stock_accounts(
            appl, broker_account=broker, income_account=income, income_account_types="D"
        )
        assert len(inc_accounts) == 1

        acc, inc_accounts = factories.create_stock_accounts(
            appl, broker_account=broker, income_account=income, income_account_types="CL"
        )
        assert len(inc_accounts) == 1
        acc, inc_accounts = factories.create_stock_accounts(
            appl, broker_account=broker, income_account=income, income_account_types="CS"
        )
        assert len(inc_accounts) == 1
        acc, inc_accounts = factories.create_stock_accounts(
            appl, broker_account=broker, income_account=income, income_account_types="I"
        )
        assert len(inc_accounts) == 1
        acc, inc_accounts = factories.create_stock_accounts(
            appl, broker_account=broker, income_account=income, income_account_types="D/CL/CS/I"
        )
        assert len(income.children) == 4
        book_basic.flush()
        assert sorted(income.children, key=lambda x: x.guid) == sorted(
            [_acc.parent for _acc in inc_accounts], key=lambda x: x.guid
        )
        assert broker.children == [acc]

    @needweb
    def test_create_stock_from_symbol(self, book_basic):
        assert len(book_basic.commodities) == 2

        factories.create_stock_from_symbol("AAPL", book_basic)

        assert len(book_basic.commodities) == 3

        cdty = book_basic.commodities(mnemonic="AAPL")

        assert cdty.namespace == "NMS"
        assert cdty.quote_tz == "America/New_York"
        assert cdty.quote_source == "yahoo"
        assert cdty.mnemonic == "AAPL"
        assert cdty.fullname == "Apple Inc."

    def test_create_currency_from_ISO(self, book_basic):
        assert factories.create_currency_from_ISO("CAD").fullname == "Canadian Dollar"

        with pytest.raises(ValueError):
            factories.create_currency_from_ISO("EFR").fullname


class TestFactoriesTransactions(object):
    def test_single_transaction(self, book_basic):
        today = datetime.today()
        print("today=", today)
        factories.single_transaction(
            today.date(),
            today,
            "my test",
            Decimal(100),
            from_account=book_basic.accounts(name="inc"),
            to_account=book_basic.accounts(name="asset"),
        )
        book_basic.save()
        tr = book_basic.transactions(description="my test")
        assert len(tr.splits) == 2
        sp1, sp2 = tr.splits
        if sp1.value > 0:
            sp2, sp1 = sp1, sp2
        # sp1 has negative value
        assert sp1.account == book_basic.accounts(name="inc")
        assert sp2.account == book_basic.accounts(name="asset")
        assert sp1.value == -sp2.value
        assert sp1.quantity == sp1.value
        assert tr.enter_date == tzlocal.get_localzone().localize(today.replace(microsecond=0))
        assert tr.post_date == tzlocal.get_localzone().localize(today).date()

    def test_single_transaction_tz(self, book_basic):
        today = tzlocal.get_localzone().localize(datetime.today())
        tr = factories.single_transaction(
            today.date(),
            today,
            "my test",
            Decimal(100),
            from_account=book_basic.accounts(name="inc"),
            to_account=book_basic.accounts(name="asset"),
        )
        book_basic.save()
        tr = book_basic.transactions(description="my test")
        assert tr.post_date == today.date()
        assert tr.enter_date == today.replace(microsecond=0)

    def test_single_transaction_rollback(self, book_basic):
        today = tzlocal.get_localzone().localize(datetime.today())
        factories.single_transaction(
            today.date(),
            today,
            "my test",
            Decimal(100),
            from_account=book_basic.accounts(name="inc"),
            to_account=book_basic.accounts(name="asset"),
        )
        book_basic.validate()
        assert len(book_basic.transactions) == 1
        book_basic.cancel()
        assert len(book_basic.transactions) == 0
