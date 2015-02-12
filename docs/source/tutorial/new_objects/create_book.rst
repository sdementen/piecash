Creating a new Book
-------------------

.. py:currentmodule:: piecash.core.book

piecash can create a new GnuCash document (a :class:`Book`) from scratch through the :func:`create_book` function.

To create a in-memory sqlite3 document (useful to test piecash for instance), a simple call is enough:

.. ipython:: python

    import piecash

    book = piecash.create_book()

To create a file-based sqlite3 document:

.. ipython:: python

    book = piecash.create_book("example_file.gnucash")
    # or equivalently (adding the overwrite=True argument to overwrite the file if it already exists)
    book = piecash.create_book(sqlite_file="example_file.gnucash", overwrite=True)
    # or equivalently
    book = piecash.create_book(uri_conn="sqlite:///example_file.gnucash", overwrite=True)

and for a postgres document (needs a pacakge installable via "pip install psycopg2")::

    book = piecash.create_book(uri_conn="postgres://user:passwd@localhost/example_gnucash_db")


.. note::

    Per default, the currency of the document is the euro (EUR) but you can specify any other ISO currency through
    its ISO symbol:

.. ipython:: python

    book = piecash.create_book(sqlite_file="example_file.gnucash",
                            currency="USD",
                            overwrite=True)

If the document already exists, piecash will raise an exception. You can force piecash to overwrite an existing file/database
(i.e. delete it and then recreate it) by passing the overwrite=True argument:

.. ipython:: python

    book = piecash.create_book(sqlite_file="example_file.gnucash", overwrite=True)
