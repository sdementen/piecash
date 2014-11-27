#!/usr/bin/env python
# # @file
# @brief Creates a basic set of accounts and a couple of transactions
# @ingroup python_bindings_examples

from piecash import create_book, Account, Transaction, Split, Commodity

FILE_1 = "/tmp/example.gnucash"

with create_book(FILE_1, overwrite=True) as session:
    book = session.book
    root_acct = book.root_account
    cad = Commodity.create_from_ISO("CAD")
    expenses_acct = Account(parent=root_acct,
                            name="Expenses",
                            account_type="EXPENSE",
                            commodity=cad)
    savings_acct = Account(parent=root_acct,
                           name="Savings",
                           account_type="BANK",
                           commodity=cad)
    opening_acct = Account(parent=root_acct,
                           name="Opening Balance",
                           account_type="EQUITY",
                           commodity=cad)
    num1 = (4, 1)
    num2 = (100, 1)
    negnum1 = (-4, 1)
    negnum2 = (-100, 1)
    num3 = (15, 1)

    # create transaction with core objects in one step
    trans1 = Transaction(currency=cad,
                         description="Groceries",
                         splits=[
                             Split(value=num1, account=expenses_acct),
                             Split(value=negnum1, account=savings_acct),
                         ])

    # create transaction with core object in multiple steps
    trans2 = Transaction(currency=cad,
                         description="Opening Savings Balance")

    split3 = Split(value=num2,
                   account=savings_acct,
                   transaction=trans2)

    split4 = Split(value=negnum2,
                   account=opening_acct,
                   transaction=trans2)

    # create transaction with factory function
    trans3 = Transaction.single_transaction(None,None,"Pharmacy", num3, savings_acct, expenses_acct)

    session.save()


