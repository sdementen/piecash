"""
Read currency exchange rates.
This functionality could be used to display the exchange rate graph, for example.
"""
import piecash
from piecash import Account, Commodity, Budget, Vendor

# Variables
filename = "test.gnucash"
symbol = "AUD"
#

book = piecash.open_book(filename, open_if_lock=True)
# , readonly=False, 

# get the SQLAlchemy session
session = book.session
#accountsFiltered = session.query(Account).filter(Account.name >= "T").all()

# all commodities
#commodities = book.commodities

# find the currencies to update

# SQLAlchemy methods: count, first, all
#commoditiesFiltered = session.query(Commodity).filter(Commodity.mnemonic == "EUR").all()

cdty = session.query(Commodity).filter(Commodity.mnemonic == symbol).first()
print(cdty)

# Accessing individual records.

# accessing attributes of a commodity
print("Commodity namespace={cdty.namespace}\n"
      "          mnemonic={cdty.mnemonic}\n"
      "          cusip={cdty.cusip}\n"
      "          fraction={cdty.fraction}".format(cdty=cdty))

# loop on the prices.
# This can be used to display a price graph, for example.
print("Historical prices:")
for pr in cdty.prices:
    print("Price date={pr.date}"
          "      value={pr.value} {pr.currency.mnemonic}/{pr.commodity.mnemonic}".format(pr=pr))      