import csv
from pathlib import Path

from piecash import open_book, Account

GNUCASH_BOOK = "../gnucash_books/simple_sample.gnucash"

# open the book and the export file
with open_book(GNUCASH_BOOK, readonly=True, open_if_lock=True) as book:
    # show accounts
    print(book.accounts)
    print("Number of splits in the book:", len(book.splits))
    # select the 3rd account
    account = book.accounts[2]
    print(account, " has splits: ", account.splits)

    # delete the account from the book
    book.delete(account)
    # flush the change
    book.flush()
    # check the account has disappeared from the book and its related split too
    print(book.accounts)
    print("Number of splits in the book:", len(book.splits))

    # even if the account object and its related object still exists
    print(account, " has splits: ", account.splits)

    # do not forget to save the book if you want
    # your changes to be saved in the database
