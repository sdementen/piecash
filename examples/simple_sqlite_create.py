#!/usr/bin/env python
##  @file
#   @brief Example Script simple sqlite create
#   @ingroup python_bindings_examples

import os
from piecash import create_book, Account, Commodity, open_book

filename = os.path.abspath('test.blob')

with create_book(filename) as s:
    a = Account(parent=s.book.root_account,
                name="wow",
                account_type="ASSET",
                commodity=Commodity.create_from_ISO("CAD"))

    s.save()

with open_book(filename) as s:
    print s.book.root_account.children
    print s.commodities.get(mnemonic="CAD")

os.remove(filename)