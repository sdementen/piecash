# coding=utf-8
from __future__ import unicode_literals

from decimal import Decimal

# dummy line to avoid removing unused symbols
from piecash import Address, Employee, Account, Vendor, Customer, Job
from piecash.business import Taxtable, TaxtableEntry
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, Person

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, Person


class TestBusinessPerson_create_Person(object):
    """
    Person is a parameter taking values in [Customer, Vendor, Employee]
    """

    def test_create_customer_job(self, book_basic, Person):
        EUR = book_basic.commodities(namespace="CURRENCY")

        # create detached person
        c = Customer(name="John Föo", currency=EUR)
        j = Job(name="my job")

        c.jobs = [j]
        book_basic.add(c)
        book_basic.validate()
        book_basic.flush()
        print(c.jobs)
