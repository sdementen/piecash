piecash
=======

.. image:: https://travis-ci.org/sdementen/piecash.svg?branch=master
    :target: https://travis-ci.org/sdementen/piecash

piecash offers a pythonic interface to GnuCash documents stored through the SQL backend (sqlite, postgres).

A simple example:

.. code:: python

    from piecash import open_book

    # open a book and print all transactions to screen
    with open_book("test_cur.gnucash") as s:
        for tr in s.transactions:
            print("Transaction : {}".format(tr.description))
            for i, sp in enumerate(tr.splits):
                direction = "increased" if sp.value > 0 else "decreased"
                print("\t{} : '{}' is {} by {}".format(i,
                                                       sp.account.fullname,
                                                       direction,
                                                       sp.value))

    from piecash import create_book, Account
    # create a new account
    with create_book("my_new_book.gnucash") as s:
        acc = Account(name="Income", parent=s.book.root_account, account_type="INCOME")
        s.save()

The project documentation is available on http://piecash.readthedocs.org/en/latest/.
