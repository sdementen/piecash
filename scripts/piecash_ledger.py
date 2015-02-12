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

if sys.version_info.major==2:
    out = codecs.getwriter('UTF-8')(sys.stdout)
else:
    out = sys.stdout

parser = argparse.ArgumentParser(description="Generate a ledger-cli representation of a gnucash book")
parser.add_argument("gnucash_filename",
                    help="the name of the gnucash file to process")
args = parser.parse_args()

def format_commodity(commodity):
    mnemonic = commodity.mnemonic
    try:
        if mnemonic.encode('ascii').isalpha():
            return mnemonic
    except:
        pass
    return "\"{}\"" .format(mnemonic)  # TODO: escape " char in mnemonic

with piecash.open_book(args.gnucash_filename, open_if_lock=True) as data:
    
    for commodity in data.commodities:
        if commodity.mnemonic == "":
            continue
        out.write("commodity {}\n" .format(format_commodity(commodity)))
        if commodity.fullname != "":
            out.write("\tnote {}\n" .format(commodity.fullname))
    out.write("\n")
    
    for acc in data.accounts:
        # ignore "dummy" accounts
        if acc.type is None or acc.type == "ROOT":
            continue
        if str(acc.commodity) == "template":
            continue
        out.write("account {}\n" .format(acc.fullname, ))
        if acc.description != "":
            out.write("\tnote {}\n" .format(acc.description,))
        out.write("\tcheck commodity == \"{}\"\n" .format(acc.commodity.mnemonic))
        out.write("\n")
    
    # Prices
    for price in sorted(data.prices, key=lambda x:x.date):
        out.write(
            "P {:%Y/%m/%d %H:%M:%S} {} {} {}\n" .format(price.date, format_commodity(price.commodity), price.value, format_commodity(price.currency)))
    out.write("\n")
    
    for trans in sorted(data.transactions,key=lambda x: x.post_date):
        out.write(trans.ledger_str())
        out.write("\n")
