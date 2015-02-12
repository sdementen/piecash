from __future__ import print_function
from decimal import Decimal
import datetime
import decimal
import inspect

from piecash import open_book, Budget
from piecash._common import Recurrence
from piecash import create_book, Account, Transaction, Split





# create a book (in memory)
from piecash.core import factories

s = create_book(currency="EUR")
# get the EUR and create the USD currencies
c1 = s.book.default_currency
c2 = factories.create_currency_from_ISO("USD")
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
tr.ledger_str()

# change the book to use the "trading accounts" options
s.book.use_trading_accounts = True
# add a new transaction identical to the previous
tr2 = Transaction(currency=c1,
                  description="transfer 2",
                  splits=[
                      Split(account=a1, value=-100),
                      Split(account=a2, value=100, quantity=30)
                  ])
tr2.ledger_str()
# when flushing, the trading accounts are created
s.flush()
tr2.ledger_str()

# trying to create an unbalanced transaction trigger an exception
# (there is not automatic creation of an imbalance split)
tr3 = Transaction(currency=c1,
                  description="transfer imb",
                  splits=[
                      Split(account=a1, value=-100),
                      Split(account=a2, value=100, quantity=30)
                  ])
print(tr3.ledger_str())
s.flush()

fdsfdsfds
if True:
    from piecash import create_book, Account

    with create_book(currency="EUR") as s:
        # retrieve the default currency
        EUR = s.commodities.get(mnemonic="EUR")

        # creating a placeholder account
        acc = Account(name="My account",
                      type="ASSET",
                      parent=s.book.root_account,
                      commodity=EUR,
                      placeholder=True, )

        # creating a detailed sub-account
        subacc = Account(name="My sub account",
                         type="BANK",
                         parent=acc,
                         commodity=EUR,
                         commodity_scu=1000,
                         description="my bank account",
                         code="FR013334...", )
        print(acc)
        s.save()
dfds

from piecash import create_book, Commodity

# create a book (in memory) with some currency
s = create_book(currency="EUR")

print(s.commodities)
print(s, s.book, s.book.gnc_session)

# creating a new ISO currency (if not already available in s.commodities)
USD = s.book.create_currency_from_ISO("USD")
print(USD)

# create a commodity
apple = s.book.create_stock_from_symbol("AAPL")
print(apple)

XBT = Commodity(namespace="CURRENCY", mnemonic="XBT", fullname="Bitcoin", fraction=1000000)
print(XBT)
cxwcxwcxw
# with create_book("empty.gnucash", overwrite=True) as s:
# print(list(s.book.iteritems()))

# with open_book("test_bitcoin_piecash.gnucash", readonly=False, open_if_lock=True, backup=False) as s:
# for tr in s.transactions:
# print(tr.ledger_str())
# with create_book("super_empty_piecash.gnucash") as s:
# pass
# dffdsfds


with open_book("super_empty_piecash.gnucash", readonly=False, open_if_lock=True, backup=False) as s:
    print(s.book.root_account.commodity)
    print(s.commodities)
    fdfdsfds
    sa = s.session
    sql = sa.query(Split.value).filter_by(value=100)
    print(sql)
    print(sql.all())
    # print(list(sa.execute("select * from splits")))

dsdsqdsq
#
with open_book("test_bitcoin_piecash.gnucash", readonly=False, open_if_lock=True, backup=False) as s:
    # print(s.book.use_trading_accounts)
    # print(s.book.RO_threshold_day)
    # s.book.use_split_action_field=True
    # print(list(s.book.iteritems()))
    # s.book.RO_threshold_day=0
    # s.book.use_trading_accounts=not s.book.use_trading_accounts
    # print(s.book.use_trading_accounts)
    # print(list(s.book.iteritems()))
    # s.book.RO_threshold_day=12
    # s.book.use_trading_accounts=not s.book.use_trading_accounts
    # print(s.book.use_trading_accounts)
    # print(list(s.book.iteritems()))
    # fdfdsfds
    s.book.use_trading_accounts = True

    # mtr = s.transactions(description="weird transaction")
    # print(mtr.ledger_str())
    # print(mtr.calculate_imbalances())
    # fdsfds

    for tr in s.transactions:
        if tr.description == "weird transaction":
            print(tr.ledger_str())
            tr.splits = [sp for sp in tr.splits if sp.account.type != "TRADING"]

        before = tr.ledger_str()
        if any(tr.calculate_imbalances()[1]):
            print(before)
            tr.normalize_trading_accounts()
            print(tr.ledger_str())

    s.save()
fdsfdsfds

with create_book("test_bitcoin.gnucash", overwrite=True) as s:
    root = s.book.root_account
    bitcoin = Commodity("CURRENCY", "XBT", "Bitcoin", 1000000)
    Account("My bitcoin account", "BANK", bitcoin, parent=root)
    s.save()
fdsfds

with open_book("../gnucash_books/default_book.gnucash") as s:
    # accessing the book object from the session
    book = s.book

    # accessing root accounts
    root = book.root_account

    # accessing children accounts of root
    r = s.book.root_account.children(name="Assets").children[0]
    for acc in s.book.root_account.children(name="Assets").children[0].children:
        print(acc)

    print(inspect.getmro(Budget))
    print(inspect.getmro(Recurrence))
    b = Budget(name=lambda x: x, foo="3")
    b = Budget(name=lambda x: x, foo="3")
    fdsd
    print(b)
fdsfds

with create_book() as s:
    # retrieve list of slots
    print(s.book.slots)

    # set slots
    s.book["myintkey"] = 3
    s.book["mystrkey"] = "hello"
    s.book["myboolkey"] = True
    s.book["mydatekey"] = datetime.datetime.today().date()
    s.book["mydatetimekey"] = datetime.datetime.today()
    s.book["mynumerickey"] = decimal.Decimal("12.34567")
    s.book["account"] = s.book.root_account

    # iterate over all slots
    for k, v in s.book.iteritems():
        print("slot={v} has key={k} and value={v.value} of type {t}".format(k=k, v=v, t=type(v.value)))

    # delete a slot
    del s.book["myintkey"]
    # delete all slots
    del s.book[:]

    # create a key/value in a slot frames (and create them if they do not exist)
    s.book["options/Accounts/Use trading accounts"] = "t"
    # access a slot in frame in whatever notations
    s1 = s.book["options/Accounts/Use trading accounts"]
    s2 = s.book["options"]["Accounts/Use trading accounts"]
    s3 = s.book["options/Accounts"]["Use trading accounts"]
    s4 = s.book["options"]["Accounts"]["Use trading accounts"]
    assert s1 == s2 == s3 == s4

dsqdsq
with open_book("/home/sdementen/Desktop/test_sch_txn_sqlite.gnucash", acquire_lock=False, open_if_lock=True) as s:
    print(s.book.root_template.children)
    print(s.commodities)
    for tr in s.transactions:
        print(tr.splits[0].slots)
        print(tr.slots)
    print(s.transactions[0].scheduled_transaction)
    s.transactions[0].scheduled_transaction = None
    # print(s.transactions[0]["from-sched-xaction"])
    s.book["a/n"]
    print(s.accounts.get(name='Checking Account').lots.get(title="Lot 3"))
fdsfdssfd

dsqdsqdsq
with open_book("../gnucash_books/simple_sample.gnucash", acquire_lock=False, open_if_lock=True) as s:
    asset = s.accounts.get(name="Asset")
    expense = s.accounts.get(name="Expense")
    eur = asset.commodity
    tr = Transaction(currency=eur,
                     description="test",
                     splits=[Split(asset, 100), Split(expense, -100)])
    print(tr)
dffdsfsd

from piecash import open_book, create_book, Account, Transaction, Split

# with create_book("all_account_types.gnucash", overwrite=True) as s:
# for actype in ACCOUNT_TYPES:
# if actype=="ROOT":
# continue
#         acc = Account(name=actype, account_type=actype, parent=s.book.root_account, commodity=s.book.root_account.commodity)
#     s.save()

with open_book("simple_sample.gnucash", acquire_lock=False, open_if_lock=True) as s:
    asset = s.accounts.get(name="Asset")
    expense = s.accounts.get(name="Expense")
    eur = asset.commodity
    tr = Transaction(currency=eur,
                     description="test",
                     splits=[Split(asset, 100), Split(expense, -100)])
    print(tr)
    fdsdf
    for tr in s.transactions:
        for sp in tr.splits:
            sp.account = asset

    fdsfsdfd

    for tr in s.transactions:
        print(tr)
        for sp in tr.splits:
            print("\t", sp)

    for acc in s.accounts:
        if acc.commodity:
            print(acc.commodity.base_currency)
            bal = acc.get_balance()
            print("{} : {} {}".format(acc.fullname, bal, acc.commodity.mnemonic))

fsdsfsd


# with create_book("test_simple_transaction.gnucash",overwrite=True) as s:
with create_book(currency="EUR") as s:
    EUR = s.commodities.get(mnemonic="EUR")
    acc1 = Account(name="acc1",
                   commodity=EUR,
                   parent=s.book.root_account,
                   account_type="BANK")
    acc2 = Account(name="acc2",
                   commodity=EUR,
                   parent=s.book.root_account,
                   account_type="BANK",
                   commodity_scu=10)
    s.session.flush()

    tr = Transaction(currency=EUR,
                     description="foo",
                     splits=[
                         Split(value=Decimal("1.2345"),
                               account=acc1),
                         Split(value=Decimal("-1.2345"),
                               account=acc2),
                     ])
    s.session.flush()

    print([(sp._quantity_denom, sp._value_denom) for sp in tr.splits])
    print(s.session.query(Account.commodity).all())
    print(tr.slots)
    tr.post_date = datetime.datetime.now()
    print(tr.slots)
    tr.post_date = None
    print(tr.slots)
    print(acc2.slots)
    acc2.placeholder = 1
    print(acc2.slots)
    acc2.placeholder = 0
    print(acc2.slots)
    s.save()
    # del tr.splits[-1]
    # print tr.get_imbalances()

dsqsdqdqs
#
# with create_book("test.gnucash", keep_foreign_keys=False, overwrite=True) as s:
# EUR = Commodity.create_from_ISO("EUR")
# tr = Transaction(currency=EUR,description="first")
#     sp = Split(transaction=tr, account=s.book.root_account, value=(100,1), quantity=(10,1))
#     tr = Transaction(currency=EUR,description="second")
#     s.save()


# with open_book("trading_accounts.gnucash", readonly=False) as s:
#     for tr in s.transactions:#.get(description="other transfer + expense")
#         print "{}\t{}".format(tr.currency, tr.description)
#         # print tr.get_imbalances()
#         for sp in tr.splits:
#             print "\t[{}] {} / {} for {}".format( sp.account.commodity,sp.value, sp.quantity,sp.account)
#     # tr1 = s.transactions.get(description="first")
#     # tr2 = s.transactions[1]
#     tr2 = s.transactions.get(description="cross CAD to USD transfer (initiated from USD account)")
#     sp = s.transactions.get(description="cross CAD to USD transfer").splits[0]
#     # sp = s.transactions[0].splits[0]
#     print "o"*100
#     # print sp
#     print "o"*100
#     sp.transaction = tr2
#     s.session.flush()
# fdfdsfsd

with open_book("trading_accounts.gnucash", readonly=False, open_if_lock=True, acquire_lock=True) as s:
    for tr in s.transactions:  #.get(description="other transfer + expense")
        print("{}\t{}".format(tr.currency, tr.description))
        # print tr.get_imbalances()
        for sp in tr.splits:
            print("\t[{}] {} / {} for {}".format(sp.account.commodity, sp.value, sp.quantity, sp.account))
    # sp.memo = "foo"
    # tr.description = "foo"
    # s.session.flush()

    tr = s.transactions.get(description="cross CAD to USD transfer (initiated from USD account)")
    sp = s.transactions.get(description="cross CAD to USD transfer").splits[0]
    # sp.transaction = tr
    tr.description = "foo"
    # tr.currency = s.commodities[-1]
    # print "foooooooooooooooooooooooooooooooo"
    # print sp.transaction, s.transactions.get(description="cross CAD to USD transfer").splits[1].transaction

    acc = s.accounts[0]
    assert isinstance(acc, Account)
    acc.commodity_scu = 1

    s.session.flush()
    Transaction(currency=s.commodities.get(mnemonic="EUR"),
                description="foo",
                splits=[
                    Split(value=Decimal("1.2345"),
                          account=s.accounts[0]),
                    Split(value=Decimal("1.2345"),
                          account=s.accounts[1]),
                ])
    s.session.flush()
    # del tr.splits[-1]
    # print tr.get_imbalances()
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
print(t.splits)
imb = t.get_imbalances()
print(imb)
t.add_imbalance_splits()
s.save()
# print s.session.query(Split).filter(Split.value_magic>=1.0).all()
ffdsfdd

# print t.splits[0].value_gnc, t.splits[0].value_denom, t.splits[0].value_num

print(s.book.root_account.children.append(Account(name="rool", account_type="ASSET", placeholder=False, commodity=EUR)))
s.save()
print(s.transactions.get)
print(s.accounts.get)
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
    s1.session.add(p)
    print(p.value)
    print(p.value_denom)
    print(p.value_num)

    with b1:
        print(get_active_session())
        with b2:
            print(get_active_session())
        print(get_active_session())

    with b1:
        acc = Account(name="foo")
    print(s1.session.new)
