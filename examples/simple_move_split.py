import random

from piecash import create_book, Account, Transaction, Split

# create new book
with create_book() as s:
    ra = s.book.root_account
    eur = ra.commodity

    # number of accounts
    N = 5
    # number of transactions
    T = 100

    # create accounts
    accounts = [Account("account {}".format(i), "ASSET", eur, parent=ra)
                for i in range(N)]

    # create transactions
    for i, v in enumerate(random.randrange(10) for j in range(T)):
        tx = Transaction(eur,
                         "transaction {}".format(i),
        )
        Split(accounts[random.randrange(N)], value=v, transaction=tx)
        Split(accounts[random.randrange(N)], value=-v, transaction=tx)
    s.save()

    # select two accounts
    acc = accounts[0]
    tacc = accounts[1]
    # move all splits from account acc to account tacc
    for spl in list(acc.splits):
        spl.account = tacc
    s.save()

    # check no more splits in account acc
    assert len(acc.splits) == 0

