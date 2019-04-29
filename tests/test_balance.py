from decimal import Decimal

from piecash import ledger
from test_helper import (db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri,
                         book_transactions, book_complex)

# dummy line to avoid removing unused symbols
a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_transactions, book_complex


def test_get_balance(book_complex):
    """
    Tests listing the commodity quantity in the account.
    """

    asset = book_complex.accounts.get(name="Asset")
    broker = book_complex.accounts.get(name="Broker")
    foo_stock = book_complex.accounts.get(name="Foo stock")
    expense =  book_complex.accounts.get(name="Expense")
    income = book_complex.accounts.get(name="Income")
    assert foo_stock.get_balance(recurse=True) == Decimal('130')
    assert broker.get_balance(recurse=True) == Decimal('117')
    assert asset.get_balance(recurse=False) == Decimal('0')
    assert asset.get_balance() == Decimal('24695.3')
    assert expense.get_balance() == Decimal('260')
    assert income.get_balance() == Decimal('150')
    assert income.get_balance(natural_sign=False) == Decimal('-150')
