# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
# from pytest.mark import parametrize
#
import shutil
import os

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
    def test_slots(self, session):

        session.book["foo"] = 1
        session.save()

        assert "foo" in session.book
        assert session.book["foo"]==1

        assert session.query(Slot).filter_by(obj_guid=session.book.guid).one().value == 1

