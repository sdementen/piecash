#!/usr/bin/env python
# # @file
# @brief Creates a basic set of accounts and a couple of transactions
# @ingroup python_bindings_examples
from decimal import Decimal

from piecash import create_book, Account, Transaction, Split, Commodity
from piecash.core.factories import create_currency_from_ISO

FILE_1 = "/tmp/example.gnucash"

with create_book(FILE_1, overwrite=True) as book:
    root_acct = book.root_account
    cad = create_currency_from_ISO("CAD")
    expenses_acct = Account(parent=root_acct,
                            name="Expenses",
                            type="EXPENSE",
                            commodity=cad)
    savings_acct = Account(parent=root_acct,
                           name="Savings",
                           type="BANK",
                           commodity=cad)
    opening_acct = Account(parent=root_acct,
                           name="Opening Balance",
                           type="EQUITY",
                           commodity=cad)
    num1 = Decimal("4")
    num2 = Decimal("100")
    num3 = Decimal("15")

    # create transaction with core objects in one step
    trans1 = Transaction(currency=cad,
                         description="Groceries",
                         splits=[
                             Split(value=num1, account=expenses_acct),
                             Split(value=-num1, account=savings_acct),
                         ])

    # create transaction with core object in multiple steps
    trans2 = Transaction(currency=cad,
                         description="Opening Savings Balance")

    split3 = Split(value=num2,
                   account=savings_acct,
                   transaction=trans2)

    split4 = Split(value=-num2,
                   account=opening_acct,
                   transaction=trans2)

    # create transaction with factory function
    trans3 = Transaction.single_transaction(None,None,"Pharmacy", num3, savings_acct, expenses_acct)

    book.save()


