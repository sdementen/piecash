Accounts
--------

Accessing the accounts (:class:`piecash.core.account.Account`):

.. ipython:: python

    book = open_book(gnucash_books + "simple_sample.gnucash", open_if_lock=True)

    # accessing the root_account
    root = book.root_account
    print(root)

    # accessing the first children account of a book
    acc = root.children[0]
    print(acc)

    # accessing attributes of an account
    print(f"Account name={acc.name}\n"
          f"        commodity={acc.commodity.namespace}/{acc.commodity.mnemonic}\n"
          f"        fullname={acc.fullname}\n"
          f"        type={acc.type}")

    # calculating the balance of the accounts:
    for acc in root.children:
        print(f"Account balance for {acc.name}: {acc.get_balance()} (without sign reversal: {acc.get_balance(natural_sign=False)}")

    # accessing all splits related to an account
    for sp in acc.splits:
        print(f"account <{acc.fullname}> is involved in transaction '{sp.transaction.description}'")

