=============
Documentation
=============

This project provides a simple and pythonic interface to GnuCash files stored in SQL (sqlite3, Pandostgres and MySQL)
for Linux and Windows (not tested on Mac OS).

piecash is a pure python package, tested on python 3.6/3.7/3.8, that can be used as an alternative to:

- the official python bindings (as long as no advanced book modifications and/or engine calculations are needed).
  This is specially useful on Windows where the official python bindings may be tricky to install or if you want to work with
  python 3.
- XML parsing/reading of XML GnuCash files if you prefer python over XML/XLST manipulations.

piecash is built on the excellent SQLAlchemy library and does not require the installation of GnuCash itself.

piecash allows you to:

- create a GnuCash book from scratch or edit an existing one
- create new accounts, transactions, etc or change (within some limits) existing objects.
- read/browse all objects through an intuitive interface

A simple example of a piecash script::

    with open_book("example.gnucash") as book:
        # get default currency of book
        print( book.default_currency )  # ==> Commodity<CURRENCY:EUR>

        # iterating over all splits in all books and print the transaction description:
        for acc in book.accounts:
            for sp in acc.splits:
                print(sp.transaction.description)

As piecash is essentially a SQLAlchemy layer, it could be potentially reused by any web framework that has
a SQLAlchemy interface to develop REST API or classical websites. It can also be used for reporting purposes.

The project has reached beta stage. Knowledge of SQLAlchemy is at this stage not anymore required to use it and/or
to contribute to it. Some documentation for developers on the object model of GnuCash as understood by the author is
available :doc:`here <../object_model>`.

.. warning::

   1) Always do a backup of your gnucash file/DB before using piecash.
   2) Test first your script by opening your file in readonly mode (which is the default mode)

Installation
============

To install with pip::

    $ pip install piecash

or to upgrade if piecash is already installed::

    $ pip install -U piecash

piecash comes with 6 extra options (each option depends on extra packages that will be installed only if the option is chosen):
 - pandas: install also pandas to use :meth:`piecash.core.book.Book.splits_df` and :meth:`piecash.core.book.Book.prices_df`
 - yahoo: to retrieve quotes/prices
 - postgres: to support connecting to a book saved on a postgresql database
 - mysql: to support connecting to a book saved on a mysql database
 - qif: to support export to QIF
For developers, two extra options:
 - test: to install what is needed for testing piecash
 - dev: to install what is needed for developing piecash (docs, ...)

To install these options, simply specify them between brackets after the piecash package::

    $ pip install piecash[pandas,qif,postgres]


To install with pipenv::

    $ pipenv install piecash

Otherwise, you can install by unpacking the source distribution from PyPI and then::

    $ python setup.py install

If you are on MS Windows and not so familiar with python, we would suggest you to install the miniconda python distribution
from Continuum Analytics available at http://conda.pydata.org/miniconda.html (you can choose whatever version 3.X
of python you would like) and then run the following command in the command prompt (cmd.exe)::

    $ conda create -n piecash_venv python=3 pip sqlalchemy
    $ activate piecash_venv
    $ pip install piecash

The first command create a new python environment named "piecash_venv" with python 3.7, pip and sqlalchemy installed.

The second command activates the newly created piecash_venv. Afterwards, you only need to execute this command before using
python through the command line.

The third command installs piecash and its dependencies. piecash depends also on sqlalchemy but as the sqlalchemy package requires
a compiler if it is installed through pip, we found it easier to install it through conda (this is done in the first command).

If you need to use directly the python interpreter in the newly created "piecash_env", you can find it
installed in your user folder under Miniconda3\\envs\\piecash_venv\\python.exe (or Miniconda2\\...).

On OS X, this option may also be valuable.

Quickstart
==========

The simplest workflow to use piecash starts by opening a GnuCash file

.. code-block:: python

    import piecash

    # open a GnuCash Book
    book = piecash.open_book("test.gnucash", readonly=True)

and then access GnuCash objects through the book, for example to query the stock prices

.. code-block:: python

    # example 1, print all stock prices in the Book
    # display all prices
    for price in book.prices:
        print(price)

.. parsed-literal::

    <Price 2014-12-22 : 0.702755 EUR/CAD>
    <Price 2014-12-19 : 0.695658 EUR/CAD>
    <Price 2014-12-18 : 0.689026 EUR/CAD>
    <Price 2014-12-17 : 0.69005 EUR/CAD>
    <Price 2014-12-16 : 0.693247 EUR/CAD>
    <Price 2014-12-22 : 51.15 USD/YHOO>
    <Price 2014-12-19 : 50.88 USD/YHOO>
    <Price 2014-12-18 : 50.91 USD/YHOO>
    <Price 2014-12-17 : 50.12 USD/YHOO>
    <Price 2014-12-16 : 48.85 USD/YHOO>
    ...

or to query the accounts:

.. code-block:: python

    for account in book.accounts:
        print(account)

.. parsed-literal::

    Account<[EUR]>
    Account<Assets[EUR]>
    Account<Assets:Current Assets[EUR]>
    Account<Assets:Current Assets:Checking Account[EUR]>
    Account<Assets:Current Assets:Savings Account[EUR]>
    Account<Assets:Current Assets:Cash in Wallet[EUR]>
    Account<Income[EUR]>
    Account<Income:Bonus[EUR]>
    Account<Income:Gifts Received[EUR]>
    ...
    Account<Expenses[EUR]>
    Account<Expenses:Commissions[EUR]>
    Account<Expenses:Adjustment[EUR]>
    Account<Expenses:Auto[EUR]>
    Account<Expenses:Auto:Fees[EUR]>
    ...
    Account<Liabilities[EUR]>
    Account<Liabilities:Credit Card[EUR]>
    Account<Equity[EUR]>
    Account<Equity:Opening Balances[EUR]>
    ...

or to create a new expense account for utilities:

.. code-block:: python

    # retrieve currency
    EUR = book.commodities.get(mnemonic='EUR')

    # retrieve parent account
    acc_exp = book.accounts.get(fullname="Expenses:Utilities")

    # add a new subaccount to this account of type EXPENSE with currency EUR
    new_acc = piecash.Account(name="Cable", type="EXPENSE", parent=acc_exp, commodity=EUR)

    # save changes (it should raise an exception if we opened the book as readonly)
    book.save()

Most basic objects used for personal finance are supported (Account, Split, Transaction, Price, ...).

The piecash command line interface
==================================

The `piecash` CLI offers the following features:

.. command-output:: piecash -h

To export specific entities out of a GnuCash book:

.. command-output:: piecash export -h

To export a GnuCash book to the ledger-cli format:

.. command-output:: piecash ledger -h

Or in python


.. ipython:: python

    book = open_book(gnucash_books + "simple_sample.gnucash", open_if_lock=True)

    from piecash import ledger

    # printing the ledger-cli (https://www.ledger-cli.org/) representation of the book
    print(ledger(book))

    # printing the ledger-cli (https://www.ledger-cli.org/) representation of the book using regional settings (locale) for currency output
    print(ledger(book, locale=True))

For more information on how to use piecash, please refer to the Tutorials on
:doc:`Using existing objects <../tutorial/index_existing>` and
:doc:`Creating new objects <../tutorial/index_new>`,
the :doc:`Example scripts <../tutorial/examples>` or
the :doc:`package documentation <../api/piecash>`.
