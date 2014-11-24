# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
# from pytest.mark import parametrize
#
import shutil
import os
import datetime

import pytest




# parametrize = pytest.mark.parametrize
from piecash import Transaction, Commodity, open_book, create_book
from piecash.model_core.account import Account
from piecash.kvp import Slot
from piecash.model_common import GnucashException
from piecash.model_core import Version, gnclock


@pytest.fixture
def session(request):
    s = create_book()
    return s


class TestIntegration_EmptyBook(object):
    def test_create_access_simple_slot(self, session):
        kv = {
            "vint": 3,
            "vfl":2.34,
            "vstr":"hello",
            # "vdate":datetime.datetime.now().date(),
            "vtime":datetime.datetime.now(),
            "vnum":(453,100)
        }
        for k, v in kv.iteritems():
            session.book[k] = v
        session.save()

        for k, v in kv.iteritems():
            assert k in session.book
            assert session.book[k]==v

        # assert session.query(Slot).filter_by(obj_guid=session.book.guid).one().value == 1

