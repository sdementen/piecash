Creating a new Book
===================

.. py:currentmodule:: piecash.core.session

piecash can create a new GnuCash document (a :class:`GncSession`) from scratch through the :func:`create_book` function.

To create a in-memory sqlite3 document (useful to test piecash for instance), a simple call is enough::

    import piecash

    s = piecash.create_book()

To create a file-based sqlite3 document::

    s = piecash.create_book("example_file.gnucash")
    # or equivalently
    s = piecash.create_book(sqlite_file="example_file.gnucash")
    # or equivalently
    s = piecash.create_book(uri_conn="sqlite:///example_file.gnucash")

and for a postgres document::

    s = piecash.create_book(uri_conn="postgres://user:passwd@localhost/example_gnucash_db")


.. note:: Specifying the default currency

    Per default, the currency of the document is the euro (EUR) but you can specify any other currency through
    its ISO symbol::

        s = piecash.create_book(sqlite_file="example_file.gnucash", currency="USD")

If the document already exists, piecash will raise an exception. You can force piecash to overwrite an existing file/database
 (i.e. delete it and then recreate it) by passing the overwrite=True argument::

    s = piecash.create_book(sqlite_file="example_file.gnucash")
    s = piecash.create_book(sqlite_file="example_file.gnucash", overwrite=True)

