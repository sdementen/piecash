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

    $ pip install pyscash

Usage
=====

The simplest workflow to use pyscash is first to open a SQLAlchemy session to a GnuCash Book

.. code-block:: python

    import pyscash

    # open a GnuCash Book
    session = pyscash.connect_to_gnucash_book("test.gnucash", readonly=True)


Use the SQLAlchemy session to query the Book, for example to query the stock prices

.. code-block:: python

    # example 1, print all stock prices in the Book
    # display all prices
    for price in session.query(pyscash.Price).all():
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

    for account in session.query(pyscash.Account).all():
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

Most basic objects used for personal finance are supported (Account, Split, Transaction, Price, ...).

A more complete example showing interactions with an existing GnuCash Book created from scratch in GnuCash
is available in the tests/ipython subfolder as ipython notebook (`ipython session <http://htmlpreview.github.io/?https://github.com/sdementen/pyscash/blob/master/tests/ipython/pyscash_session.html>`_)

To do:
======

- write more tests
- implement higher function to offer a higher level API than the SQLAlchemy layer
(for instance return a Book instead of SA session, be able to do Book.currencies to
return session.query(pyscash.Commodity).filter(Commodity.namespace == "CURRENCY").all())
- review non core objects (model_budget, model_business)
- write example scripts
- improve KVP support


Authors
=======

* sdementen
