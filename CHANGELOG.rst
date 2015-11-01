What's new
==========

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