===================================
GnuCash SQL Object model and schema
===================================

A clear documentation of the SQL schema (tables, columns, relationships) and the implicit semantic (invariants that should
be always satisfied, logic to apply in ambiguous/corner cases) is critical for piecash to

 a) ensure data integrity
 b) ensure compatibility in semantic with the official GnuCash application

.. warning::

    This document explains what the author understands in these domains. It is not the reference documentation, please refer
    to the official GnuCash documentation for this.

Core objects
============

There are 5 core objects in GnuCash  : `Book`_, `Commodity`_, `Account`_, `Transaction`_, `Split`_.
An additional object, the `Price`_, is used in reports and for display (for instance, to convert all accounts balance
in the default currency). While not as core as the others, it is an essential piece of functionality for anyone using
GnuCash to track a stock portfolio value.

.. note::

    A priori, all these objects are all "create once, never change" objects. Changing some fields of an object may lead to
    complex renormalisation procedures. Deleting some objects may lead to complex cascade changes/renormalisation procedures.
    In this respect, it is important to either avoid changes/deletions or to have clear invariants that should stay true at any time.


Book
----

The Book is the object model representing a GnuCash document. It has a link to the root account, the account at the
root of the tree structure.

Fields
~~~~~~
root_account (mandatory)
  The account at the root of the tree structure

root_template (???)
  Use to be investigated...


Invariant
~~~~~~~~~
 - one (and only one) Book per GnuCash document


Questions
~~~~~~~~~

 - in the XML version, the book encapsulates the whole XML structure. If we had two books in a single xml document,
   they would not share the commodities. In the C api, the creation of a commodity requires a Book.

   In the SQL version, the book only has a root_account. It has no directly link to the other objects. If we had to have
   two Books in a single document, they would de facto share the Commodity/Price/etc as there is no explicit link between
   the Commodity/Price/etc and the book ?

Commodity
---------

A Commodity is either a currency (€, $, ...) or a commodity/stock that can be stored in/traded through an Account.

The Commodity object is used in two different (but related) contexts.

 a) each Account should specify the Commodity it handles/stores. For usual accounts (Savings, Expenses, etc), the Commodity
    is a currency. For trading accounts, the Commodity is usually a stock (AMZN, etc).
    In this role, each commodity (be it a stock or a currency) can have Prices attached to it that give the value of the
    commodity expressed in a given currency.

 b) each Transaction should specify the Currency which is used to balance itself.


Fields
~~~~~~
namespace (mandatory)
  A string representing the group/class of the commodity. All commodities that are currencies should have 'CURRENCY' as
  namespace. Non currency commodities should have other groups.

mnemonic (mandatory)
  The symbol/stock sticker of the commodity (relevant for online download of quotes)

fullname
  The full name for the commodity. Besides the fullname, there is a "calculated property" unique_name equal to "namespace::mnemonic"

cusip
  unique code for the commodity

fraction
  The smallest unit that can be accounted for (for a currency, this is equivalent to the scu, the smallest currency unit)
  This is essentially used for a) display and b) roundings

quote_flag
  True if Prices for the commodity should be retrieved for the given stock. This is used by the "quote download" functionnality.

quote_source
  The source for online download of quotes



Invariant
~~~~~~~~~

 - a currency commodity has namespace=='CURRENCY'
 - currencies can not be created (could not find a way to do it in the GUI)
 - a stock commodity has namespace!='CURRENCY'


Questions
~~~~~~~~~
None


Account
-------

An account tracks some commodity for some business purpose. Changes in the commodity amounts are modelled through Splits
(see Transaction & Splits).

Fields
~~~~~~

account_type (mandatory)
  the type of the account as string

commodity (mandatory)
  The commodity that is handled by the account

parent (almost mandatory)
  the parent account to which the account is attached. All accounts but the root_account should have a parent account.

commodity_scu (mandatory)
  The smallest currency/commodity unit is similar to the fraction of a commodity. It is the smallest amount of the commodity
  that is tracked in the account. If it is different than the fraction of the commodity to which the account is linked,
  the field non_std_scu is set to 1 (otherwise the latter is set to 0).

name
  self-explanatory

description
  self-explanatory

placeholder
  if True/1, the account cannot be involved in transactions through splits (ie it can only be the parent of other accounts).
  if False/0, the account can have Splits referring to it (as well as be the parent of other accounts)

hidden
  to be investigated


Invariant
~~~~~~~~~
 - if placeholder, no Splits can refer to account
 - only one account can have account_type ROOT


Questions
~~~~~~~~~
 - changing the placeholder status of an account with splits in gnucash does not trigger any warning, is it normal ?
   is the placeholder flag just informative (or used for reporting)  ?
 - are there any constrains on the account_type of an account wrt account_type of its parent ?

.. _Transaction:

.. _Split:

Transaction & Splits
--------------------

The transaction represents movement of money between accounts expressed in a given currency (the currency of the transaction).
The transaction is modelled through a set of Splits (2 or more).
Each Split is linked to an Account and gives the increase/decrease in units of the account commodity (quantity)
related to the transaction as well as the equivalent amount in currency (value).
For a given transaction, the sum of the split expressed in the currency (value) should be balanced.

Fields for Transaction
~~~~~~~~~~~~~~~~~~~~~~
currency (mandatory)
  The currency of the transaction

num (optional)
  A transaction number (only used for information ?)

post_date (mandatory)
  self-explanatory

enter_date (mandatory)
  self-explanatory

description (mandatory)
  self-explanatory

Fields for Split
~~~~~~~~~~~~~~~~
tx (mandatory)
  the transaction of the split

account (mandatory)
  the account to which the split refers to

value (mandatory)
  the value of the split expressed in the currency of the transaction

quantity (mandatory)
  the change in quantity of the account expressed in the commodity of the account

reconcile information
  to be filled

lot
  reference to the lot (to be investigated)

Invariant
~~~~~~~~~

 - the sum of the value on all splits in a transaction should = 0 (transaction is balanced). If it is not the case, the
   GnuCash application create automatically an extra Split entry towards the Account Imbalance-XXX (with XXX the currency
   of the transaction)
 - the value and quantity fields are expressed as numerator / denominator. The denominator of the value should be
   the same as the fraction of the currency. The denominator of the quantity should be the same as the commodity_scu of
   the account.

Questions
~~~~~~~~~

 - how is the currency of the transaction defined ? is the default currency (in gnucash preferences) ? is it the
   currency (if any) of the account into which the transaction is initiated in the gui ? can this be changed through the GUI ?
 - what happens to the splits of an account that is removed ? in GUI, splits are either moved to other account or deleted
   with a corresponding entry created in the Imbalance-XXX account.
 - what happens to the splits when the currency of a transaction is changed ? the quantity and value do not change
   (irrespective of any exchange rate) ?


Price
-----

The Price represent the value of a commodity in a given currency at some time.

It is used for exchange rates and stock valuation.

Fields
~~~~~~
commodity (mandatory)
  the commodity related to the Price

currency (mandatory)
  The currency of the Price

datetime (mandatory)
  self-explanatory (expressed in UTC)

value (mandatory)
  the value in currency of the commodity

Invariant
~~~~~~~~~

 - the value is expressed as numerator / denominator. The denominator of the value should be
   the same as the fraction of the currency.

Questions
~~~~~~~~~

None


Secondary Objects
=================

