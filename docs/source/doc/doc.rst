=============
Documentation
=============

This project provides a simple and pythonic interface to GnuCash files stored in SQL (sqlite3 and Postgres, not tested in MySQL).

piecash is a pure python package, tested on python 2.7 and 3.4, that can be used as an alternative to:

- the official python bindings (as long as no advanced book modifications and/or engine calculations are needed).
  This is specially useful on Windows where the official python bindings may be tricky to install or if you want to work with
  python 3.
- XML parsing/reading of XML GnuCash files if you prefer python over XML/XLST manipulations.

piecash is built on the excellent SQLAlchemy library and does not require the installation of GnuCash itself.

piecash allows you to:

- create a GnuCash document from scratch or edit an existing one
- create new accounts, transactions, etc or change (within some limits) existing objects.
- read/browse all objects through an intuitive interface

A simple example of a piecash script::

    with open_book("example.gnucash") as s:
        # get default currency of book
        print( s.book.default_currency )  # ==> Commodity<CURRENCY:EUR>

        # iterating over all splits in all books and print the transaction description:
        for acc in s.accounts:
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

To install with easy_install::

    $ easy_install piecash

Otherwise, you can install by unpacking the source distribution from PyPI and then::

    $ python setup.py install

If you are on windows and not so familiar with python, we would suggest you to install the miniconda python distribution
available at http://conda.pydata.org/miniconda.html (you can choose whatever version - 2.7 or 3.X - of python you would like)
and then::

    $ conda install pip sqlalchemy
    $ pip install piecash

On OS X, this option may also be valuable.

Quickstart
==========

The simplest workflow to use piecash starts by opening a GnuCash file

.. code-block:: python

    import piecash

    # open a GnuCash Book
    session = piecash.open_book("test.gnucash", readonly=True)

and then access GnuCash objects through the session, for example to query the stock prices

.. code-block:: python

    # example 1, print all stock prices in the Book
    # display all prices
    for price in session.prices:
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

    for account in session.accounts:
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
    EUR = session.commodities.get(mnemonic='EUR')

    # retrieve parent account
    acc_exp = session.accounts.get(fullname="Expenses:Utilities")

    # add a new subaccount to this account of type EXPENSE with currency EUR
    new_acc = piecash.Account(name="Cable", type="EXPENSE", parent=acc_exp, commodity=EUR)

    # save changes (it should raise an exception if we opened the book as readonly)
    session.save()

Most basic objects used for personal finance are supported (Account, Split, Transaction, Price, ...).

For more information on how to use piecash, please refer to the Tutorials on
:doc:`Using existing objects <../tutorial/index_existing>` and
:doc:`Creating new objects <../tutorial/index_new>`,
the :doc:`Example scripts <../tutorial/examples>` or
the :doc:`package documentation <../api/piecash>`.
