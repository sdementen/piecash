======================================
Python GnuCash SQL interface (pyscash)
======================================

Project
=======

This project provides a simple interface to a GnuCash Book stored in SQL (sqlite3 or Postgres).
It is basically a SQLAlchemy layer augmented with methods to ease the manipulation of core GnuCash objects.

Project is in early development. Knowledge of SQLAlchemy is a probably required...

Installation
============

From pip::

    $ pip install --upgrade rstcheck

Usage
=====

Here is a simple example of an interaction with an existing GnuCash Book created from scratch in GnuCash.


.. code:: python

    import pyscash
    import datetime
.. code:: python

    # open a SQLAlchemy session linked to the test.gnucash file (as sqlite3 saved Book)
    s = pyscash.connect_to_gnucash_book("test.gnucash", readonly=False)
.. code:: python

    # retrieve the single Book object from the session (this is a sqlalchemy standard call)
    book = s.query(pyscash.Book).one()
    # retrieve the EUR currency
    EUR = s.query(pyscash.Commodity).one()
.. code:: python

    # from the book, retrieve the root account and display its children accounts
    book.root_account.children



.. parsed-literal::

    [Account<Assets>,
     Account<Liabilities>,
     Account<Income>,
     Account<Expenses>,
     Account<Equity>]



.. code:: python

    # retrieve the standard 3 default assets accounts (checking account, saving account, cash in wallet)
    curacc, savacc, cash = book.root_account.children[0].children[0].children
.. code:: python

    # check splits (they should be empty if the GnuCash book was an empty Book)
    savacc.splits, curacc.splits



.. parsed-literal::

    ([], [])



.. code:: python

    # create a transaction of 45 € from the saving  account to the checking account
    tr = pyscash.Transaction.single_transaction(datetime.date.today(),datetime.date.today(), "transfer of money", 45, EUR, savacc, curacc)
.. code:: python

    # check some attributes of the transaction
    tr.description, tr.splits



.. parsed-literal::

    ('transfer of money',
     [<Split Account<Assets:Current Assets:Savings Account> -45>,
      <Split Account<Assets:Current Assets:Checking Account> 45>])



.. code:: python

    # check the splits from the accounts point of view
    savacc.splits, curacc.splits



.. parsed-literal::

    ([<Split Account<Assets:Current Assets:Savings Account> -45>],
     [<Split Account<Assets:Current Assets:Checking Account> 45>])



.. code:: python

    # rollback the session (i.e. undo all changes)
    s.rollback()
.. code:: python

    # check splits after the rollback (they should be unchanged)
    savacc.splits, curacc.splits



.. parsed-literal::

    ([], [])


Authors
=======

* sdementen
