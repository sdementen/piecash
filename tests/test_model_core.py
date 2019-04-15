# -*- coding: utf-8 -*-
import os
import shutil

import pytest

from piecash import Transaction, Commodity, open_book, create_book, Account
from piecash._common import GnucashException
from piecash.core.session import Version, gnclock
from piecash.kvp import Slot
from test_helper import file_template, file_for_test


@pytest.fixture
def session(request):
    s = create_book()
    return s.session


@pytest.fixture
def session_readonly(request):
    shutil.copyfile(str(file_template), str(file_for_test))

    # default session is readonly
    s = open_book(file_for_test)

    @request.addfinalizer
    def close_s():
        s.close()
        file_for_test.unlink()

    return s


@pytest.fixture
def book_readonly_lock(request):
    shutil.copyfile(str(file_template), str(file_for_test))

    # default session is readonly
    book = open_book(file_for_test)

    @request.addfinalizer
    def close_s():
        book.close()
        file_for_test.unlink()

    return book


class TestModelCore_EmptyBook(object):
    def test_accounts(self, session):
        # two accounts in an empty gnucash file
        account_names = session.query(Account.name).all()

        assert set(account_names) == {(u'Template Root',),
                                      (u'Root Account',),
                                      }

    def test_transactions(self, session):
        # no transactions in an empty gnucash file
        transactions = session.query(Transaction).all()
        assert transactions == []

    def test_commodities(self, session):
        # no commodities in an empty gnucash file
        commodities = session.query(Commodity.mnemonic).all()
        assert commodities == [("EUR",)]

    def test_slots(self, session):
        # no slots in an empty gnucash file but the default_currency
        slots = session.query(Slot._name).all()
        assert slots == []

    def test_versions(self, session):
        # confirm versions of tables
        versions = session.query(Version.table_name,
                                 Version.table_version).all()
        assert set(versions) == {(u'Gnucash', 3000000), (u'Gnucash-Resave', 19920),
                                 (u'accounts', 1), (u'books', 1),
                                 (u'budgets', 1), (u'budget_amounts', 1), ('jobs', 1), (u'orders', 1),
                                 (u'taxtables', 2), (u'taxtable_entries', 3), (u'vendors', 1), (u'recurrences', 2),
                                 (u'slots', 4), (u'transactions', 4), (u'splits', 4), (u'lots', 2), (u'entries', 4),
                                 (u'billterms', 2), (u'invoices', 4), (u'commodities', 1), (u'schedxactions', 1),
                                 (u'prices', 3), (u'customers', 2), (u'employees', 2),
                                 }

    def test_readonly_true(self, session_readonly):
        # control exception when adding object to readonly gnucash db
        v = Version(table_name="sample", table_version="other sample")
        sa_session_readonly = session_readonly.session
        sa_session_readonly.add(v)
        with pytest.raises(GnucashException):
            sa_session_readonly.commit()

        # control exception when deleting object to readonly gnucash db
        sa_session_readonly.delete(session_readonly.query(Account).first())
        with pytest.raises(GnucashException):
            sa_session_readonly.commit()

        # control exception when modifying object to readonly gnucash db
        sa_session_readonly.query(Account).first().name = "foo"
        with pytest.raises(GnucashException):
            sa_session_readonly.commit()

    def test_readonly_false(self, session):
        v = Version(table_name="fo", table_version="ok")
        session.add(v)
        assert session.flush() is None

    def test_lock(self, book_readonly_lock):
        # test that lock is not taken in readonly session
        locks = list(book_readonly_lock.session.execute(gnclock.select()))
        assert len(locks) == 0
