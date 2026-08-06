Invoices
--------

The list of all invoices in the book can be retrieved via the ``invoices`` attribute:

.. ipython:: python

    from piecash import open_book

    book = open_book(gnucash_books + "invoices.gnucash", open_if_lock=True)

    # all invoices
    for invoice in book.invoices:
        print(invoice)
