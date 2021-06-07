from piecash import open_book, create_book, GnucashException, Account


def open_gnucash_book(GNUCASH_BOOK):
    # open or create gnucash book if not found
    import os
    import tempfile

    if os.path.exists(GNUCASH_BOOK):
        print("Found: ", GNUCASH_BOOK)
        # open book file
        book = open_book(
            GNUCASH_BOOK, readonly=False, open_if_lock=True, do_backup=False
        )
    else:
        # create book file
        book = create_book(GNUCASH_BOOK, overwrite=True, currency="EUR")
        print("Created: ", GNUCASH_BOOK)
    return book


def get_or_create_account(book, fullname, type):
    # get_or_create_accounts
    acc_tree = ""
    for name in fullname.split(":"):
        if acc_tree:
            acc_tree += ":" + name
        else:
            acc_tree = name
            acc = book.root_account
        try:
            acc = book.accounts(fullname=acc_tree)
            # print("> Found: ", acc_tree)
        except KeyError:
            # print("> Create: ",  name)
            acc = Account(
                name=name,
                type=type,
                parent=acc,
                commodity=EUR,
                placeholder=False,
            )
            book.flush()
    return acc


def basic_coa():
    # get_or_create_accounts
    get_or_create_account(book, fullname="Asset", type="ASSET")
    get_or_create_account(book, fullname="Asset:Cheque", type="BANK")
    get_or_create_account(book, fullname="Asset:Saving", type="BANK")
    get_or_create_account(book, fullname="Expense", type="EXPENSE")
    get_or_create_account(book, fullname="Income", type="INCOME")


def print_coa():
    # basic account listing
    print()
    for account in book.accounts:
        print(account)


GNUCASH_BOOK = "../gnucash_books/simple_csv_book_creation.gnucash"
book = open_gnucash_book(GNUCASH_BOOK)

# retrieve the default currency
EUR = book.commodities.get(mnemonic="EUR")

basic_coa()
# print_coa()

import csv
from piecash import open_book, Transaction, Split
from datetime import datetime, date
from decimal import Decimal

CSV_IMPORT = "import.csv"
today = datetime.now()
import_account = get_or_create_account(book, fullname="Asset:Cheque", type="BANK")

# import file
with open(CSV_IMPORT, "r") as file:
    # initialise the CSV reader
    csv_file = csv.DictReader(file)

    # iterate on all the transactions in the file
    for row in csv_file:

        # reformat data as required
        transfer_account = get_or_create_account(
            book, fullname=row["Account"], type=row["Account"].split(":")[0].upper()
        )
        amount = Decimal(row["Amount"])

        # create the transaction with its two splits
        Transaction(
            post_date=date(
                int(row["Date"][6:8]) + 2000,
                int(row["Date"][3:5]),
                int(row["Date"][0:2]),
            ),
            enter_date=today,
            currency=EUR,
            description=row["Entity"],
            splits=[
                Split(account=import_account, value=amount, memo=row["Memo"]),
                Split(account=transfer_account, value=-amount, memo=row["Memo"]),
            ],
        )
    # save the book
    book.save()
