# coding=utf-8
from __future__ import unicode_literals
import sys
from piecash import open_book, Transaction, Split
from piecash.kvp import Slot
# from gnucash import Session, Account, Transaction, Split, GncNumeric
# import gnucash
from piecash import create_book, Account, Split, Transaction, Commodity, Price
from datetime import datetime

bookname = "/home/sdementen/Projects/piecash/tests/foozbar.sqlite"
bookname = "/home/sdementen/Projects/piecash/gnucash_books/complex_example_piecash.gnucash"

with create_book(bookname, currency="EUR", keep_foreign_keys=False, overwrite=True) as b:
    # create some accounts
    curr = b.default_currency
    other_curr = b.currencies(mnemonic="USD")
    cdty = Commodity(namespace=u"BEL20", mnemonic=u"GnuCash Inc.", fullname=u"GnuCash Inc. stock")
    asset = Account(name="asset", type="ASSET", commodity=curr, parent=b.root_account)
    foreign_asset = Account(name="foreign asset", type="ASSET", commodity=other_curr, parent=b.root_account)
    stock = Account(name="broker", type="STOCK", commodity=cdty, parent=asset)
    expense = Account(name="exp", type="EXPENSE", commodity=curr, parent=b.root_account)
    income = Account(name="inc", type="INCOME", commodity=curr, parent=b.root_account)

    tr1 = Transaction(post_date=datetime(2015, 10, 21),
                      description="my revenue",
                      currency=curr,
                      splits=[
                          Split(account=asset, value=(1000, 1)),
                          Split(account=income, value=(-1000, 1)),
                      ]
                      )
    tr2 = Transaction(post_date=datetime(2015, 10, 25),
                      description="my expense",
                      currency=curr,
                      splits=[
                          Split(account=asset, value=(-100, 1)),
                          Split(account=expense, value=(20, 1), memo="cost of X"),
                          Split(account=expense, value=(80, 1), memo="cost of Y"),
                      ]
                      )
    tr_stock = Transaction(post_date=datetime(2015, 10, 29),
                           description="my purchase of stock",
                           currency=curr,
                           splits=[
                               Split(account=asset, value=(-200, 1)),
                               Split(account=expense, value=(15, 1), memo="transaction costs"),
                               Split(account=stock, value=(185, 1), quantity=(6, 1), memo="purchase of stock"),
                           ]
                           )
    tr_to_foreign = Transaction(post_date=datetime(2015, 10, 30),
                                description="transfer to foreign asset",
                                currency=curr,
                                splits=[
                                    Split(account=asset, value=(-200, 1)),
                                    Split(account=foreign_asset, value=(200, 1), quantity=(135, 1)),
                                ]
                                )
    tr_from_foreign = Transaction(post_date=datetime(2015, 10, 31),
                                  description="transfer from foreign asset",
                                  currency=other_curr,
                                  splits=[
                                      Split(account=asset, value=(135, 1), quantity=(215, 1)),
                                      Split(account=foreign_asset, value=(-135, 1)),
                                  ]
                                  )
    Price(commodity=cdty,
          currency=other_curr,
          date=datetime(2015, 11, 1),
          value=(123, 100),
          )
    Price(commodity=cdty,
          currency=other_curr,
          date=datetime(2015, 11, 4),
          value=(127, 100),
          )
    Price(commodity=cdty,
          currency=curr,
          date=datetime(2015, 11, 2),
          value=(234, 100),
          )

    b.save()

    print(b.prices_df().to_string())
    print(b.prices)

fdsdfsfds
with open_book(bookname, readonly=True, open_if_lock=True) as b:
    for sp in b.splits:
        print(sp.transaction.post_date, sp.transaction.enter_date, "=>", sp.slots)
    for p in b.prices:
        print(p._value_denom, p._value_num, p.slots)

    print("\n".join(map(str, b.session.query(Slot).all())))
dfdsffd

if False:
    sys.path.append("/home/sdementen/Apps/lib/python2.7/site-packages")


    def lookup_account_by_path(parent, path):
        acc = parent.lookup_by_name(path[0])
        if acc.get_instance() == None:
            raise Exception('Account path {} not found'.format(':'.join(path)))
        if len(path) > 1:
            return lookup_account_by_path(acc, path[1:])
        return acc


    def lookup_account(root, name):
        path = name.split(':')
        return lookup_account_by_path(root, path)


    session = Session("/path/to/file.gnucash")  # , ignore_lock=True)
    # or use URI string: ('mysql://USER:PASSWORD@HOST/DATABASE')

    today = datetime.now()
    book = session.book  # All actions are performed through the book object (or its children)
    root = book.get_root_account()  # Parent of all accounts
    currency = book.get_table().lookup('ISO4217', "USD")
    tx = Transaction(book)
    tx.BeginEdit()
    tx.SetCurrency(currency)
    tx.SetDateEnteredTS(today)
    tx.SetDatePostedTS(today)  # or another datetime object for the transaction's "register date"
    tx.SetDescription("Transaction Description!")
    # tx.SetNum(int_variable) # if you need a transaction number
    amount = 24
    sp1 = Split(book)  # First half of transaction
    sp1.SetParent(tx)
    # The lookup string needs to match your account path exactly.
    sp1.SetAccount(lookup_account(root, "Expenses:Some Expense Account"))
    # amount is an int (no $ or .), so $5.23 becomes amount=523
    sp1.SetValue(GncNumeric(amount, 100))  # Assuming you only have one split
    # For multiple splits, you need to make sure the totals all balance out.
    sp1.SetAmount(GncNumeric(amount, 100))
    sp1.SetMemo("Split Memo!")  # optional

    sp2 = Split(book)  # Need a balancing split
    sp2.SetParent(tx)
    sp2.SetAccount(lookup_account(root, "Assets:Current Assets:Checking"))
    sp2.SetValue(sp1.GetValue().neg())
    sp2.SetAmount(sp1.GetValue().neg())
    sp2.SetMemo("Other Split Memo!")  # optional

    tx.CommitEdit()  # Finish editing transaction
    session.save()
    session.end()

    fdsfsfds

if True:

    with create_book("../gnucash_books/example.gnucash", overwrite=True) as mybook:
        mybook.root_account.children = [
            Account(name="Expenses",
                    type="EXPENSE",
                    commodity=mybook.currencies(mnemonic="USD"),
                    placeholder=True,
                    children=[
                        Account(name="Some Expense Account",
                                type="EXPENSE",
                                commodity=mybook.currencies(mnemonic="USD")),
                    ]),
            Account(name="Assets",
                    type="ASSET",
                    commodity=mybook.currencies(mnemonic="USD"),
                    placeholder=True,
                    children=[
                        Account(name="Current Assets",
                                type="BANK",
                                commodity=mybook.currencies(mnemonic="USD"),
                                placeholder=True,
                                children=[
                                    Account(name="Checking",
                                            type="BANK",
                                            commodity=mybook.currencies(mnemonic="USD"))
                                ]),
                    ]),
        ]
        mybook.save()

    from piecash import open_book, Transaction, Split
    from datetime import datetime
    from decimal import Decimal

    with open_book("../gnucash_books/example.gnucash",
                   open_if_lock=True,
                   readonly=False) as mybook:
        today = datetime.now()
        # retrieve the currency from the book
        USD = mybook.currencies(mnemonic="USD")
        # define the amount as Decimal
        amount = Decimal("25.35")
        # retrieve accounts
        from_account = mybook.accounts(fullname="Expenses:Some Expense Account")
        to_account = mybook.accounts(fullname="Assets:Current Assets:Checking")
        # create the transaction with its two splits
        Transaction(
            post_date=today,
            enter_date=today,
            currency=USD,
            description="Transaction Description!",
            splits=[
                Split(account=to_account,
                      value=amount,
                      memo="Split Memo!"),
                Split(account=from_account,
                      value=-amount,
                      memo="Other Split Memo!"),
            ]
        )
        # save the book
        mybook.save()

    fdsfdsfds

    # create a book (in memory)
    b = open_book("../gnucash_books/book_schtx.gnucash", open_if_lock=True)
    print("============================================")
    df_splits = b.splits_df()

    # df_prices = b.prices_df()
    # assert isinstance(df_prices, pandas.DataFrame)

    fdsfdsfsd
    # get the currency
    eur = b.default_currency

    # create a customer
    c1 = Customer(name="Mickey", currency=eur, address=Address(addr1="Sesame street 1", email="mickey@example.com"))
    # the customer has not yet an ID
    b.add(c1)

    # flush the book
    b.flush()
    sps = b.splits
    print(sps)
    for sp in sps:
        print(sp.value)
    # the customer gets its ID
    print(c1)
    print(b.splits_df())
    fdsfds

    # or create a customer directly in a book (by specifying the book argument)
    c2 = Customer(name="Mickey", currency=eur, address=Address(addr1="Sesame street 1", email="mickey@example.com"),
                  book=b)

    # the customer gets immediately its ID
    c2

    # the counter of the ID is accessible as
    b.counter_customer

    fdsdsffds
from decimal import Decimal
from datetime import datetime
import decimal
import inspect
from sqlalchemy.orm import object_session
from piecash import open_book, Budget, Address
from piecash._common import Recurrence
from piecash import create_book, Account, Transaction, Split, Commodity, Vendor
from piecash.business import Customer

b = create_book("foo.sqlite", currency="EUR", keep_foreign_keys=False, overwrite=True)
c = Customer(book=b, name="foo", currency=b.currencies(mnemonic="EUR"),
             address=Address(name="foo", addr1="a1", addr4="a4", fax="fax", email="email", phone="phoen"))
print(c.addr_addr1)
b.add(Customer(name="john", id=456, currency=b.currencies(mnemonic="EUR")))
b.add(Customer(name="baz", currency=b.currencies(mnemonic="EUR")))
b.add(Customer(name="dsdsbaz", tax_included="YES", currency=b.currencies(mnemonic="EUR")))
b.add(Vendor(name="dsdsbaz", tax_included="YES", currency=b.currencies(mnemonic="EUR")))
b.save()
print(b.customers)
print(b.vendors)
fdsfdsfds
# create some accounts
curr = b.currencies[0]
cdty = Commodity(namespace="échange", mnemonic="ïoà", fullname="Example of unicode déta")
a = Account(name="asset", type="ASSET", commodity=curr, parent=b.root_account)
Account(name="broker", type="STOCK", commodity=cdty, parent=a)
Account(name="exp", type="EXPENSE", commodity=curr, parent=b.root_account)
Account(name="inc", type="INCOME", commodity=curr, parent=b.root_account)
b.flush()
EUR = b.commodities(namespace="CURRENCY")
racc = b.root_account
a = b.accounts(name="asset")
s = b.accounts(name="broker")
b.book.use_trading_accounts = True
tr = Transaction(currency=EUR, description="buy stock", notes="on St-Eugène day",
                 post_date=datetime(2014, 1, 2),
                 enter_date=datetime(2014, 1, 3),
                 splits=[
                     Split(account=a, value=100, memo="mémo asset"),
                     Split(account=s, value=-90, memo="mémo brok"),
                 ])
sp = tr.splits(account=s)
print(sp)
sp.quantity = -15
# adjust balance
Split(account=a, value=-10, memo="missing exp", transaction=tr)
b.flush()
sp.quantity = -14
b.flush()
# print (tr.splits)
sp.quantity = -12
b.flush()
# print (tr.splits)
sp.quantity = -13
b.flush()
sp.quantity = -13
b.flush()
print(tr.splits)

fdsfdsfd
# b1 = create_book("foo.gnucash",overwrite=True,echo=True)
# b1.save()
b1 = open_book("foo.gnucash", readonly=False, echo=True, do_backup=False)
b2 = open_book("foo.gnucash", readonly=False, echo=True, do_backup=False)
# a1 = Account("Acc 1", "ASSET", b1.default_currency, parent=b1.root_account)
# b1.flush()
# b1.save()
a = b2.accounts[0].name
# b2["fooo"] = b2.accounts[0].name
b2.accounts[0].name = "hello you2"
b1.accounts[0].name = "hello me1"
b1.flush()
b1.save()
b2.flush()
b2.save()
print(a, b1.accounts[0].name, b2.accounts[0].name)
fdsffds

# create a book (in memory)
from piecash.ledger import ledger

b = create_book(currency="EUR")
b.control_mode = ["allow-root-subaccounts"]
# get the EUR and create the USD currencies
c1 = b.default_currency
# create two accounts
a1 = Account("Acc 1", "ROOT", c1, parent=b.root_account)
b.add(a1)
print(object_session(a1).book)
print(a1)
print(b.currencies(mnemonic="USD"))
a2 = Account("Acc 2", "ROOT", c1, parent=a1)
print(a2)
b.save()
a1.name = "foo"
b.save()
tr = Transaction(b.default_currency,
                 splits=[
                     Split(account=a1, value=100, quantity=10),
                     Split(account=a2, value=-100, quantity=20)
                 ])
b.save()
# del tr.splits[0]
# b.save()
print(ledger(b))

fdsfds
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
    for tr in s.transactions:  # .get(description="other transfer + expense")
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
