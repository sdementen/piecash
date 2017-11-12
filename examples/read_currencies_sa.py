"""
Read currency exchange rates.
This example is similar to read_currencies script but uses SQLAlchemy directly
to achieve the same result.

The goal is simply to illustrate what happens under the hood. Hopefully this 
shows how simple the piecash API is.
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

    # SQLAlchemy session.
    session = book.session

    # query example:
    #accountsFiltered = session.query(Account).filter(Account.name >= "T").all()
    # SQLAlchemy methods: count, first, all, one...

    # Get all the currencies in the book (i.e. for update).
    print("All currencies used in the book:")
    currencies = session.query(Commodity).filter(Commodity.namespace == "CURRENCY").all()
    for c in currencies:
        print(c)

    # Accessing individual records.

    print("\nSelected single currency details (" + symbol + "):")
    cdty = session.query(Commodity).filter(Commodity.namespace == "CURRENCY", Commodity.mnemonic == symbol).first()

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
