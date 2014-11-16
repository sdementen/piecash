======================================
Python GnuCash SQL interface (piecash)
======================================

Project
=======

This project provides a simple and pythonic CRUD interface to a GnuCash Book stored in SQL (sqlite3 or Postgres).
It is a pure python package relying on SQL Alchemy. It can be used as an alternative to:
- the official python bindings (if no advanced engine calculations are needed)
- XLST transformations of the XML GnuCash document

It is basically a SQLAlchemy layer augmented with methods to ease the manipulation of the GnuCash objects.

Project is in early development. Knowledge of SQLAlchemy is at this stage a probably required to use it and/or
to contribute to it. Some documentation for developers on the object model of GnuCash as understood by the author is
available `here <https://github.com/sdementen/piecash/blob/master/docs/source/object_model.rst>`_.

Installation
============

From pip::

    $ pip install piecash

Usage
=====

The simplest workflow to use piecash is first to open a SQLAlchemy session to a GnuCash Book

.. code-block:: python

    import piecash

    # open a GnuCash Book
    book = piecash.connect_to_gnucash_book("test.gnucash", readonly=True)
    session = book.get_session()


Use the SQLAlchemy session to query the Book, for example to query the stock prices

.. code-block:: python

    # example 1, print all stock prices in the Book
    # display all prices
    for price in session.query(piecash.Price).all():
        print "{}/{} on {} = {} {}".format(price.commodity.namespace,
                                           price.commodity.mnemonic,
                                           price.date,
                                           float(price.value_num) / price.value_denom,
                                           price.currency.mnemonic,
                                           )

.. parsed-literal::

    NASDAQ/CZR on 2014-11-12 14:27:00 = 13.65 USD
    ...

or to query the accounts:

.. code-block:: python

    for account in session.query(piecash.Account).all():
        print account

.. parsed-literal::

    Account<>
    Account<Assets>
    Account<Assets:Current Assets>
    Account<Assets:Current Assets:Checking Account>
    Account<Assets:Current Assets:Savings Account>
    Account<Assets:Current Assets:Cash in Wallet>
    Account<Liabilities>
    Account<Liabilities:Credit Card>
    Account<Income>
    Account<Income:Bonus>
    Account<Income:Gifts Received>
    ...

or to create a new account below some existing account:

.. code-block:: python

    # build map between account fullname (e.g. "Assets:Current Assets" and account)
    map_fullname_account = {account.fullname():account for account in session.query(piecash.Account).all()}

    # use it to retrieve the current assets account
    acc_cur = map_fullname_account["Assets:Current Assets"]

    # retrieve EUR currency
    EUR = session.query(piecash.Commodity).filter_by(mnemonic='EUR')

    # add a new subaccount to this account of type ASSET with currency EUR
    piecash.Account(name="new savings account", account_type="ASSET", parent=acc_cur, commodity=EUR)

    # save changes
    session.commit()


Most basic objects used for personal finance are supported (Account, Split, Transaction, Price, ...).

A more complete example showing interactions with an existing GnuCash Book created from scratch in GnuCash
is available in the tests/ipython subfolder as ipython notebook (`ipython session <http://htmlpreview.github.io/?https://github.com/sdementen/piecash/blob/master/tests/ipython/pyscash_session.html>`_)

To do:
======

- write more tests
- implement higher function to offer a higher level API than the SQLAlchemy layer
  (for instance return a Book instead of SA session, be able to do Book.currencies to
  return session.query(piecash.Commodity).filter(Commodity.namespace == "CURRENCY").all())
- review non core objects (model_budget, model_business)
- write example scripts
- improve KVP support


Authors
=======

* sdementen
