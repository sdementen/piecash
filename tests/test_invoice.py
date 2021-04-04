# coding=utf-8
from __future__ import unicode_literals

from decimal import Decimal

from test_helper import (
    db_sqlite_uri,
    db_sqlite,
    new_book,
    new_book_USD,
    book_uri,
    book_invoices,
    Person,
)

# dummy line to avoid removing unused symbols
from piecash import Address, Employee, Account, Invoice
from piecash.business import Taxtable, TaxtableEntry

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_invoices, Person


class TestInvoice(object):
    """
    Person is a parameter taking values in [Customer, Vendor, Employee]
    """

    def test_create_person_noid_nobook(self, book_invoices):
        assert len(book_invoices.invoices) == 1
        invoice = book_invoices.invoices[0]
        assert invoice.charge_amt == 0
        assert len(invoice.entries) == 2
        entry = invoice.entries[0]
        assert entry.quantity == Decimal("25")
        assert entry.invoice == invoice
