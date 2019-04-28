Commodities and Prices
----------------------

The list of all commodities in the book can be retrieved via the ``commodities`` attribute:

.. ipython:: python

    book = open_book(gnucash_books + "book_prices.gnucash", open_if_lock=True)

    # all commodities
    print(book.commodities)

    cdty = book.commodities[0]

    # accessing attributes of a commodity
    print("Commodity namespace={cdty.namespace}\n"
          "          mnemonic={cdty.mnemonic}\n"
          "          cusip={cdty.cusip}\n"
          "          fraction={cdty.fraction}".format(cdty=cdty))

The prices (:class:`piecash.core.commodity.Price`) of a commodity can be iterated through the ``prices`` attribute:

.. ipython:: python

    # loop on the prices
    for cdty in book.commodities:
        for pr in cdty.prices:
            print("Price date={pr.date}"
                  "      value={pr.value} {pr.currency.mnemonic}/{pr.commodity.mnemonic}".format(pr=pr))
