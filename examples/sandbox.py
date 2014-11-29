from decimal import Decimal
import datetime

from piecash import Commodity, Price, get_active_session, create_book, Account, Transaction, open_book



# s = create_book(postgres_conn="postgres://user:passwd@localhost/gnucash_book1", overwrite=True)
# s = create_book("test.gnucash",overwrite=True)
s = create_book()
EUR = Commodity.create_from_ISO("EUR")
acc1 = Account(name="foo", parent=s.book.root_account, account_type="ASSET", placeholder=True, commodity=EUR)
acc2 = Account(name="baz", parent=s.book.root_account, account_type="ASSET", placeholder=False, commodity=EUR)
Transaction.single_transaction(datetime.datetime.now(),
                               datetime.datetime.now(),
                               "first transaction",
                               (100,1),
                               acc1,
                               acc2)
print s.book.root_account.children.append(Account(name="rool", account_type="ASSET", placeholder=False, commodity=EUR))
s.save()
print s.transactions.get
print s.accounts.get
s.close()
# end_of_example


with open_book("sample1.gnucash", readonly=False, open_if_lock=True) as s1, open_book("sample2.gnucash") as s2:
    b1 = s1.book
    # s2 = open_book("sample2.gnucash")
    b2 = s2.book

    eur = s1.get(Commodity, mnemonic="EUR")

    b1.root_account["notes"] = "Hello world!"

    p = Price(currency=eur,
              commodity=eur,
              value=Decimal("4234.342"),
    )
    s1.sa_session.add(p)
    print p.value
    print p.value_denom
    print p.value_num

    with b1:
        print get_active_session()
        with b2:
            print get_active_session()
        print get_active_session()

    with b1:
        acc = Account(name="foo")
    print s1.sa_session.new
