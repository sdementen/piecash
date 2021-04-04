#!/usr/bin/env python
##  @file
#   @brief Example Script simple sqlite create
#   @ingroup python_bindings_examples

from __future__ import print_function
import os

from piecash import create_book, Account, Commodity, open_book
from piecash.core.factories import create_currency_from_ISO

filename = os.path.abspath("test.blob")
if os.path.exists(filename):
    os.remove(filename)

with create_book(filename) as book:
    a = Account(
        parent=book.root_account,
        name="wow",
        type="ASSET",
        commodity=create_currency_from_ISO("CAD"),
    )

    book.save()

with open_book(filename) as book:
    print(book.root_account.children)
    print(book.commodities.get(mnemonic="CAD"))

os.remove(filename)
