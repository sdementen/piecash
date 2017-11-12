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

# Variables
filename = sys.argv[1]
if filename is None:
    print("You need to specify a valid .gnucash file to use.")
    filename = "test.gnucash"

symbol = "AUD"
####################################

with piecash.open_book(filename, open_if_lock=True) as book:
    # , readonly=False,

    # Get all commodities.
    # The commodities (including currencies) in the book are only those used in accounts.
    #commodities = book.commodities

    # Get all the currencies in the book (i.e. for update).
    print("All currencies used in the book:")
    currencies = book.currencies
    for c in currencies:
        print(c)

    # Accessing individual records.

    print("\nSelected single currency details (" + symbol + "):")
    cdty = book.get(Commodity, namespace="CURRENCY", mnemonic=symbol)

    # Accessing attributes of a commodity.
    print("Commodity namespace={cdty.namespace}\n"
        "          mnemonic={cdty.mnemonic}\n"
        "          cusip={cdty.cusip}\n"
        "          fraction={cdty.fraction}".format(cdty=cdty))

    # Loop through the existing commodity prices.
    # This can be used to fetch the points for a price graph.
    print("\nHistorical prices:")
    for pr in cdty.prices:
        print("Price date={pr.date}"
            "      value={pr.value} {pr.currency.mnemonic}/{pr.commodity.mnemonic}".format(pr=pr))

    # List of accounts which use the commodity:
    #cdty.accounts
