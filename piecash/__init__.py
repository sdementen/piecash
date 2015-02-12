# -*- coding: utf-8 -*-
"""Python interface to GnuCash documents"""
from . import metadata

__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright

from ._common import GncNoActiveSession, GnucashException, GncValidationError, GncImbalanceError
from .core import (Book,
                   Account, ACCOUNT_TYPES,
                   Transaction, Split, ScheduledTransaction, Lot,
                   Commodity, Price,
                   create_book, open_book,
                   factories,
)
from .business import Invoice, Employee, Customer, Job, Vendor  # must import as Transaction has a relation to it
from .budget import Budget, BudgetAmount
from .kvp import slot
