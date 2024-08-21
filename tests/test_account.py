# -*- coding: latin-1 -*-
import pytest
from datetime import datetime, date
from piecash import Account, Commodity, Lot, Split, Transaction
from piecash.kvp import Slot
from test_helper import (
    db_sqlite_uri,
    db_sqlite,
    new_book,
    new_book_USD,
    book_uri,
    book_transactions,
)

# dummy line to avoid removing unused symbols

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri


class TestAccount_create_account(object):
    def test_create_parentless_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create an account without parent that is not ROOT
        acc = Account(name="test account", type="ASSET", commodity=EUR)
        new_book.add(acc)
        with pytest.raises(ValueError):
            new_book.validate()
        new_book.cancel()

        # create an account without parent that is ROOT but with wrong name
        acc = Account(name="test account", type="ROOT", commodity=EUR)
        new_book.add(acc)
        with pytest.raises(ValueError):
            new_book.validate()
        new_book.cancel()

        # create an account without parent that is ROOT with correct name
        acc = Account(name="Root Account", type="ROOT", commodity=EUR)
        new_book.add(acc)
        new_book.flush()

        assert len(new_book.accounts) == 0
        root_accs = new_book.query(Account).all()
        assert len(root_accs) == 3

    def test_create_samenameandparent_accounts(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account
        acc1 = Account(name="test account", type="ASSET", commodity=EUR, parent=racc)
        acc2 = Account(name="test account", type="ASSET", commodity=EUR, parent=racc)
        with pytest.raises(ValueError):
            new_book.validate()

    def test_create_samenameanddifferentparent_accounts(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create 2 accounts with same name but different parent
        acc1 = Account(name="test account", type="ASSET", commodity=EUR, parent=racc)
        acc2 = Account(name="test account", type="ASSET", commodity=EUR, parent=acc1)
        new_book.flush()
        assert acc1.fullname == "test account"
        assert acc2.fullname == "test account:test account"

    def test_create_standardasset_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create normal account
        acc = Account(name="test account", type="ASSET", commodity=EUR, parent=racc)
        new_book.flush()
        assert len(new_book.accounts) == 1
        assert acc.non_std_scu == 0
        assert acc.commodity_scu == EUR.fraction
        assert acc.get_balance() == 0
        assert acc.get_balance(at_date=date.today()) == 0
        assert acc.sign == 1
        assert not acc.is_template

    def test_account_balance_on_date(self, book_transactions):
        a = book_transactions.accounts(name="asset")
        assert a.get_balance(at_date=date(2015, 10, 21)) == 1000
        assert a.get_balance(at_date=date(2015, 10, 25)) == 900

    def test_create_standardliability_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create normal account
        acc = Account(name="test account", type="LIABILITY", commodity=EUR, parent=racc)
        new_book.flush()
        assert len(new_book.accounts) == 1
        assert acc.non_std_scu == 0
        assert acc.commodity_scu == EUR.fraction
        assert acc.get_balance() == 0
        assert acc.sign == -1
        assert not acc.is_template

    def test_create_unknowntype_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create account with unknown type
        with pytest.raises(ValueError):
            acc = Account(name="test account", type="FOO", commodity=EUR, parent=racc)
            new_book.validate()

    def test_create_nobook_account(self, new_book):
        USD = Commodity(namespace="FOO", mnemonic="BAZ", fullname="cuz")

        # create account with no book attachable to it
        with pytest.raises(ValueError):
            acc = Account(name="test account", type="ASSET", commodity=USD)
            new_book.flush()

    def test_create_children_accounts(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create account with unknown type
        acc = Account(
            name="test account",
            type="ASSET",
            commodity=EUR,
            parent=racc,
            children=[Account(name="test sub-account", type="ASSET", commodity=EUR)],
        )
        new_book.flush()
        assert len(acc.children) == 1

    def test_create_unicodename_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create normal account
        acc = Account(name=u"inou� �trange", type="ASSET", commodity=EUR, parent=racc)
        new_book.flush()
        assert len(new_book.accounts) == 1
        assert len(repr(acc)) >= 2

    def test_create_root_subaccount(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create root account should raise an exception
        acc = Account(name="subroot accout", type="ROOT", commodity=EUR, parent=racc)
        with pytest.raises(ValueError):
            new_book.validate()

        # except if we add the control_mode 'allow-root-subaccounts' to the book
        new_book.control_mode.append("allow-root-subaccounts")
        new_book.validate()

        assert len(new_book.accounts) == 1


class TestAccount_features(object):
    def test_sign_accounts(self, new_book):
        EUR = new_book.commodities[0]
        neg = "EQUITY,PAYABLE,LIABILITY,CREDIT,INCOME".split(",")
        pos = "STOCK,MUTUAL,EXPENSE,BANK,TRADING,CASH,ASSET,RECEIVABLE".split(",")
        all = neg + pos
        for acc in all:
            assert Account(name=acc, type=acc, commodity=EUR).sign == (
                1 if acc in pos else -1
            )

    def test_scu(self, new_book):
        EUR = new_book.commodities[0]
        acc = Account(name="test", type="ASSET", commodity=EUR)
        assert acc.commodity_scu == EUR.fraction
        assert not acc.non_std_scu
        acc.commodity_scu = 100
        assert acc.non_std_scu
        acc.commodity_scu = None
        assert acc.commodity_scu == EUR.fraction
        assert not acc.non_std_scu

    def test_scrub(self, new_book):
        EUR = new_book.commodities[0]

        # Create a sample stock
        xyz = Commodity(namespace="EUREX", mnemonic="XYZ",
                                 fullname="XYZ Inc.", fraction=10000)
        new_book.add(xyz)

        # Create accounts
        checking_account = Account(name="Checking account",
                                   type="ASSET",
                                   parent=new_book.root_account,
                                   commodity=EUR,
                                   placeholder=False,)
        xyz_account = Account(name="XYZ account",
                              type="STOCK",
                                     parent=new_book.root_account,
                                     commodity=xyz,
                                     placeholder=False,)

        # Create some transactions buying and selling xyz
        tr1 = Transaction(currency=EUR,
                    post_date = date(2024, 1, 1),
                    description="Buy 10 XYZ@11",
                    splits=[
                        Split(account=checking_account, value=-110),
                        Split(account=xyz_account, value=110, quantity=10)
                    ])
        tr2 = Transaction(currency=EUR,
                    post_date = date(2024, 2, 1),
                    description="Buy 12 XYZ@13",
                    splits=[
                        Split(account=checking_account, value=-156),
                        Split(account=xyz_account, value=156, quantity=12)
                    ])
        tr3 = Transaction(currency=EUR,
                    post_date = date(2024, 3, 1),
                    description="Buy 13 XYZ@14",
                    splits=[
                        Split(account=checking_account, value=-182),
                        Split(account=xyz_account, value=182, quantity=13)
                    ])
        tr4 = Transaction(currency=EUR,
                    post_date = date(2024, 4, 1),
                    description="Sell 25 XYZ@12",
                    splits=[
                        Split(account=checking_account, value=300),
                        Split(account=xyz_account, value=-300, quantity=-25)
                    ])
        tr5 = Transaction(currency=EUR,
                    post_date = date(2024, 5, 1),
                    description="Sell 5 XYZ@13",
                    splits=[
                        Split(account=checking_account, value=65),
                        Split(account=xyz_account, value=-65, quantity=-5)
                    ])

        new_book.flush()
        new_book.validate()

        # Scrub xyz_account
        xyz_account.scrub_account()

        # Scrub xyz_account again, checking nothing gets added twice.
        xyz_account.scrub_account()

        assert len(new_book.accounts) == 2 + 1      # created orphan-gains account
        assert len(new_book.prices) == 5            # one for each transaction
        assert len(new_book.transactions) == 9      # 5 above, 4 created for realised gains/losses
        assert len(new_book.splits) == 20           # 5 transactions above * 2 = 10
                                                    # 4 transactions w/realised gains * 2 = 8
                                                    # 1 split needed sub-splitting twice -> +2 = 20
        lots = new_book.session.query(Lot).all()
        assert len(lots) == 3                       # 1 for each buy-transaction
        assert len(xyz_account.lots) == 3           # all lots should be associated with xyz_account
        assert len(new_book.session.query(Slot).all()) == 37    # start with 5 (date posted for transactions above)
                                                                # and 32 created during scrubbing
        # Check the lots' quantities and values
        quantities = [0, 0, 5]
        values = [10, -12, -11]
        for i, lot in enumerate(lots):
            assert lot.quantity == quantities[i]
            assert sum(split.value for split in lot.splits if split.quantity == 0) == values[i]

        # Checks relationships
        original_transactions = [tr1, tr2, tr3, tr4, tr5]
        new_transactions = [tr for tr in new_book.transactions if tr not in original_transactions]
        realisation_gains = [split for split in tr4.splits + tr5.splits if split.quantity < 0]
        realised_gains_splits = []
        for tr in new_transactions:
            realised_gains_splits.extend([split for split in tr.splits if split.quantity == 0])

        for idx, split in enumerate(realisation_gains):
            assert "gains-split" in split
            assert split["gains-split"].value == realised_gains_splits[idx]
            assert realised_gains_splits[idx]["gains-source"].value == split

            if idx < 3:
                assert split["lot-split/date"].value.date() == datetime.today().date()
                assert split["lot-split/peer_guid"].value in tr4.splits

        assert xyz_account["lot-mgmt/gains-acct/CURRENCY::EUR"].value == new_book.accounts(name="Orphaned Gains-EUR")
        assert xyz_account["lot-mgmt/next-id"].value == 3

# this works
        import json
        from sqlalchemy.schema import MetaData
        meta = MetaData()
        meta.reflect(bind=new_book.session.bind)  # http://docs.sqlalchemy.org/en/rel_0_9/core/reflection.html
        result = {}

        for table in meta.sorted_tables:
            if table.name == "slots":
#                result[table.name] = [dict(row) for row in new_book.session.execute(table.select())]
#                result[table.name] = [row for row in new_book.session.execute(table.select())]

                for row in new_book.session.execute(table.select()):
                    print(row)
#ok        print(json.dumps(result))
# end this works


        assert 1 == 2
