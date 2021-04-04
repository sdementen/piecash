What's new
==========

Version 1.1.7 (2021-04-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix issue when deleting splits (fix #155)
- reformat files with black


Version 1.1.6 (2021-04-03)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- add `at_date` parameter to `Account.get_balance` (tx @rvijayc, @gregwalters)

Version 1.1.5 (2021-03-21)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix ledger export truncation of prices (fix #158)
- fix ledger export to order transactions by date (fix #159)

Version 1.1.4 (2021-01-29)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- allow tags with zero quantity by fixing unit price calculation (fix #153, tx @croth1)
- allow tags with zero quantity of value by fixing validation control (fix #154, tx @stoklund)
- use template0 when creating new books in postgres (vs template1 before) to fix encoding issues
- add examples for deleting an account and exporting transactions to a CSV file

Version 1.1.3 (2021-01-17)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- requires sqlalchemy < 1.4 (fix #149)
- fix example with wrong post_date type
- update currency_ISO
- update use of deprecated function in xml (fix #147, tx @bxbrenden)
- add example of program to modify an existing transaction

Version 1.1.2 (2020-10-24)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- import requests from functions using it to avoid making it a required dependency (fix #90)
- adapt setup.py to avoid depending on SQLAlchemy-Utils 0.36.8 (fix #91)
- updated gnucash projects page: https://piecash.readthedocs.io/en/latest/doc/github_links.html


Version 1.1.1 (2020-10-21)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- add a check_exists flag to allow bypassing check existence of DB on opening (fix #91, tx @williamjacksn)

Version 1.1.0 (2020-10-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix use of ISO date for ledger export (fix #115 by @MisterY)
- add field is_credit and is_debit to split (fix #105)
- fix get_balance sign when recursing + add natural_sign keyword to specify if sign should be reverse or not
- add support for Gnucash 4.1 (fix #136)
- fix table names not matching in case (fix #137)
- fix test suite to support 3.8
- deprecate python 3.5
- quandl will retrieve API KEY from environment variable QUANDL_API_KEY (if defined)
- yahoo will use exchangeTimezoneName for timezone (vs exchangeTimezoneShortName before), thanks @geoffwright240
- add possibility to export accounts with their short name in ledger (fix #123)


Version 1.0.0 (2019-04-15)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- drop support of py27 and py34 (fix #53)
- support gnucash 3.0.x format (code + test and book migration)
- set autoflush to False for open_book (was only done for create_book before) (fix #93)
- remove tz info when serialising DateTime to SQL (issue with postgresql doing some TZ conversion)
- add basic support for Jobs


Version 0.18.0 (2018-04-24)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mostly refactoring:
- refactor common parts of vendor, customer and employee into person
- add 'on_book_add' protocol called when object is added to a book
- set autoflush to False to prevent weird behavior when using slots (that retrigger a query in the middle of a flush)
- refactor slots
- align sql schema 100% with 2.6.21 (based on sqlite reference)
- support business slots


Version 0.17.0 (2018-03-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- internal refactoring of setup.py
- add optional packages
- move to pipenv
- improve documentation
- fix missing extra blank between account name and amount in ledger export (fix #86)


Version 0.16.0 (2018-03-04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- add a documentation section about piecash on android
- fix yahoo finance quote retrieval
- indicate correct reconcile state in ledger output (fix #77)



Version 0.15.0 (2018-02-21)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- add piecash CLI (refactor of scripts)
- add book.invoices to retrieve all invoices in a book
- expose gnucash rationals as decimals in Entry and Invoice
- fix issue #65 about "template" (scheduled transactions) appearing in ledger export
- fix issue #64 about escaping in double quote mnemonic with non alpha characters
- fix issue #19 allowing to pass the check_same_thread flag for sqlite
- add argument recurse to get_balance (fix #73)
- handle currency conversion in get_balance
- add Commodity.currency_conversion to get a conversion factor between a commodity and a currency


Version 0.14.1 (2018-02-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix bug in pc-export

Version 0.14.0 (2018-02-01)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- fix definition of account get_balance to use quantities (and not values) (@sdementen)
- fix bug when providing a float instead of a Decimal to a numeric value (@gregorias)
- support new format for date for 2.7/2.8 (@MisterY, @sdementen)
- fix bug where transactions based on deleted scheduled transactions cause exceptions (@spookylukey)
- fix bug (#58) where large Decimals where raising an sql exception instead of a ValueError exception (@sdementen)
- add Recurrence to global imports + add documentation to Recurrence (@MisterY)
- add script pc-export to export customers and vendors from a gnucash book (@sdementen)

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
