piecash
=======


.. image:: https://travis-ci.org/sdementen/piecash.svg?branch=master
    :target: https://travis-ci.org/sdementen/piecash

.. image:: https://ci.appveyor.com/api/projects/status/af7mb3pwv31i6ltv/branch/master?svg=true
    :target: https://ci.appveyor.com/project/sdementen/piecash

.. image:: https://readthedocs.org/projects/piecash/badge/?version=master
    :target: http://piecash.readthedocs.org

.. image:: https://img.shields.io/pypi/v/piecash.svg
    :target: https://pypi.python.org/pypi/piecash

.. image:: https://img.shields.io/pypi/pyversions/piecash.svg
    :target: https://pypi.python.org/pypi/piecash/

.. image:: https://img.shields.io/pypi/dd/piecash.svg
    :target: https://pypi.python.org/pypi/piecash/

.. image:: https://requires.io/github/sdementen/piecash/requirements.svg?branch=master
    :target: https://requires.io/github/sdementen/piecash/requirements/?branch=master

.. image:: https://coveralls.io/repos/sdementen/piecash/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/sdementen/piecash?branch=master


Piecash provides a simple and pythonic interface to GnuCash files stored in SQL (sqlite3, Postgres and MySQL).

:Documentation: http://piecash.readthedocs.org.
:Google group: https://groups.google.com/d/forum/piecash (piecash@googlegroups.com)
:Github: https://github.com/sdementen/piecash
:PyPI: https://pypi.python.org/pypi/piecash


It is a pure python package, tested on python 2.7 and 3.3/3.4/3.5, that can be used as an alternative to:

- the official python bindings (as long as no advanced book modifications and/or engine calculations are needed).
  This is specially useful on Windows where the official python bindings may be tricky to install or if you want to work with
  python 3.
- XML parsing/reading of XML GnuCash files if you prefer python over XML/XLST manipulations.

piecash test suite runs successfully on Windows and Linux on the three supported SQL backends (sqlite3, Postgres and MySQL).
piecash has also been successfully run on Android (sqlite3 backend) thanks to Kivy buildozer and python-for-android.

It allows you to:

- open existing GnuCash documents and access all objects within
- modify objects or add new objects (accounts, transactions, prices, ...)
- create new GnuCash documents from scratch

Scripts are also available to:

- export to ledger-cli format (http://www.ledger-cli.org/)
- export to QIF format
- import/export prices (CSV format)

A simple example of a piecash script:

.. code-block:: python

    with open_book("example.gnucash") as book:
        # get default currency of book
        print( book.default_currency )  # ==> Commodity<CURRENCY:EUR>

        # iterating over all splits in all books and print the transaction description:
        for acc in book.accounts:
            for sp in acc.splits:
                print(sp.transaction.description)

The project has reached beta stage.

.. warning::

   1) Always do a backup of your gnucash file/DB before using piecash.
   2) Test first your script by opening your file in readonly mode (which is the default mode)


