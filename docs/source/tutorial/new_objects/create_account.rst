Creating a new Account
----------------------

piecash can create new accounts (a :class:`piecash.core.account.Account`):

.. ipython:: python

    from piecash import create_book, Account

    book = create_book(currency="EUR")

    # retrieve the default currency
    EUR = book.commodities.get(mnemonic="EUR")

    # creating a placeholder account
    acc = Account(name="My account",
                  type="ASSET",
                  parent=book.root_account,
                  commodity=EUR,
                  placeholder=True,)

    # creating a detailed sub-account
    subacc = Account(name="My sub account",
                     type="BANK",
                     parent=acc,
                     commodity=EUR,
                     commodity_scu=1000,
                     description="my bank account",
                     code="FR013334...",)

    book.save()

    book.accounts


