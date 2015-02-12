Commodities and Prices
----------------------

The list of all commodities in the book can be retrieved via the ``commodities`` attribute::

    # all commodities
    print(book.commodities)

    cdty = book.commodities[0]

    # accessing attributes of a commodity
    print("Commodity namespace={cdty.namespace}\n"
          "          mnemonic={cdty.mnemonic}\n"
          "          cusip={cdty.cusip}\n"
          "          fraction={cdty.fraction}".format(cdty=cdty))

The prices (:class:`piecash.core.commodity.Price`) of a commodity can be iterated through the ``prices`` attribute::

    # loop on the prices
    for pr in cdty.prices:
        print("Price date={pr.date}"
              "      value={pr.value} {pr.currency.mnemonic}/{pr.commodity.mnemonic}".format(pr=pr))
