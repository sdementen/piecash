# coding=utf-8
from __future__ import unicode_literals

from collections import defaultdict
from datetime import datetime, date, time
from decimal import Decimal

import pytest

from piecash import Transaction, Split, GncImbalanceError, GncValidationError, Lot
from test_helper import (
    db_sqlite_uri,
    db_sqlite,
    new_book,
    new_book_USD,
    book_uri,
    book_basic,
    book_transactions,
)

# dummy line to avoid removing unused symbols

a = (
    db_sqlite_uri,
    db_sqlite,
    new_book,
    new_book_USD,
    book_uri,
    book_basic,
    book_transactions,
)


class TestTransaction_create_transaction(object):
    def test_create_basictransaction_neutraltime(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        e = book_basic.accounts(name="exp")

        tr = Transaction(
            currency=EUR,
            description="wire from Hélène",
            notes="on St-Eugène day",
            post_date=date(2014, 1, 1),
            splits=[
                Split(account=a, value=100, memo="mémo asset"),
                Split(account=e, value=-100, memo="mémo exp"),
            ],
        )

        assert isinstance(tr.post_date, date)

        book_basic.flush()
        book_basic.validate()

        assert isinstance(tr.post_date, date)

    def test_create_basictransaction_validation_date(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        e = book_basic.accounts(name="exp")

        splits = [
            Split(account=a, value=100, memo="mémo asset"),
            Split(account=e, value=-10, memo="mémo exp"),
        ]

        with pytest.raises(GncValidationError):
            tr = Transaction(
                currency=EUR,
                description="wire from Hélène",
                notes="on St-Eugène day",
                post_date=datetime(2014, 1, 1),
                enter_date=datetime(2014, 1, 1),
                splits=splits,
            )
            book_basic.add(tr)

        with pytest.raises(GncValidationError):
            tr = Transaction(
                currency=EUR,
                description="wire from Hélène",
                notes="on St-Eugène day",
                post_date=datetime(2014, 1, 1),
                enter_date=time(10, 59, 00),
                splits=splits,
            )
            book_basic.add(tr)

        with pytest.raises(GncValidationError):
            tr = Transaction(
                currency=EUR,
                description="wire from Hélène",
                notes="on St-Eugène day",
                post_date=date(2014, 1, 1),
                enter_date=date(2014, 1, 1),
                splits=splits,
            )
            book_basic.add(tr)

        tr = Transaction(
            currency=EUR,
            description="wire from Hélène",
            notes="on St-Eugène day",
            post_date=None,
            enter_date=None,
            splits=splits,
        )
        book_basic.add(tr)

        with pytest.raises(GncImbalanceError):
            book_basic.flush()
            book_basic.validate()

    def test_create_basictransaction(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        e = book_basic.accounts(name="exp")

        tr = Transaction(
            currency=EUR,
            description="wire from Hélène",
            notes="on St-Eugène day",
            post_date=date(2014, 1, 1),
            enter_date=datetime(2014, 1, 1),
            splits=[
                Split(account=a, value=100, memo="mémo asset"),
                Split(account=e, value=-10, memo="mémo exp"),
            ],
        )
        book_basic.add(tr)
        # check issue with balance
        with pytest.raises(GncImbalanceError):
            book_basic.flush()
            book_basic.validate()

        # adjust balance
        book_basic.add(Split(account=e, value=-90, memo="missing exp", transaction=tr))
        book_basic.flush()

        # check no issue with str
        assert str(tr)
        assert str(tr.splits)
        assert repr(tr)
        assert repr(tr.splits)
        assert tr.notes == "on St-Eugène day"

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

        tr = Transaction(
            currency=EUR,
            description="buy stock",
            notes="on St-Eugène day",
            post_date=date(2014, 1, 2),
            enter_date=datetime(2014, 1, 3),
            splits=[
                Split(account=a, value=100, memo="mémo asset"),
                Split(account=s, value=-90, memo="mémo brok"),
            ],
        )
        book_basic.add(tr)

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
        book_basic.add(Split(account=a, value=-10, memo="missing asset corr", transaction=tr))
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

    def test_create_split_overflow(self, book_basic):
        a = book_basic.accounts(name="asset")

        # raise error as Transaction has a non CURRENCY commodity
        with pytest.raises(TypeError):
            sp = Split(account=a, value=1.0 / 3.0, quantity=10, memo="mémo asset")

        with pytest.raises(ValueError):
            sp = Split(
                account=a, value=Decimal(1) / Decimal(3), quantity=10, memo="mémo asset"
            )

        sp = Split(
            account=a,
            value=Decimal(1234567890123455678),
            quantity=10,
            memo="mémo asset",
        )

        with pytest.raises(ValueError):
            sp = Split(
                account=a,
                value=Decimal(1234567890123455678901234),
                quantity=10,
                memo="mémo asset",
            )

    def test_create_cdtytransaction_cdtycurrency(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")

        tr = Transaction(
            currency=s.commodity,
            description="buy stock",
            notes="on St-Eugène day",
            post_date=date(2014, 1, 2),
            enter_date=datetime(2014, 1, 3),
            splits=[
                Split(account=a, value=100, quantity=10, memo="mémo asset"),
                Split(account=s, value=-100, quantity=-10, memo="mémo brok"),
            ],
        )
        book_basic.add(tr)
        # raise error as Transaction has a non CURRENCY commodity
        with pytest.raises(GncValidationError):
            book_basic.validate()

    def test_create_cdtytransaction_tradingaccount(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")

        book_basic.use_trading_accounts = True
        tr = Transaction(
            currency=EUR,
            description="buy stock",
            notes="on St-Eugène day",
            post_date=date(2014, 1, 2),
            enter_date=datetime(2014, 1, 3),
            splits=[
                Split(account=a, value=100, memo="mémo asset"),
                Split(account=s, value=-100, quantity=-15, memo="mémo brok"),
            ],
        )
        book_basic.add(tr)
        book_basic.validate()

        assert "{}".format(tr) == "Transaction<[EUR] 'buy stock' on 2014-01-02>"
        assert "{}".format(s) == "Account<asset:broker[ïoà]>"
        assert (
            "{}".format(tr.splits(account=s))
            == "Split<Account<asset:broker[ïoà]> -100 EUR [-15 ïoà]>"
        )
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
        sp = tr.splits(memo="mémo brok")
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

    def test_tag_split_zero_quantity(self, book_transactions):
        broker = book_transactions.accounts(name="broker")
        asset = book_transactions.accounts.get(name="asset")
        inc = book_transactions.accounts.get(name="inc")
        currency = book_transactions.default_currency

        value = Decimal(250)
        splits = [
            Split(asset, value),
            Split(inc, -value),
            Split(
                broker, value=0, quantity=0
            ),  # tag split for assigning dividend income to stock
        ]

        Transaction(currency, description="Dividend income", splits=splits)

        book_transactions.validate()

    def test_tag_split_zero_quantity_with_value(self, book_transactions):
        broker = book_transactions.accounts(name="broker")
        inc = book_transactions.accounts.get(name="inc")
        value = Decimal(250)

        # Transaction recording capital gains.
        splits = [
            Split(broker, value, quantity=0),
            Split(inc, -value),
        ]
        Transaction(inc.commodity, description="Capital gains", splits=splits)
        book_transactions.validate()

        # Transaction recording capital loss.
        splits = [
            Split(broker, -value, quantity=0),
            Split(inc, value),
        ]
        Transaction(inc.commodity, description="Capital loss", splits=splits)
        book_transactions.validate()

        # Do the same tests with a -0.0 quantity. This Decimal has is_signed=True.
        mzero = Decimal("-0.00")

        # Transaction recording capital gains.
        splits = [
            Split(broker, value, quantity=mzero),
            Split(inc, -value),
        ]
        Transaction(inc.commodity, description="Capital gains", splits=splits)
        book_transactions.validate()

        # Transaction recording capital loss.
        splits = [
            Split(broker, -value, quantity=mzero),
            Split(inc, value),
        ]
        Transaction(inc.commodity, description="Capital loss", splits=splits)
        book_transactions.validate()

    def test_tag_split_zero_value(self, book_transactions):
        broker = book_transactions.accounts(name="broker")
        asset = book_transactions.accounts.get(name="asset")
        currency = book_transactions.default_currency

        # Give away 250 shares for free.
        quantity = Decimal(-250)
        splits = [
            Split(asset, 0),
            Split(broker, 0, quantity=quantity),
        ]

        Transaction(currency, description="donation", splits=splits)

        book_transactions.validate()


class TestTransaction_lots(object):
    def test_create_simpletlot_addsplits(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")
        l = Lot(title="test mé", account=s, notes="ïlya")
        for i, am in enumerate([45, -35, -20]):
            tr = Transaction(
                currency=EUR,
                description="trade stock",
                notes="àçö",
                post_date=date(2014, 1, 1 + i),
                enter_date=datetime(2014, 1, 1 + i),
                splits=[
                    Split(account=a, value=am * 10, memo="mémo asset"),
                    Split(
                        account=s, value=-am * 10, quantity=-am, memo="mémo brok", lot=l
                    ),
                ],
            )
        book_basic.flush()

    def test_create_simpletlot_initialsplits(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")
        sp = []
        for i, am in enumerate([45, -35, -20]):
            tr = Transaction(
                currency=EUR,
                description="trade stock",
                notes="àçö",
                post_date=date(2014, 1, 1 + i),
                enter_date=datetime(2014, 1, 1 + i),
                splits=[
                    Split(account=a, value=am * 10, memo="mémo asset"),
                    Split(account=s, value=-am * 10, quantity=-am, memo="mémo brok"),
                ],
            )
            sp.append(tr.splits(account=s))

        l = Lot(title="test mé", account=s, notes="ïlya", splits=sp)
        book_basic.flush()

    def test_create_closedlot_addsplits(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")
        l = Lot(title="test mé", account=s, notes="ïlya")
        l.is_closed = 1
        # raise valueerror as lot is closed
        with pytest.raises(ValueError):
            tr = Transaction(
                currency=EUR,
                description="trade stock",
                notes="àçö",
                post_date=date(2014, 1, 1),
                enter_date=datetime(2014, 1, 1),
                splits=[
                    Split(account=a, value=10, memo="mémo asset"),
                    Split(account=s, value=-10, quantity=-2, memo="mémo brok", lot=l),
                ],
            )

    def test_create_simplelot_inconsistentaccounts(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        racc = book_basic.root_account
        a = book_basic.accounts(name="asset")
        s = book_basic.accounts(name="broker")
        l = Lot(title="test mé", account=a, notes="ïlya")
        # raise valueerror as split account not the same as lot account
        tr = Transaction(
            currency=EUR,
            description="trade stock",
            notes="àçö",
            post_date=date(2014, 1, 1),
            enter_date=datetime(2014, 1, 1),
            splits=[
                Split(account=a, value=10, memo="mémo asset"),
                Split(account=s, value=-10, quantity=-2, memo="mémo brok", lot=l),
            ],
        )
        book_basic.add(tr)

        with pytest.raises(ValueError):
            book_basic.validate()


class TestTransaction_changes(object):
    def test_delete__replace_existing_split(self, book_transactions):
        s = len(book_transactions.splits)
        transaction = book_transactions.transactions(description="my revenue")
        split = transaction.splits(value=1000)
        assert len(transaction.splits) == 2
        splits = [
            Split(
                account=split.account,
                value=split.value,
                quantity=split.quantity,
            )
            for split in list(transaction.splits)
        ]

        assert len(transaction.splits) == 2
        transaction.splits[:] = splits
        assert split.transaction is None
        assert len(transaction.splits) == 2
        book_transactions.flush()
        book_transactions.save()
        ns = len(book_transactions.splits)
        assert ns == s

    def test_delete__replace_existing_split__split_with_transaction(
        self, book_transactions
    ):
        s = len(book_transactions.splits)
        transaction = book_transactions.transactions(description="my revenue")
        split = transaction.splits(value=1000)
        split_guid = split.guid
        assert len(transaction.splits) == 2
        splits = list(transaction.splits)
        del transaction.splits[:]

        splits = [
            Split(
                account=split.account,
                value=split.value * 2,
                quantity=split.quantity * 2,
                transaction=transaction,
            )
            for split in splits
        ]

        assert len(transaction.splits) == 2
        transaction.splits[:] = splits
        assert split.transaction is None
        assert len(transaction.splits) == 2
        book_transactions.flush()
        book_transactions.save()
        # check that previous split has been deleted
        with pytest.raises(KeyError, match="Could not find object with {'guid'"):
            split = book_transactions.splits(guid=split_guid)
        ns = len(book_transactions.splits)
        assert ns == s

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
        p_expected = (sp.value / sp.quantity).quantize(Decimal("0.000001"))
        assert p.value == p_expected

        # changing the quantity of the split should NOT change the existing price
        sp.quantity = (5, 1)

        book_transactions.validate()

        p_not_expected = (sp.value / sp.quantity).quantize(Decimal("0.000001"))

        assert len(book_transactions.prices) == 6
        assert p.value == p_expected
        assert p_expected != p_not_expected

        # changing the post date of the transaction of the split should create a new price
        tr.post_date = date(2015, 1, 29)
        book_transactions.validate()
        book_transactions.flush()
        assert len(book_transactions.prices) == 7


class TestSplit_credit_debit(object):
    def test_delete_existing_transaction(self, book_transactions):
        asset = book_transactions.accounts.get(name="asset")
        inc = book_transactions.accounts.get(name="inc")
        exp = book_transactions.accounts.get(name="exp")

        # revenue item
        revenue = book_transactions.transactions(description="my revenue")
        revenue_split_asset = revenue.splits(account=asset)
        revenue_split_inc = revenue.splits(account=inc)
        assert revenue_split_asset.is_credit is False
        assert revenue_split_asset.is_debit is True
        assert revenue_split_inc.is_credit is True
        assert revenue_split_inc.is_debit is False

        # expense item
        expense = book_transactions.transactions(description="my expense")
        expense_split_asset = expense.splits(account=asset)
        expense_split_inc = expense.splits(account=exp)
        assert expense_split_asset.is_credit is True
        assert expense_split_asset.is_debit is False
        assert expense_split_inc.is_credit is False
        assert expense_split_inc.is_debit is True
