from decimal import Decimal
import datetime

from piecash import Commodity, Price, get_active_session, create_book, Account, Transaction, open_book, Split

with open_book("trading_accounts.gnucash", readonly=True, open_if_lock=True) as s:
    for tr in s.transactions:#.get(description="other transfer + expense")
        print "{}\t{}".format(tr.currency, tr.description)
        # print tr.get_imbalances()
        for sp in tr.splits:
            print "\t[{}] {} / {} for {}".format( sp.account.commodity,sp.value, sp.quantity,sp.account)
    del tr.splits[-1]
    print tr.get_imbalances()
fdfsdfds



# s = create_book(postgres_conn="postgres://user:passwd@localhost/gnucash_book1", overwrite=True)
# s = create_book("test.gnucash",overwrite=True)

s = create_book("test.gnucash", overwrite=True)
# s = create_book()
EUR = Commodity.create_from_ISO("EUR")
CAD = Commodity.create_from_ISO("CAD")
USD = Commodity.create_from_ISO("USD")
# EUR.fraction = 100000
acc1 = Account(name="foo EUR", parent=s.book.root_account, account_type="ASSET", placeholder=False, commodity=EUR)
acc2 = Account(name="baz CAD", parent=s.book.root_account, account_type="STOCK", placeholder=False, commodity=CAD)
acc3 = Account(name="baz USD", parent=s.book.root_account, account_type="STOCK", placeholder=False, commodity=USD)
# acc1.commodity_scu = 1000
t = Transaction(description="foo",
                post_date=datetime.datetime.now(),
                enter_date=datetime.datetime.now(),
                currency=EUR)
Split(transaction=t,
      value=-25,
      quantity=-25,
      account=acc1)
Split(transaction=t,
      value=15,
      quantity=10,
      account=acc2)
Split(transaction=t,
      value=11,
      quantity=12,
      account=acc3)
print t.splits
imb = t.get_imbalances()
print imb
t.add_imbalance_splits()
s.save()
# print s.sa_session.query(Split).filter(Split.value_magic>=1.0).all()
ffdsfdd

# print t.splits[0].value_gnc, t.splits[0].value_denom, t.splits[0].value_num

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
