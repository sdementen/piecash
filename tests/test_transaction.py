# coding=utf-8
from __future__ import unicode_literals
from collections import defaultdict
from datetime import datetime, date
from decimal import Decimal
import pytest
from piecash import Transaction, Split, GncImbalanceError, GncValidationError, Lot
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, book_transactions

# dummy line to avoid removing unused symbols

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, book_transactions


class TestTransaction_create_transaction(object):
    def test_create_basictransaction(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        e = book_basic.accounts(name="exp")

        tr = Transaction(currency=EUR, description=u"wire from Hélène", notes=u"on St-Eugène day",
                         post_date=datetime(2014, 1, 1),
                         enter_date=datetime(2014, 1, 1),
                         splits=[
                             Split(account=a, value=100, memo=u"mémo asset"),
                             Split(account=e, value=-10, memo=u"mémo exp"),
                         ])
        # check issue with balance
        with pytest.raises(GncImbalanceError):
            book_basic.flush()
            book_basic.validate()

        # adjust balance
        Split(account=e, value=-90, memo="missing exp", transaction=tr)
        book_basic.flush()

        # check no issue with str
        assert str(tr)
        assert str(tr.splits)
        assert repr(tr)
        assert repr(tr.splits)

    def test_create_basictransaction_splitfirst(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        e = book_basic.accounts(name="exp")
        s = Split(account=a, value=Decimal(1))
        assert repr(s)

    def test_create_cdtytransaction(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")

        tr = Transaction(currency=EUR, description="buy stock", notes=u"on St-Eugène day",
                         post_date=datetime(2014, 1, 2),
                         enter_date=datetime(2014, 1, 3),
                         splits=[
                             Split(account=a, value=100, memo=u"mémo asset"),
                             Split(account=s, value=-90, memo=u"mémo brok"),
                         ])

        # check issue with quantity for broker split not defined
        with pytest.raises(GncValidationError):
            book_basic.validate()

        sb = tr.splits(account=s)
        sb.quantity = 15

        # check issue with quantity not same sign as value
        with pytest.raises(GncValidationError):
            book_basic.validate()

        sb.quantity = -15

        # verify imbalance issue
        with pytest.raises(GncImbalanceError):
            book_basic.validate()

        # adjust balance
        Split(account=a, value=-10, memo="missing asset corr", transaction=tr)
        book_basic.save()
        assert str(sb)
        assert str(sb)

        # changing currency of an existing transaction is not allowed
        tr.currency = book_basic.currencies(mnemonic="USD")
        with pytest.raises(GncValidationError):
            book_basic.validate()
        book_basic.cancel()

        # check sum of quantities are not balanced per commodity but values are
        d = defaultdict(lambda: Decimal(0))
        for sp in tr.splits:
            assert sp.quantity == sp.value or sp.account != a
            d[sp.account.commodity] += sp.quantity
            d["cur"] += sp.value
        assert d["cur"] == 0
        assert all([v != 0 for k, v in d.items() if k != "cur"])

    def test_create_cdtytransaction_cdtycurrency(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")

        tr = Transaction(currency=s.commodity, description="buy stock", notes=u"on St-Eugène day",
                         post_date=datetime(2014, 1, 2),
                         enter_date=datetime(2014, 1, 3),
                         splits=[
                             Split(account=a, value=100, quantity=10, memo=u"mémo asset"),
                             Split(account=s, value=-100, quantity=-10, memo=u"mémo brok"),
                         ])
        # raise error as Transaction has a non CURRENCY commodity
        with pytest.raises(GncValidationError):
            book_basic.validate()

    def test_create_cdtytransaction_tradingaccount(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")

        book_basic.use_trading_accounts = True
        tr = Transaction(currency=EUR, description="buy stock", notes=u"on St-Eugène day",
                         post_date=datetime(2014, 1, 2),
                         enter_date=datetime(2014, 1, 3),
                         splits=[
                             Split(account=a, value=100, memo=u"mémo asset"),
                             Split(account=s, value=-100, quantity=-15, memo=u"mémo brok"),
                         ])
        book_basic.validate()

        assert "{}".format(tr) == "Transaction<[EUR] 'buy stock' on 2014-01-02>"
        assert "{}".format(s) == "Account<asset:broker[ïoà]>"
        assert "{}".format(tr.splits(account=s)) == "Split<Account<asset:broker[ïoà]> -100 EUR [-15 ïoà]>"
        assert "{}".format(tr.splits(account=a)) == "Split<Account<asset[EUR]> 100 EUR>"

        # check sum of quantities are all balanced per commodity as values are
        d = defaultdict(lambda: Decimal(0))
        for sp in tr.splits:
            assert sp.quantity == sp.value or sp.account != a
            d[sp.account.commodity] += sp.quantity
            d["cur"] += sp.value

        assert d["cur"] == 0
        assert all([v == Decimal(0) for k, v in d.items() if k != "cur"])

        # change existing quantity
        sp = tr.splits(memo=u"mémo brok")
        sp.quantity += 1
        book_basic.validate()

        # check sum of quantities are all balanced per commodity as values are
        d = defaultdict(lambda: Decimal(0))
        for sp in tr.splits:
            assert sp.quantity == sp.value or sp.account != a
            d[sp.account.commodity] += sp.quantity
            d["cur"] += sp.value
        assert d["cur"] == 0
        assert all([v == Decimal(0) for k, v in d.items() if k != "cur"])


class TestTransaction_lots(object):
    def test_create_simpletlot_addsplits(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")
        l = Lot(title=u"test mé", account=s, notes=u"ïlya")
        for i, am in enumerate([45, -35, -20]):
            tr = Transaction(currency=EUR, description="trade stock", notes=u"àçö",
                             post_date=datetime(2014, 1, 1 + i),
                             enter_date=datetime(2014, 1, 1 + i),
                             splits=[
                                 Split(account=a, value=am * 10, memo=u"mémo asset"),
                                 Split(account=s, value=-am * 10, quantity=-am, memo=u"mémo brok", lot=l),
                             ])
        book_basic.flush()

    def test_create_simpletlot_initialsplits(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")
        sp = []
        for i, am in enumerate([45, -35, -20]):
            tr = Transaction(currency=EUR, description="trade stock", notes=u"àçö",
                             post_date=datetime(2014, 1, 1 + i),
                             enter_date=datetime(2014, 1, 1 + i),
                             splits=[
                                 Split(account=a, value=am * 10, memo=u"mémo asset"),
                                 Split(account=s, value=-am * 10, quantity=-am, memo=u"mémo brok"),
                             ])
            sp.append(tr.splits(account=s))

        l = Lot(title=u"test mé", account=s, notes=u"ïlya", splits=sp)
        book_basic.flush()

    def test_create_closedlot_addsplits(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")
        l = Lot(title=u"test mé", account=s, notes=u"ïlya")
        l.is_closed = 1
        # raise valueerror as lot is closed
        with pytest.raises(ValueError):
            tr = Transaction(currency=EUR, description="trade stock", notes=u"àçö",
                             post_date=datetime(2014, 1, 1),
                             enter_date=datetime(2014, 1, 1),
                             splits=[
                                 Split(account=a, value=10, memo=u"mémo asset"),
                                 Split(account=s, value=- 10, quantity=-2, memo=u"mémo brok", lot=l),
                             ])

    def test_create_simplelot_inconsistentaccounts(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")
        l = Lot(title=u"test mé", account=a, notes=u"ïlya")
        # raise valueerror as split account not the same as lot account
        tr = Transaction(currency=EUR, description="trade stock", notes=u"àçö",
                         post_date=datetime(2014, 1, 1),
                         enter_date=datetime(2014, 1, 1),
                         splits=[
                             Split(account=a, value=10, memo=u"mémo asset"),
                             Split(account=s, value=- 10, quantity=-2, memo=u"mémo brok", lot=l),
                         ])

        with pytest.raises(ValueError):
            book_basic.validate()


class TestTransaction_changes(object):
    def test_delete_existing_transaction(self, book_transactions):
        l = len(book_transactions.transactions)
        s = len(book_transactions.splits)
        tr = book_transactions.transactions(description="my revenue")
        book_transactions.delete(tr)
        book_transactions.save()
        nl = len(book_transactions.transactions)
        ns = len(book_transactions.splits)
        assert nl == l - 1
        assert ns == s - 2

    def test_change_cdty_split_price(self, book_transactions):
        tr = book_transactions.transactions(description="my purchase of stock")
        sp = tr.splits(account=book_transactions.accounts(name="broker"))

        assert len(book_transactions.prices) == 6

        p = [p for p in book_transactions.prices if p.date.day == 29][0]
        assert p.value == (sp.value / sp.quantity).quantize(Decimal("0.000001"))

        # changing the quantity of the split should change the existing price
        sp.quantity = (5, 1)
        book_transactions.validate()
        assert len(book_transactions.prices) == 6
        assert p.value == (sp.value / sp.quantity).quantize(Decimal("0.000001"))

        # changing the post date of the transaction of the split should create a new price
        tr.post_date = datetime(2015, 1, 29, tzinfo=tr.post_date.tzinfo)
        book_transactions.validate()
        assert len(book_transactions.prices) == 7
