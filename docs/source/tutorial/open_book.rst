Opening an existing Book
========================

.. py:currentmodule:: piecash.model_core.session

To open an existing GnuCash document (and get the related :class:`GncSession`), use the :func:`open_book` function::

    import piecash

    # for a sqlite3 document
    s = piecash.open_book("existing_file.gnucash")

    # or through an URI connection string for sqlite3
    s = piecash.open_book(uri_conn="sqlite:///existing_file.gnucash")
    # or for postgres
    s = piecash.open_book(uri_conn="postgres://user:passwd@localhost/existing_gnucash_db")

The documents are open as readonly per default. To allow RW access, specify explicitly readonly=False as::

    s = piecash.open_book("existing_file.gnucash", readonly=False)

Per default, piecash will acquire a lock on the file (as GnuCash does). To avoid acquiring the lock, you can
set the acquire_lock=False argument::

    s = piecash.open_book("existing_file.gnucash", acquire_lock=False)

To force opening the file even through there is a lock on it, use the open_if_lock=True argument::

    s = piecash.open_book("existing_file.gnucash", open_if_lock=True)

