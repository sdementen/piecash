#!/usr/local/bin/python
"""original script from https://github.com/MatzeB/pygnucash/blob/master/gnucash2ledger.py by Matthias Braun matze@braunis.de
 adapted for:
 - python 3 support
 - new string formatting

The security must exist in GnuCash database.
Example of a valid CSV file:
    currency,commodity,value,date
    AUD,YMAX,9.06,"2017-11-10"
 
"""
import argparse
import csv
import sys
from datetime import datetime
from decimal import Decimal

import piecash
from piecash import Price

parser = argparse.ArgumentParser(description="""
Import and export prices to and from a gnucash book.

Per default, it exports the full prices list from the gnucash book to the standard output in a CSV format.
To import, add the argument "--import file_to_import.csv".

The format used is a standard CSV (comma as separator) with the following columns:
 - date (YYYY-MM-DD)
 - commodity (gnucash mnemonic)
 - currency (gnucash mnemonic)
 - type (string, optional)
 - value (float)
 - type (string, optional)
""", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("gnucash_filename",
                    help="the name of the gnucash file")
parser.add_argument("--import", dest="operation",
                    help="to import the prices from a csv file (default export)")
args = parser.parse_args()

# args.operation is the name of the import file (.csv).

if args.operation is None:
    # export the prices
    sys.stdout.write("date,type,value,value_num, value_denom, currency,commodity,source\n")
    with piecash.open_book(args.gnucash_filename, open_if_lock=True) as book:
        sys.stdout.writelines(
            "{p.date:%Y-%m-%d},{p.type},{p.value},{p._value_num},{p._value_denom},{p.currency.mnemonic},{p.commodity.mnemonic},{p.source}\n".format(
                p=p) for p in book.prices)
else:
    # import the prices
    with piecash.open_book(args.gnucash_filename, open_if_lock=True, readonly=False) as book:
        cdty = book.commodities
        importFile = open(args.operation, 'r')

        for l in csv.DictReader(importFile):
            cur = cdty(mnemonic=l['currency'])
            com = cdty(mnemonic=l['commodity'])
            type = l.get('type', None)
            date = datetime.strptime(l['date'], "%Y-%m-%d")
            v = Decimal(l['value'])
            Price(currency=cur,
                  commodity=com,
                  date=date,
                  value=v,
                  source="piecash-importer")
        book.save()
