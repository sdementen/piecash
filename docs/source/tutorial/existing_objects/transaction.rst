Transactions and Splits
-----------------------

The list of all transactions in the book can be retrieved via the ``transactions`` attribute:

.. ipython:: python

    from piecash import open_book

    book = open_book(gnucash_books + "book_schtx.gnucash", open_if_lock=True)

    # all transactions (including transactions part of a scheduled transaction description)
    for tr in book.transactions:
        print(tr)

    # selecting first transaction generated from a scheduled transaction
    tr = [ tr for tr in book.transactions if tr.scheduled_transaction ][0]


For a given transaction, the following attributes are accessible:

.. ipython:: python

    # accessing attributes of a transaction
    print("Transaction description='{tr.description}'\n"
          "            currency={tr.currency}\n"
          "            post_date={tr.post_date}\n"
          "            enter_date={tr.enter_date}".format(tr=tr))

    # accessing the splits of the transaction
    tr.splits

    # identifying which split is a credit or a debit
    for sp in tr.splits:
        split_type = "credit" if sp.is_credit else "debit"
        print(f"{sp} is a {split_type}")

    # accessing the scheduled transaction
    [ sp for sp in tr.scheduled_transaction.template_account.splits]

    # closing the book
    book.close()
