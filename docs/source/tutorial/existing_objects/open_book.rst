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

Per default, piecash will acquire a lock on the file (as GnuCash does). To avoid acquiring the lock, you can
set the acquire_lock=False argument::

    s = piecash.open_book("existing_file.gnucash", acquire_lock=False)

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

        In [1]: import os

        In [1]: os.path.abspath(os.curdir)

        In [1]: s = open_book("../gnucash_books/default_book.gnucash")

        In [1]: s.book      # accessing the book

        In [1]: s.book.root_account # accessing the root_account

        In [1]: # looping through the children accounts of the root_account
           ...: for acc in s.book.root_account.children:
           ...:     print(acc)

        In [1]: # accessing children accounts
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

    .. ipython::

        In [1]: s = open_book("../gnucash_books/default_book.gnucash")

        In [1]: s.accounts  # accessing all accounts

        In [1]: s.commodities  # accessing all commodities

        In [1]: s.transactions  # accessing all transactions

    Each of these collections can be either iterated or accessed through some indexation or filter mechanism (return
    first element of collection satisfying some criteria(s)):

    .. ipython::

        In [1]: for acc in s.accounts:  # iteration
           ...:     if acc.type == "ASSET": print(acc)

        In [1]: s.accounts[10]  # indexation

        In [1]: s.accounts(name="Garbage collection")  # filter by name

        In [1]: s.accounts(type="EXPENSE")  # filter by type

        In [1]: s.accounts(fullname="Expenses:Taxes:Social Security") # filter by fullname

        In [1]: s.accounts(commodity=s.commodities[0], name="Gas") # filter by multiple criteria

The "SQLAlchemy" access (advanced users)
    In this mode, we access elements through SQLAlchemy queries on the SQLAlchemy session:

    .. ipython::

        In [1]: session = s.sa_session # retrieve underlying SQLAlchemy session object

        In [1]: session.query(Account).filter(Account.name>="T").all() # get all account with name >= "T"

        In [1]: # display underlying query
           ...: str(session.query(Account).filter(Account.name>="T"))
