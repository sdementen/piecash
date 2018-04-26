# -*- coding: latin-1 -*-

import sys

import piecash
from test_helper import file_template_full


class TestLedger_out_write(object):
    def test_out_write(self):
        with piecash.open_book(file_template_full, open_if_lock=True) as data:
            sys.stdout.write(piecash.ledger(data))
