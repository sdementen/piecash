#!/usr/bin/env python
##  @file
#   @brief Example Script simple sqlite create
#   @ingroup python_bindings_examples

from __future__ import print_function
import os

from piecash import create_book, Account, Commodity, open_book

filename = os.path.abspath('test.blob')

with create_book(filename) as s:
    a = Account(parent=s.book.root_account,
                name="wow",
                account_type="ASSET",
                commodity=Commodity.create_currency_from_ISO("CAD"))

    s.save()

with open_book(filename) as s:
    print(s.book.root_account.children)
    print(s.commodities.get(mnemonic="CAD"))

os.remove(filename)
