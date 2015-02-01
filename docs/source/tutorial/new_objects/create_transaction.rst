Creating a new Transaction
--------------------------

piecash can create new transactions (a :class:`piecash.core.transaction.Transaction`):

.. ipython:: python

    from piecash import create_book, Account, Transaction, Split, GncImbalanceError

    # create a book (in memory)
    s = create_book(currency="EUR")
    # get the EUR and create the USD currencies
    c1 = s.book.default_currency
    c2 = s.book.create_currency_from_ISO("USD")
    # create two accounts
    a1 = Account("Acc 1", "ASSET", c1, parent=s.book.root_account)
    a2 = Account("Acc 2", "ASSET", c2, parent=s.book.root_account)
    # create a transaction from a1 to a2
    tr = Transaction(currency=c1,
                     description="transfer",
                     splits=[
                         Split(account=a1, value=-100),
                         Split(account=a2, value=100, quantity=30)
                     ])
    s.flush()

    # ledger_str() returns a representation of the transaction in the ledger-cli format
    print(tr.ledger_str())

    # change the book to use the "trading accounts" options
    s.book.use_trading_accounts = True
    # add a new transaction identical to the previous
    tr2 = Transaction(currency=c1,
                      description="transfer 2",
                      splits=[
                          Split(account=a1, value=-100),
                          Split(account=a2, value=100, quantity=30)
                      ])
    print(tr2.ledger_str())
    # when flushing, the trading accounts are created
    s.flush()
    print(tr2.ledger_str())

    # trying to create an unbalanced transaction trigger an exception
    # (there is not automatic creation of an imbalance split)
    tr3 = Transaction(currency=c1,
                      description="transfer imb",
                      splits=[
                          Split(account=a1, value=-100),
                          Split(account=a2, value=90, quantity=30)
                      ])
    print(tr3.ledger_str())
    try:
        # the imbalance exception is triggered at flush time
        s.flush()
    except GncImbalanceError:
        print("Indeed, there is an imbalance !")