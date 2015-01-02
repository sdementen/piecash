Transactions and Splits
-----------------------

The list of all transactions in the book can be retrieved via the ``transactions`` attribute::

    # all transactions
    print(s.transactions)

    tr = s.transactions[0]

    # accessing attributes of a transaction
    print("Transaction description='{tr.description}'\n"
          "            currency={tr.currency}\n"
          "            post_date={tr.post_date}\n"
          "            enter_date={tr.enter_date}".format(tr=tr))

and the related splits via the ``splits`` attribute of the transaction::

    for sp in tr.splits:
        print("     Split memo='{sp.memo}'\n"
              "           account={sp.account.fullname}\n"
