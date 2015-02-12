Other objects
-------------

In fact, any object can be retrieved from the session through a generic ``get(**kwargs)`` method::

    from piecash import Account, Commodity, Budget, Vendor

    # accessing specific objects through the get method
    acc = book.get(Account, name="Asset", parent=book.root_account)
    cdty = book.get(Commodity, namespace="CURRENCY", mnemonic="EUR")
    bdgt = book.get(Budget, name="my first budget")
    invoice = book.get(Vendor, name="Looney")

If you know SQLAlchemy, you can get access to the underlying :class:`~sqlalchemy.orm.session.Session` as ``book.session`` and execute
queries using the piecash classes::

    from piecash import Account, Commodity, Budget, Vendor

    # get the SQLAlchemy session
    session = book.session

    # loop through all invoices
    for invoice in session.query(Invoice).all():
        print(invoice.notes)

.. note::

    Easy access to objects from :mod:`piecash.business` and :mod:`piecash.budget` could be given directly from the session
    in future versions if deemed useful.
