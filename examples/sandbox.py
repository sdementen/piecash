from decimal import Decimal

from sqlalchemy.orm import Session

from piecash import connect_to_gnucash_book, Account, Commodity, Price, get_active_session, create_book


# b = create_book(postgres_conn="postgres://postgres:postgres@localhost/gnucash_fooffffff", overwrite=True)
# b = create_book(postgres_conn="postgresql+pg8000://postgres:postgres@localhost/gnucash_fooffffff", overwrite=True)
# b = create_book("foo5.gnucash",overwrite=True)
b = create_book()
Account(name="foo", parent=b.root_account, account_type="ASSET")
b.cancel()

print b.root_account.children

fdfdsfsd

b1 = connect_to_gnucash_book("sample1.gnucash", readonly=False)
b2 = connect_to_gnucash_book("sample2.gnucash")
s1 = b1.get_session()
s2 = b2.get_session()

with b1:
    # print Commodity.lookup("EUR").get_kvp("ba")
    eur = Commodity.lookup("EUR")

# b1.set_kvp("num", (2554,100))
# print b1.get_kvp("num")
assert isinstance(b1.root_account, Account)
b1.root_account.set_kvp("notes", "Hello world!")
print b1.root_account.get_kvp("notes")
# b1.root_account.del_kvp("notes")
# b1.save()
# print b1.root_account.get_kvp("notes")
# fdsfd

with b1:
    p = Price(currency="EUR",
              commodity='EUR',
              value=Decimal("4234.342"),
    )
s1.add(p)
print p.value
print p.value_denom
print p.value_num

with b1:
    print get_active_session()
    with b2:
        print get_active_session()
    print get_active_session()

assert isinstance(s1, Session)

with b1:
    acc = Account(name="foo")
print s1.new
