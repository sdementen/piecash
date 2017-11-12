"""
Read currency exchange rates.
This functionality could be used to display the exchange rate graph, for example.

The first (and only) parameter is the name of the GnuCash file to use. If not set, 
'test.gnucash' is used.
"""
# pylint: disable=invalid-name
import sys
import piecash
from piecash import Commodity
# Account, Budget, Vendor

# Variables
filename = sys.argv[1]
print(filename)
if filename is None:
    filename = "test.gnucash"
symbol = "AUD"
####################################

book = piecash.open_book(filename, open_if_lock=True)
# , readonly=False,

# The data can also be read directly through the SQLAlchemy session, if desired.
session = book.session
#accountsFiltered = session.query(Account).filter(Account.name >= "T").all()
# SQLAlchemy methods: count, first, all
#commoditiesFiltered = session.query(Commodity).filter(Commodity.mnemonic == "EUR").all()
# Getting a single commodity.
#cdty = session.query(Commodity).filter(Commodity.mnemonic == symbol).first()

# Get all commodities.
# The commodities (including currencies) in the book are only those used in accounts.
#commodities = book.commodities
#print(commodities)

# Get all the currencies in the book (to update, for example).

print("All currencies used in the book:")
#currencies = book.get(Commodity, namespace="CURRENCY")
currencies = session.query(Commodity).filter(Commodity.namespace == "CURRENCY").all()
for c in currencies:
    print(c)

# Accessing individual records.

print("\nSelected single currency details (" + symbol + "):")
cdty = book.get(Commodity, namespace="CURRENCY", mnemonic=symbol)

# accessing attributes of a commodity
print("Commodity namespace={cdty.namespace}\n"
      "          mnemonic={cdty.mnemonic}\n"
      "          cusip={cdty.cusip}\n"
      "          fraction={cdty.fraction}".format(cdty=cdty))

# loop on the prices.
# This can be used to display a price graph, for example.
print("\nHistorical prices:")
for pr in cdty.prices:
    print("Price date={pr.date}"
          "      value={pr.value} {pr.currency.mnemonic}/{pr.commodity.mnemonic}".format(pr=pr))
