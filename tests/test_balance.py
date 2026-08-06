from datetime import date

from decimal import Decimal

import pytest
from piecash import ledger
from piecash._common import GncConversionError
from test_helper import (
    db_sqlite_uri,
    db_sqlite,
    new_book,
    new_book_USD,
    book_uri,
    book_transactions,
    book_complex,
    book_historical_prices
)

# dummy line to avoid removing unused symbols
a = (
    db_sqlite_uri,
    db_sqlite,
    new_book,
    new_book_USD,
    book_uri,
    book_transactions,
    book_complex,
    book_historical_prices
)


def test_get_balance(book_complex):
    """
    Tests listing the commodity quantity in the account.
    """

    asset = book_complex.accounts.get(name="Asset")
    broker = book_complex.accounts.get(name="Broker")
    foo_stock = book_complex.accounts.get(name="Foo stock")
    expense = book_complex.accounts.get(name="Expense")
    income = book_complex.accounts.get(name="Income")
    assert foo_stock.get_balance(recurse=True) == Decimal("130")
    assert broker.get_balance(recurse=True) == Decimal("117")
    assert asset.get_balance(recurse=False) == Decimal("0")
    assert asset.get_balance() == Decimal("24695.3")
    assert expense.get_balance() == Decimal("260")
    assert income.get_balance() == Decimal("150")
    assert income.get_balance(natural_sign=False) == Decimal("-150")

def test_get_historical_balance(book_historical_prices):
    """
    Tests expressing the account balance (as of a date in the past) in a different currency, using historical price data.
    """

    assets = book_historical_prices.accounts.get(name="Assets")
    current = assets.children(name="Current Assets")
    eur_cash = current.children(name="EUR Cash Account")
    gbp_cash = current.children(name="GBP Cash Account")
    stocks = assets.children(name="Stocks")
    ts1 = stocks.children(name="Test Stock Account 1")
    ts2 = stocks.children(name="Test Stock Account 2")
    test_assets = book_historical_prices.accounts.get(name="Test Asset Account")
    egp_cash = test_assets.children(name="Test Cash Account")
    eur = book_historical_prices.commodities(mnemonic='EUR')
    gbp = book_historical_prices.commodities(mnemonic='GBP')
    usd = book_historical_prices.commodities(mnemonic='USD')

    # Forward rate on exact date
    assert gbp_cash.get_balance(commodity=eur, at_date=date(2020, 6, 10), use_historical=True) == Decimal("16000")
    # Forward rate before at_date
    assert gbp_cash.get_balance(commodity=eur, at_date=date(2020, 1, 14), use_historical=True) == Decimal("11000")
    # Forward rate after at_date
    assert gbp_cash.get_balance(commodity=eur, at_date=date(2020, 3, 4), use_historical=True) == Decimal("13000")

    # Reverse rate on exact date
    assert gbp_cash.get_balance(commodity=eur, at_date=date(2020, 7, 12), use_historical=True) == Decimal("20000")
    # Reverse rate before at_date
    assert gbp_cash.get_balance(commodity=eur, at_date=date(2020, 2, 20), use_historical=True) == Decimal("12500")
    # Reverse rate after at_date
    assert gbp_cash.get_balance(commodity=eur, at_date=date(2020, 6, 30), use_historical=True) == Decimal("20000")

    # Indirect rate
    assert round(gbp_cash.get_balance(commodity=usd, at_date=date(2020, 8, 1), use_historical=True), 2) == Decimal("16949.15")

    # Recursive (cash accounts)
    assert current.get_balance(commodity=eur, at_date=date(2020, 4, 20), use_historical=True, recurse=True) == Decimal('23000')

    # Not recursive (cash accounts)
    assert current.get_balance(commodity=eur, at_date=date(2020, 4, 20), use_historical=True, recurse=False) == Decimal('0')

    assert ts1.get_balance(commodity=eur, at_date=date(2020, 5, 20), use_historical=True) == Decimal('40.5')
    assert ts2.get_balance(commodity=eur, at_date=date(2020, 5, 20), use_historical=True) == Decimal('128.25')
    assert stocks.get_balance(commodity=eur, at_date=date(2020, 5, 20), use_historical=True) == Decimal('168.75')

    # Recursive (all assets)
    assert assets.get_balance(commodity=eur, at_date=date(2020, 5, 20), use_historical=True, recurse=True) == Decimal('26168.75')

    # Latest
    assert assets.get_balance(commodity=eur, at_date=date.today(), use_historical=True, recurse=True) \
           == assets.get_balance(commodity=eur, use_historical=False, recurse=True)

    # Can't find
    with pytest.raises(GncConversionError):
        egp_cash.get_balance(commodity=eur, at_date=date(2020, 1, 2), use_historical=True)


