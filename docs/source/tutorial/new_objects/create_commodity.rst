Creating a new Commodity
------------------------

piecash can create new commodities (a :class:`piecash.core.commodity.Commodity`):

.. ipython:: python

    from piecash import create_book, Commodity, factories

    # create a book (in memory) with some currency
    book = create_book(currency="EUR")

    print(book.commodities)

    # creating a new ISO currency (if not already available in s.commodities)
    USD = factories.create_currency_from_ISO("USD")
    book.add(USD) # add to session

    # create a commodity (lookup on yahoo! finance, need web access)
    apple = factories.create_stock_from_symbol("AAPL")
    book.add(apple) # add to session

    # creating commodities using the constructor (warning, object should be manually added to session)

    # create a special "reward miles" Commodity using the constructor
    miles = Commodity(namespace="LOYALTY", mnemonic="Miles", fullname="Reward miles", fraction=1000000)
    book.add(miles) # add to session

    USD, apple, miles

.. warning::

    The following (creation of non ISO currencies) is explicitly forbidden by the GnuCash application.

.. ipython:: python

    # create a bitcoin currency (warning, max 6 digits after comma, current GnuCash limitation)
    XBT = Commodity(namespace="CURRENCY", mnemonic="XBT", fullname="Bitcoin", fraction=1000000)
    book.add(XBT) # add to session

    XBT




