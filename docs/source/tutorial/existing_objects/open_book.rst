Opening an existing Book
------------------------

.. py:currentmodule:: piecash.core.book

To open an existing GnuCash document (and get the related :class:`Book`), use the :func:`open_book` function::

    import piecash

    # for a sqlite3 document
    book = piecash.open_book("existing_file.gnucash")

    # or through an URI connection string for sqlite3
    book = piecash.open_book(uri_conn="sqlite:///existing_file.gnucash")
    # or for postgres
    book = piecash.open_book(uri_conn="postgres://user:passwd@localhost/existing_gnucash_db")

The documents are open as readonly per default. To allow RW access, specify explicitly readonly=False as::

    book = piecash.open_book("existing_file.gnucash", readonly=False)

When opening in full access (readonly=False), piecash will automatically create a backup file named
filename.piecash_YYYYMMDD_HHMMSS with the original file. To avoid creating the backup file, specificy backup=False as::

    book = piecash.open_book("existing_file.gnucash", readonly=False, backup=False)

To force opening the file even through there is a lock on it, use the open_if_lock=True argument::

    book = piecash.open_book("existing_file.gnucash", open_if_lock=True)

Access to objects
-----------------

Once a GnuCash book is opened through a :class:`piecash.core.book.Book`, GnuCash objects can be accessed
through two different patterns:

The object model

    In this mode, we access elements through their natural relations, starting from the book and jumping
    from one object to the other:

    .. ipython::

        In [1]: book = open_book(gnucash_books + "default_book.gnucash")

        In [1]: book.root_account # accessing the root_account

        In [1]: # looping through the children accounts of the root_account
           ...: for acc in book.root_account.children:
           ...:     print(acc)

        # accessing children accounts
        In [1]:
           ...: root = book.root_account              # select the root_account
           ...: assets = root.children(name="Assets")   # select child account by name
           ...: cur_assets = assets.children[0]         # select child account by index
           ...: cash = cur_assets.children(type="CASH") # select child account by type
           ...: print(cash)

        In [1]: # get the commodity of an account
           ...: commo = cash.commodity
           ...: print(commo)

        In [1]: # get first ten accounts linked to the commodity commo
           ...: for acc in commo.accounts[:10]:
           ...:     print(acc)


The "table" access

    In this mode, we access elements through collections directly accessible from the book:

    .. ipython:: python

        book = open_book(gnucash_books + "default_book.gnucash")

        # accessing all accounts
        book.accounts

        # accessing all commodities
        book.commodities

        # accessing all transactions
        book.transactions


    Each of these collections can be either iterated or accessed through some indexation or filter mechanism (return
    first element of collection satisfying some criteria(s)):

    .. ipython:: python

        # iteration
        for acc in book.accounts:
            if acc.type == "ASSET": print(acc)

        # indexation (not very meaningful)
        book.accounts[10]

        # filter by name
        book.accounts(name="Garbage collection")

        # filter by type
        book.accounts(type="EXPENSE")

        # filter by fullname
        book.accounts(fullname="Expenses:Taxes:Social Security")

        # filter by multiple criteria
        book.accounts(commodity=book.commodities[0], name="Gas")

The "SQLAlchemy" access (advanced users)

    In this mode, we access elements through SQLAlchemy queries on the SQLAlchemy session:

    .. ipython:: python

        # retrieve underlying SQLAlchemy session object
        session = book.session

        # get all account with name >= "T"
        session.query(Account).filter(Account.name>="T").all()

        # display underlying query
        str(session.query(Account).filter(Account.name>="T"))
