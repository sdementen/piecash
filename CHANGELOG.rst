What's new
==========

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