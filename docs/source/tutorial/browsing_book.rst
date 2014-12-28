Accessing the core objects
==========================

Once a GnuCash book is opened, it is straightforward to access the different GnuCash objects through the :class:`piecash.core.session.GncSession`.

Book and Accounts
-----------------

Accessing the book (:class:`piecash.core.book.Book`) and the accounts (:class:`piecash.core.account.Account`)::

    from piecash import open_book

    with open_book("gnucash_books/simple_sample.gnucash") as s:
        # accessing the book object
        book = s.book

        # accessing the root_account
        root = s.book.root_account
        print(root)

        # accessing the first children account of a book
        acc = root.children[0]
        print(acc)

        # accessing attributes of an account
        print("Account name={acc.name}\n"
              "        commodity={acc.commodity.namespace}/{acc.commodity.mnemonic}\n"
              "        fullname={acc.fullname}\n"
              "        type={acc.type}".format(acc=acc))

        # accessing all splits related to an account
        for sp in acc.splits:
            print("account <{}> is involved in transaction '{}'".format(acc.fullname, sp.transaction.description))


You can get the first element of any list like attribute that match some attributes via the ``get(**kwargs)`` method::

    # getting a the first children account with given attribute(s)
    acc = root.children.get(name="Asset")
    assert acc.name == "Asset"

    acc = root.children.get(type="ASSET")
    assert acc.type == "ASSET"

The list of all accounts in the book can be retrieved via the ``accounts`` attribute::

    for acc in s.accounts:
        print(acc.fullname)


Commodities and Prices
----------------------

The list of all commodities in the book can be retrieved via the ``commodities`` attribute::

    # all commodities
    print(s.commodities)

    cdty = s.commodities[0]

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

Transactions and Splits
-----------------------

The list of all transactions in the book can be retrieved via the ``transactions`` attribute::

    # all transactions
    print(s.transactions)

    tr = s.transactions[0]

    # accessing attributes of a transaction
    print("Transaction description='{tr.description}'\n"
          "            currency={tr.currency}\n"
          "            post_date={tr.post_date}\n"
          "            enter_date={tr.enter_date}".format(tr=tr))

and the related splits via the ``splits`` attribute of the transaction::

    for sp in tr.splits:
        print("     Split memo='{sp.memo}'\n"
              "           account={sp.account.fullname}\n"

Other objects
-------------

In fact, any object can be retrieved from the session through a generic ``get(**kwargs)`` method::

    from piecash import Account, Commodity, Budget, Vendor

    # accessing specific objects through the get method
    acc = s.get(Account, name="Asset", parent=s.book.root_account)
    cdty = s.get(Commodity, namespace="CURRENCY", mnemonic="EUR")
    bdgt = s.get(Budget, name="my first budget")
    invoice = s.get(Vendor, name="Looney")

If you know SQLAlchemy, you can get access to the underlying :class:`~sqlalchemy.orm.session.Session` as ``s.sa_session`` and execute
queries using the piecash classes::

    from piecash import Account, Commodity, Budget, Vendor

    # get the SQLAlchemy session
    session = s.sa_session

    # loop through all invoices
    for invoice in session.query(Invoice).all():
        print(invoice.notes)

.. note::

    Easy access to objects from :mod:`piecash.business` and :mod:`piecash.budget` could be given directly from the session
    in future versions if deemed useful.