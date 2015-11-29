# -*- coding: latin-1 -*-
import pytest

from piecash import Account, Commodity
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri


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
        assert acc.sign == 1
        assert not acc.is_template

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
            acc = Account(name="test account", type="FOO", commodity=USD)
            new_book.flush()

    def test_create_unicodename_account(self, new_book):
        EUR = new_book.commodities[0]
        racc = new_book.root_account

        # create normal account
        acc = Account(name=u"inouï étrange", type="ASSET", commodity=EUR, parent=racc)
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
            assert Account(name=acc, type=acc, commodity=EUR).sign == (1 if acc in pos else -1)

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