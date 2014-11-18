# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
# from pytest.mark import parametrize
#
import shutil
import os

import pytest



# parametrize = pytest.mark.parametrize
from piecash import connect_to_gnucash_book
from piecash.model_core.account import Account
from piecash.kvp import Slot
from piecash.model_common import GnucashException
from piecash.model_core import Transaction, Commodity, Version, gnclock


test_folder = os.path.dirname(os.path.realpath(__file__))
file_template = os.path.join(test_folder,"empty_book.gnucash")
file_for_test = os.path.join(test_folder,"empty_book_for_test.gnucash")


@pytest.fixture
def session(request):
    shutil.copyfile(file_template,file_for_test)

    s = connect_to_gnucash_book(file_for_test, readonly=False)

    request.addfinalizer(lambda: os.remove(file_for_test))
    return s

@pytest.fixture
def session_readonly(request):
    shutil.copyfile(file_template,file_for_test)

    # default session is readonly
    s = connect_to_gnucash_book(file_for_test)

    request.addfinalizer(lambda: os.remove(file_for_test))
    return s


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
        # no commodities  in an empty gnucash file
        commodities = session.query(Commodity).all()
        assert commodities == []

    def test_slots(self, session):
        # no slots  in an empty gnucash file
        slots = session.query(Slot).all()
        assert slots == []

    def test_versions(self, session):
        # confirm versions of tables
        versions = session.query(Version.table_name,
                                 Version.table_version).all()
        assert set(versions) == {(u'Gnucash', 2060300), (u'Gnucash-Resave', 19920),
                                 (u'accounts', 1), (u'books', 1),
                                 (u'budgets', 1), (u'budget_amounts', 1), ('jobs', 1), (u'orders', 1),
                                 (u'taxtables', 2), (u'taxtable_entries', 3), (u'vendors', 1), (u'recurrences', 2),
                                 (u'slots', 3), (u'transactions', 3), (u'splits', 4), (u'lots', 2), (u'entries', 3),
                                 (u'billterms', 2), (u'invoices', 3), (u'commodities', 1), (u'schedxactions', 1),
                                 (u'prices', 2), (u'customers', 2), (u'employees', 2),
        }

    def test_readonly_true(self, session_readonly):
        # control exception when adding object to readonly gnucash db
        v = Version(table_name="sample", table_version="other sample")
        session_readonly.add(v)
        with pytest.raises(GnucashException):
            session_readonly.flush()

        # control exception when deleting object to readonly gnucash db
        session_readonly.delete(session_readonly.query(Account).first())
        with pytest.raises(GnucashException):
            session_readonly.flush()

        # control exception when modifying object to readonly gnucash db
        session_readonly.query(Account).first().name = "foo"
        with pytest.raises(GnucashException):
            session_readonly.flush()

        # control no exception when not changing the db
        assert session_readonly.flush() is None

    def test_readonly_false(self, session):
        v = Version(table_name="fo", table_version="ok")
        session.add(v)
        assert session.flush() is None

    def test_lock(self, session):
        locks = list(session.bind.execute(gnclock.select()))
        assert len(locks) == 0


class TestModelCore_CreateObjects(object):
    def test_accounts(self, session):
        # two accounts in an empty gnucash file
        # Account(account_type=)
        account_names = session.query(Account.name).all()

        assert set(account_names) == {(u'Template Root',),
                                      (u'Root Account',),
        }

    def test_transactions(self, session):
        # no transactions in an empty gnucash file
        transactions = session.query(Transaction).all()
        assert transactions == []

    def test_commodities(self, session):
        # no commodities  in an empty gnucash file
        commodities = session.query(Commodity).all()
        assert commodities == []

    def test_slots(self, session):
        # no slots  in an empty gnucash file
        slots = session.query(Slot).all()
        assert slots == []

    def test_versions(self, session):
        # confirm versions of tables
        versions = session.query(Version.table_name,
                                 Version.table_version).all()
        assert set(versions) == {(u'Gnucash', 2060300), (u'Gnucash-Resave', 19920),
                                 (u'accounts', 1), (u'books', 1),
                                 (u'budgets', 1), (u'budget_amounts', 1), ('jobs', 1), (u'orders', 1),
                                 (u'taxtables', 2), (u'taxtable_entries', 3), (u'vendors', 1), (u'recurrences', 2),
                                 (u'slots', 3), (u'transactions', 3), (u'splits', 4), (u'lots', 2), (u'entries', 3),
                                 (u'billterms', 2), (u'invoices', 3), (u'commodities', 1), (u'schedxactions', 1),
                                 (u'prices', 2), (u'customers', 2), (u'employees', 2),
        }