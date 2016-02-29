# -*- coding: latin-1 -*-
import pytest

import sys
import codecs
import piecash
from test_helper import file_template_full

if sys.version_info.major == 2:
    out = codecs.getwriter('UTF-8')(sys.stdout)
else:
    out = sys.stdout

class TestLedger_out_write(object):
    def test_out_write(self):
        with piecash.open_book( file_template_full, open_if_lock=True ) as data:
            out.write(piecash.ledger(data))