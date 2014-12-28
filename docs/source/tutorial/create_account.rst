Creating a new Account
======================

piecash easily create new accounts (a :class:`piecash.core.account.Account`)::

    from piecash import create_book, Account

    with create_book(currency="EUR") as s:
        # retrieve the default currency
        EUR = s.commodities.get(mnemonic="EUR")

        # creating a placeholder account
        acc = Account(name="My account",
                      type="ASSET",
                      parent=s.book.root_account,
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

        s.save()


