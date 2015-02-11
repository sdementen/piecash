Opening an existing Book
------------------------

.. py:currentmodule:: piecash.core.session

To open an existing GnuCash document (and get the related :class:`GncSession`), use the :func:`open_book` function::

    import piecash

    # for a sqlite3 document
    s = piecash.open_book("existing_file.gnucash")

    # or through an URI connection string for sqlite3
    s = piecash.open_book(uri_conn="sqlite:///existing_file.gnucash")
    # or for postgres
    s = piecash.open_book(uri_conn="postgres://user:passwd@localhost/existing_gnucash_db")

The documents are open as readonly per default. To allow RW access, specify explicitly readonly=False as::

    s = piecash.open_book("existing_file.gnucash", readonly=False)

When opening in full access (readonly=False), piecash will automatically create a backup file named
filename.piecash_YYYYMMDD_HHMMSS with the original file. To avoid creating the backup file, specificy backup=False as::

    s = piecash.open_book("existing_file.gnucash", readonly=False, backup=False)

To force opening the file even through there is a lock on it, use the open_if_lock=True argument::

    s = piecash.open_book("existing_file.gnucash", open_if_lock=True)

Access to objects
-----------------

Once a GnuCash book is opened through a :class:`piecash.core.session.GncSession`, GnuCash objects can be accessed
through two different patterns:

The object model

    In this mode, we access elements through their natural relations, starting from the book and jumping
    from one object to the other:

    .. ipython::

        In [1]: s = open_book(gnucash_books + "default_book.gnucash")

        In [1]: s.book      # accessing the book

        In [1]: s.book.root_account # accessing the root_account

        In [1]: # looping through the children accounts of the root_account
           ...: for acc in s.book.root_account.children:
           ...:     print(acc)

        # accessing children accounts
        In [1]:
           ...: root = s.book.root_account              # select the root_account
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

        In [1]: s.close()


The "table" access

    In this mode, we access elements through collections directly accessible from the session:

    .. ipython:: python

        s = open_book(gnucash_books + "default_book.gnucash")

        # accessing all accounts
        s.accounts

        # accessing all commodities
        s.commodities

        # accessing all transactions
        s.transactions


    Each of these collections can be either iterated or accessed through some indexation or filter mechanism (return
    first element of collection satisfying some criteria(s)):

    .. ipython:: python

        # iteration
        for acc in s.accounts:
            if acc.type == "ASSET": print(acc)

        # indexation (not very meaningful)
        s.accounts[10]

        # filter by name
        s.accounts(name="Garbage collection")

        # filter by type
        s.accounts(type="EXPENSE")

        # filter by fullname
        s.accounts(fullname="Expenses:Taxes:Social Security")

        # filter by multiple criteria
        s.accounts(commodity=s.commodities[0], name="Gas")

The "SQLAlchemy" access (advanced users)

    In this mode, we access elements through SQLAlchemy queries on the SQLAlchemy session:

    .. ipython:: python

        # retrieve underlying SQLAlchemy session object
        session = s.sa_session

        # get all account with name >= "T"
        session.query(Account).filter(Account.name>="T").all()

        # display underlying query
        str(session.query(Account).filter(Account.name>="T"))
