# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function

import datetime
import os
import shutil
import threading
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy

from piecash import create_book, Account, ACCOUNT_TYPES, open_book, Price
from piecash._common import GnucashException
from piecash.core.account import _is_parent_child_types_consistent, root_types
from piecash.kvp import Slot
from test_helper import (
    file_template_full,
    file_for_test_full,
    run_file,
    file_ghost_kvp_scheduled_transaction,
    file_ghost_kvp_scheduled_transaction_for_test,
)


@pytest.fixture
def book(request):
    b = create_book()
    return b


@pytest.fixture
def realbook_session(request):
    return use_copied_book(request, file_template_full, file_for_test_full)


@pytest.fixture
def realbook_session_multithread(request):
    return use_copied_book(request, file_template_full, file_for_test_full, check_same_thread=False)


@pytest.fixture
def ghost_kvp_scheduled_transaction_session(request):
    return use_copied_book(request, file_ghost_kvp_scheduled_transaction, file_ghost_kvp_scheduled_transaction_for_test)


def use_copied_book(request, template_filename, test_filename, check_same_thread=True):
    shutil.copy(str(template_filename), str(test_filename))

    # default book is readonly
    s = open_book(test_filename, check_same_thread=check_same_thread)

    @request.addfinalizer
    def finalizer():
        s.close()
        test_filename.unlink()

    return s


class TestIntegration_ExampleScripts(object):
    def test_simple_move_split(self):
        run_file("examples/simple_move_split.py")

    def test_simple_book(self):
        run_file("examples/simple_book.py")

    def test_filtered_transaction_report(self):
        run_file("examples/filtered_transaction_report.py")

    def test_simple_session(self):
        run_file("examples/simple_session.py")

    def test_simple_test(self):
        run_file("examples/simple_test.py")

    def test_simple_sqlite_create(self):
        run_file("examples/simple_sqlite_create.py")


class TestIntegration_EmptyBook(object):
    def test_slots_create_access(self, book):
        kv = {
            "vint": 3,
            "vfl": 2.34,
            "vstr": "hello",
            "vdate": datetime.datetime.now().date(),
            "vtime": datetime.datetime.now(),
            "vnum": Decimal("4.53"),
            "vlist": ["stri", 4, dict(foo=23)],
            "vdct": {"spl": 2.3, "vfr": {"vfr2": {"foo": 33, "baz": "hello"}, "coo": Decimal("4.53")}},
        }
        for k, v in kv.items():
            book[k] = v
        book.save()

        for k, v in kv.items():
            assert k in book
            if isinstance(v, datetime.datetime):
                # check string format as the date in piecash is localized
                assert "{:%Y%m%d%H%M%S}".format(book[k].value) == "{:%Y%m%d%H%M%S}".format(v)
            else:
                assert book[k].value == v

    def test_slots_strings_access(self, book):
        b = book

        b["a/b/c/d/e"] = 1
        book.book.flush()
        assert b["a"]["b"]["c"]["d"]["e"].value == 1

        b["a/b/c"] = {"d": {"t": "ok"}}

        b["a/b/c/d/f"] = "2"
        book.book.flush()
        assert len(b["a"]["b"]["c"]["d"].slots) == 2

        b["a/b/c/d/f"] = "5"
        assert b["a"]["b/c"]["d"]["f"].value == "5"

        for k, v in b["a/b/c/d"].iteritems():
            assert k == "f" or k == "t"
        print(b.slots)
        assert b["a/b/c/d"].get("t", "hello") == "ok"
        assert b["a/b/c/d"].get("not there", "hello") == "hello"

        del b["a/b/c/d/t"]
        assert repr(b["a"]) == "<SlotFrame a={'b': {'c': {'d': {'f': '5'}}}}>"

        with pytest.raises(TypeError):
            b["a/b/c/d/f"] = 4
        with pytest.raises(TypeError):
            b["a/b/c"] = True

        book.flush()
        assert {n for (n,) in book.session.query(Slot._name)} == {"a", "a/b", "a/b/c", "a/b/c/d", "a/b/c/d/f"}

        # delete some elements
        del b["a"]["b"][:]
        book.flush()
        assert {n for (n,) in book.session.query(Slot._name)} == {"a", "a/b"}

        book.flush()
        assert len(b["a"].slots) == 1
        assert len(b["a/b"].slots) == 0

        with pytest.raises(KeyError):
            b["a/b/c"]

        del b["a"]["b"]
        book.session.flush()
        assert len(b["a"].slots) == 0

        with pytest.raises(TypeError):
            b["a"] = b

        with pytest.raises(KeyError):
            del b["a/n"]

        del b[:]
        book.session.flush()
        assert {n for (n,) in book.session.query(Slot._name)} == set([])

    def test_smart_slots(self, book):
        book["account"] = book.root_account
        assert book.slots[0].guid_val == book.root_account.guid
        assert book["account"].value == book.root_account

        with pytest.raises(ValueError):
            book["weird"] = lambda x: x

        with pytest.raises(ValueError):
            book["unknown_guid"] = book.root_account

    def test_empty_gnucash_file(self, book):
        accs = book.accounts

        assert len(accs) == 0
        assert all(acc.parent is None for acc in accs)
        assert all(acc.type == "ROOT" for acc in accs)

    def test_is_parent_child_types_consistent(self):
        combi_OK = [("ROOT", "BANK"), (None, "ROOT"), ("ROOT", "EQUITY"), ("ROOT", "ASSET"), ("ROOT", "EXPENSE")]

        combi_not_OK = [
            ("ROOT", "ROOT"),
            ("ROOT", None),
            (None, "ASSET"),
            ("ASSET", "EQUITY"),
            ("EQUITY", "ASSET"),
            ("ASSET", "INCOME"),
            ("EXPENSE", "ASSET"),
        ]

        for p, c in combi_OK:
            assert _is_parent_child_types_consistent(p, c, [])

        for p, c in combi_not_OK:
            assert not _is_parent_child_types_consistent(p, c, [])

    def test_add_account_compatibility(self, book):
        # test compatibility between child account and parent account
        for acc_type1 in ACCOUNT_TYPES - root_types:
            acc1 = Account(name=acc_type1, type=acc_type1, parent=book.root_account, commodity=None)
            for acc_type2 in ACCOUNT_TYPES:
                if _is_parent_child_types_consistent(acc_type1, acc_type2, []):
                    acc2 = Account(name=acc_type2, type=acc_type2, parent=acc1, commodity=None)

        book.save()

        assert len(book.accounts) == 100

    def test_add_account_incompatible(self, book):
        # test compatibility between child account and parent account
        for acc_type1 in ACCOUNT_TYPES - root_types:
            acc1 = Account(name=acc_type1, type=acc_type1, parent=book.root_account, commodity=None)
        book.save()

        assert len(book.accounts) == 13
        for acc_type1 in ACCOUNT_TYPES - root_types:
            acc1 = book.accounts(name=acc_type1)
            for acc_type2 in ACCOUNT_TYPES:
                if not _is_parent_child_types_consistent(acc_type1, acc_type2, []):
                    acc2 = Account(name=acc_type2, type=acc_type2, parent=acc1, commodity=None)
                    with pytest.raises(ValueError):
                        book.validate()
                    book.cancel()
        book.save()

        assert len(book.accounts) == 13

    def test_add_account_names(self, book):
        # raise ValueError as acc1 and acc2 shares same parents with same name
        acc1 = Account(name="Foo", type="MUTUAL", parent=book.root_account, commodity=None)
        acc2 = Account(name="Foo", type="BANK", parent=book.root_account, commodity=None)
        with pytest.raises(ValueError):
            book.save()
        book.cancel()
        # ok as same name but different parents
        acc3 = Account(name="Fooz", type="BANK", parent=book.root_account, commodity=None)
        acc4 = Account(name="Fooz", type="BANK", parent=acc3, commodity=None)
        book.save()
        # raise ValueError as now acc4 and acc3 shares same parents with same name
        acc4.parent = acc3.parent
        with pytest.raises(ValueError):
            book.save()

    def test_example(self, realbook_session):
        book = realbook_session

        # example 1, print all stock prices in the Book
        # display all prices
        for price in book.query(Price).all():
            print(
                "{}/{} on {} = {} {}".format(
                    price.commodity.namespace,
                    price.commodity.mnemonic,
                    price.date,
                    float(price.value_num) / price.value_denom,
                    price.currency.mnemonic,
                )
            )

        for account in book.accounts:
            print(account)

        # build map between account fullname (e.g. "Assets:Current Assets" and account)
        map_fullname_account = {account.fullname: account for account in book.query(Account).all()}

        # use it to retrieve the current assets account
        print(map_fullname_account)
        acc_cur = map_fullname_account["Assets:Current Assets"]

        # retrieve EUR currency
        EUR = book.commodities.get(mnemonic="EUR")

        # add a new subaccount to this account of type ASSET with currency EUR
        Account(name="new savings account", type="ASSET", parent=acc_cur, commodity=EUR)

        # save changes
        with pytest.raises(GnucashException) as excinfo:
            book.save()


class TestIntegration_GhostKvpScheduledTransaction(object):

    # See PR https://github.com/sdementen/piecash/pull/20
    # The book ghost_kvp_scheduled_transaction.gnucash was created in GnuCash
    # as follows:
    # * Created a scheduled transaction
    # * Used it to create a real transaction
    # * Deleted the original template transaction

    def test_print_transactions(self, ghost_kvp_scheduled_transaction_session):
        book = ghost_kvp_scheduled_transaction_session

        for tr in book.transactions:
            assert tr.scheduled_transaction is None


class TestIntegration_Thread(object):
    def test_exception_due_to_multithread(self, realbook_session):
        book = realbook_session

        class MyThread(threading.Thread):
            def run(self):
                with pytest.raises(sqlalchemy.exc.ProgrammingError):
                    book.transactions

        thr = MyThread()
        thr.start()
        thr.join()

    def test_check_same_thread_False_allow_thread_use(self, realbook_session_multithread):
        book = realbook_session_multithread

        class MyThread(threading.Thread):
            def run(self):
                book.transactions

        thr = MyThread()
        thr.start()
        thr.join()
