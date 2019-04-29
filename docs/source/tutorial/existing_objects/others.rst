Other objects
-------------

In fact, any object can be retrieved from the session through a generic ``get(**kwargs)`` method:

.. ipython:: python

    book = open_book(gnucash_books + "invoices.gnucash", open_if_lock=True)

    from piecash import Account, Commodity, Budget, Vendor

    # accessing specific objects through the get method
    book.get(Account, name="Assets", parent=book.root_account)
    book.get(Commodity, namespace="CURRENCY", mnemonic="EUR")
    book.get(Budget, name="my first budget")
    book.get(Vendor, name="Looney")

If you know SQLAlchemy, you can get access to the underlying :class:`~sqlalchemy.orm.session.Session` as ``book.session`` and execute
queries using the piecash classes:

.. ipython:: python

    from piecash import Account, Commodity, Budget, Vendor

    # get the SQLAlchemy session
    session = book.session

    # loop through all invoices
    for invoice in session.query(Invoice).all():
        print(invoice.notes)

.. note::

    Easy access to objects from :mod:`piecash.business` and :mod:`piecash.budget` could be given directly from the session
    in future versions if deemed useful.
