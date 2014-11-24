# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
# from pytest.mark import parametrize
#
import datetime

import pytest




# parametrize = pytest.mark.parametrize
from piecash import create_book, Account


@pytest.fixture
def session(request):
    s = create_book()
    return s


class TestIntegration_EmptyBook(object):
    def test_create_access_slots(self, session):
        kv = {
            "vint": 3,
            "vfl": 2.34,
            "vstr": "hello",
            "vdate": datetime.datetime.now().date(),
            "vtime": datetime.datetime.now(),
            "vnum": (453, 100),
            "vdct": {
                "spl": 2.3,
                "vfr": {
                    "vfr2": {
                        "foo": 33,
                        "baz": "hello"
                    },
                    "coo": (23, 23)
                },
            }
        }
        for k, v in kv.iteritems():
            session.book[k] = v
        session.save()

        for k, v in kv.iteritems():
            assert k in session.book
            if isinstance(v, datetime.datetime):
                # check string format as the date in piecash is localized
                assert "{:%Y%m%d%h%M%s}".format(session.book[k]) == "{:%Y%m%d%h%M%s}".format(v)
            else:
                assert session.book[k] == v

    def test_empty_gnucash_file(self, session):
        accs = session.accounts

        assert len(accs)==2
        assert all(acc.parent is None for acc in accs)
        assert all(acc.account_type=="ROOT" for acc in accs)

    def test_add_account(self, session):
        Account(name="Foo",
                account_type="Bank",
                parent=session.book.root_account)
        session.save()
        assert len(session.accounts)==3
