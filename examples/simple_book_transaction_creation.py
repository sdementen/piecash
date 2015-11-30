from piecash import create_book, Account

# create a book with some account tree structure
with create_book("../gnucash_books/simple_book_transaction_creation.gnucash", overwrite=True) as mybook:
    mybook.root_account.children = [
        Account(name="Expenses",
                type="EXPENSE",
                commodity=mybook.currencies(mnemonic="USD"),
                placeholder=True,
                children=[
                    Account(name="Some Expense Account",
                            type="EXPENSE",
                            commodity=mybook.currencies(mnemonic="USD")),
                ]),
        Account(name="Assets",
                type="ASSET",
                commodity=mybook.currencies(mnemonic="USD"),
                placeholder=True,
                children=[
                    Account(name="Current Assets",
                            type="BANK",
                            commodity=mybook.currencies(mnemonic="USD"),
                            placeholder=True,
                            children=[
                                Account(name="Checking",
                                        type="BANK",
                                        commodity=mybook.currencies(mnemonic="USD"))
                            ]),
                ]),
    ]
    # save the book
    mybook.save()

from piecash import open_book, Transaction, Split
from datetime import datetime
from decimal import Decimal

# reopen the book and add a transaction
with open_book("../gnucash_books/simple_book_transaction_creation.gnucash",
               open_if_lock=True,
               readonly=False) as mybook:
    today = datetime.now()
    # retrieve the currency from the book
    USD = mybook.currencies(mnemonic="USD")
    # define the amount as Decimal
    amount = Decimal("25.35")
    # retrieve accounts
    to_account = mybook.accounts(fullname="Expenses:Some Expense Account")
    from_account = mybook.accounts(fullname="Assets:Current Assets:Checking")
    # create the transaction with its two splits
    Transaction(
        post_date=today,
        enter_date=today,
        currency=USD,
        description="Transaction Description!",
        splits=[
            Split(account=to_account,
                  value=amount,
                  memo="Split Memo!"),
            Split(account=from_account,
                  value=-amount,
                  memo="Other Split Memo!"),
        ]
    )
    # save the book
    mybook.save()

from piecash import ledger

# check the book by exporting to ledger format
with open_book("../gnucash_books/simple_book_transaction_creation.gnucash",
               open_if_lock=True) as mybook:
    print(ledger(mybook))