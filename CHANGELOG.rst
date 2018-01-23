What's new
==========


In development
~~~~~~~~~~~~~~

- add get_quantity on an account to retrieve the balance in quantity of the accound (for non currency based accounts)
- fix bug when providing a float instead of a Decimal to a numeric value (@gregorias)
- support new format for date for 2.7/2.8 (@MisterY, @sdementen)
- fix bug where transactions based on deleted scheduled transactions cause exceptions (@spookylukey)

Version 0.13.0 (2017-10-08)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- upgrade CI (appveyor and travis) to 2.7/3.4/3.5/3.6
- upgrade dependencies
- df_splits: allow user to specify additional fields to extract (@NigelCleland)
- improve documentation (@Brian-K-Smith)


Version 0.12.0 (2017-02-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- rely on yahoo-finance to retrieve share information and share prices
- use only ISO currency static data (remove support for looking on the web)
- normalise post_date to 11:00AM

Version 0.11.0 (2016-11-13)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- add support for python 3.5
- add preload method on book to allow preloading all objects at once

Version 0.10.2 (2015-12-06)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- add children argument to Account constructor
- add a new example (used as answer to http://stackoverflow.com/questions/17055318/create-transaction-in-gnucash-in-response-to-an-email/ )
- add a new example showing how to export Split information to pandas DataFrames
- fix an error handling in retrieving currency exchanges in quandl
- fix py3 bugs in dataframe functions
- fix type and source of Pricers to be compatible with GnuCash
- add a Price when entering a commodity Split
- set microsecond to 0 for all datetime
- add pandas for requirements-dev
- add tests for deletion of transaction and for dataframe functions



Version 0.10.1 (2015-11-29)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- refactor the validation mechanism to work well with autoflush=True
- add support to GLIST in KVP
- add new matching rule for GUID slots
- rename slot 'default_currency' to 'default-currency'
- add tests for single_transaction factory
- update ipython example with pandas dataframes

Version 0.10.0 (2015-11-18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- first draft of splits_df and prices_df methods that bring the book data into pandas DataFrames
- add an ipython notebook to show the new dataframes methods
- save default_currency of a book in a slot (when book created by piecash) or use locale to retrieve the default_currency
- improve error handling for quandl queries (currency exchange rates)

Version 0.9.1 (2015-11-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix bug with unicode on MySQL

Version 0.9.0 (2015-11-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- ported to SQLAlchemy-1.0
- set autoflush=true on the SA session
- improved coverage above 90% for all modules
- setup coveralls.io and requires.io
- fix bugs discovered by improved testing

Version 0.8.4 (2015-11-14)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- use AppVeyor for Windows continuous integration and for .exe freezing
- fix bugs in tests suite where files were not properly closed
- add Book.close function to close properly files
- depend on enum-compat instead of directly enum34
- add simple script to import/export prices from a gnucash book

Version 0.8.3 (2015-11-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix issue #8 re enum34
- updated sqlalchemy dep to use latest 0.9 series

Version 0.8.2 (2015-05-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- implementing support for creating Customer, Vendor and Employee objects as well as taxtables

Version 0.8.1 (2015-05-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- get 100% coverage on transaction module (except for scheduled transactions)
- account.full_name returns now unicode string


Version 0.8.0 (2015-05-02)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- get 100% coverage on book and account module
- fix repr and str representations of all objects to be compatible py2 and py3


Version 0.7.6 (2015-05-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix version requirement for SA (<0.9.9) and SA-utils

Version 0.7.5 (2015-03-14)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- improve doc on installation on windows through conda
- add .gitattributes to exclude html from githug language detection algorithm
- update github project list
- refactor sqlite isolation level code
- fix setup.py to avoid sqlalchemy 0.9.9 (buggy version)
- fix requirements.txt to avoid sqlalchemy 0.9.9 (buggy version)

Version 0.7.4 (2015-03-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- remove some remaining print in code

Version 0.7.3 (2015-03-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix requirements to include ipython==2.3.1

Version 0.7.2 (2015-03-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix bug in doc (was using ledger_str instead of ledger)

Version 0.7.1 (2015-03-09)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- refactor ledger functionalities
- bug fixing
- read backup functionality (ie backup when opening a book in RW)

Version 0.7.0 (2015-02-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Merge the GncSession and Book objects
- extract factory function into a factories module

Version 0.6.2 (2015-02-02)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- add reference to google groups
- disable acquiring lock on file

Version 0.6.1 (2015-02-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix: qif scripts was not included in package

Version 0.6.0 (2015-02-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- add a basic QIF exporter script as piecash_toqif
- implemented "Trading accounts"
- improved documentation
- other small api enhancements/changes

Version 0.5.11 (2015-01-12)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- add a ledger_str method to transaction to output transaction in the ledger-cli format
- add label to Decimal field in sqlalchemy expr
- add backup option when opening sqlite file in RW (enabled by default)
- renamed tx_guid to transaction_guid in Split field
- fix technical bug in validation of transaction

Version 0.5.10 (2015-01-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- add keywords to setup.py


Version 0.5.8 (2015-01-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- add notes to Transaction (via slot)
- removed standalone exe from git/package (as too large)

Version 0.5.7 (2015-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- add sign property on account
- raise NotImplementedError when creating an object is not "safe" (ie not __init__ and validators)
- renamed slot_collection to slots in kvp handling
- renamed field of Version + add explicit __init__
- updated test to add explicit __init__ when needed

Version 0.5.6 (2015-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- reordering of field definitions to match gnucash order (finished)
- add autoincr

Version 0.5.5 (2015-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- reordering of field definitions to match gnucash order (to complete)

Version 0.5.4 (2015-01-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- added back the order table in the declarations

Version 0.5.3 (2015-01-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- add support for schedule_transactions and lots (in terms of access to data, not business logic)
- improved doc

Version 0.5.2 (2015-01-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- reworked documentation
- moved Lot and ScheduledTransaction to transaction module + improved them
- improve slots support
- fixed minor bugs

Version 0.5.1 (2014-12-30)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fixed changelog/what's new documentation

Version 0.5.0 (2014-12-30)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- improve relationship in business model
- fix account.placeholder validation in transaction/splits
- made all relationships dual (with back_populates instead of backref)

Version 0.4.4 (2014-12-28)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix bug in piecash_ledger (remove testing code)
- improve documentation of core objects
- fix dependencies for developers (requests)
- regenerate the github list of projects

Version 0.4.0 (2014-12-28)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- improve bumpr integration

Version 0.3.1
~~~~~~~~~~~~~

- renamed modules in piecash packages
- updated doc

Version 0.3.0
~~~~~~~~~~~~~

.. py:currentmodule:: piecash.model_core.commodity

- ported to python 3.4
- refactored lot of classes
- improved documentation
- added helper functions:

  - :func:`Commodity.create_currency_from_ISO`
  - :func:`Commodity.create_stock_from_symbol`
  - :func:`Commodity.update_prices`
  - :func:`Commodity.create_stock_accounts`
