Accessing the book objects
==========================

Once a GnuCash book is opened, it is straightforward to access the different GnuCash objects through the :class:`piecash.core.session.GncSession`::

    from piecash import open_book

    with open_book("gnucash_books/simple_sample.gnucash") as s:
        # accessing the book object
        book = s.book

        # accessing the root_account
        root = s.book.root_account
        print(root)

        # accessing the children accounts of a book
        acc = root.children[0]                  # by index
        acc = root.children.get(name="Asset")   # by filter on some attribute
        print(acc)

        # accessing attributes of an account
        print("Account name={acc.name}\n"
              "        commodity={acc.commodity}\n"
              "        fullname={acc.fullname}\n"
              "        type={acc.account_type}".format(acc=acc))


