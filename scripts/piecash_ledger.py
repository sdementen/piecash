#!/usr/local/bin/python
"""original script from https://github.com/MatzeB/pygnucash/blob/master/gnucash2ledger.py by Matthias Braun matze@braunis.de
 adapted for:
 - python 3 support
 - new string formatting
"""
import argparse
import sys
import codecs

import piecash

if sys.version_info.major == 2:
    out = codecs.getwriter('UTF-8')(sys.stdout)
else:
    out = sys.stdout

parser = argparse.ArgumentParser(description="Generate a ledger-cli representation of a gnucash book")
parser.add_argument("gnucash_filename",
                    help="the name of the gnucash file to process")
args = parser.parse_args()

with piecash.open_book(args.gnucash_filename, open_if_lock=True) as data:
    out.write(piecash.ledger(data))
