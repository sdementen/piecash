Accounts
--------

Accessing the accounts (:class:`piecash.core.account.Account`)::

    from piecash import open_book

    with open_book("gnucash_books/simple_sample.gnucash") as book:
        # accessing the root_account
        root = book.root_account
        print(root)

        # accessing the first children account of a book
        acc = root.children[0]
        print(acc)

        # accessing attributes of an account
        print("Account name={acc.name}\n"
              "        commodity={acc.commodity.namespace}/{acc.commodity.mnemonic}\n"
              "        fullname={acc.fullname}\n"
              "        type={acc.type}".format(acc=acc))

        # accessing all splits related to an account
        for sp in acc.splits:
            print("account <{}> is involved in transaction '{}'".format(acc.fullname, sp.transaction.description))

