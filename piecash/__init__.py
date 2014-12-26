# -*- coding: utf-8 -*-
"""Python interface to GnuCash documents"""
from . import metadata

__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright

from ._common import GncNoActiveSession, GnucashException
from .core import (Book, Account, ACCOUNT_TYPES,
                         Transaction, Split,
                         Commodity, Price,
                         create_book, open_book
)
from .business import Lot  # must import as Transaction has a relation to it
from .budget import Budget, BudgetAmount
from .kvp import slot
