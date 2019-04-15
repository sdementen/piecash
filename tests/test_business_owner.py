# coding=utf-8
from __future__ import unicode_literals

# dummy line to avoid removing unused symbols
from piecash import Employee, Job
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, Person

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, Person


class TestBusinessPerson_create_Person(object):
    """
    Person is a parameter taking values in [Customer, Vendor, Employee]
    """

    def test_create_customer_job(self, book_basic, Person):
        EUR = book_basic.commodities(namespace="CURRENCY")

        # create detached person
        c = Person(name="John Föo", currency=EUR)
        book_basic.add(c)

        if Person != Employee:
            j = Job(name="my job", owner=c)

        book_basic.validate()
        book_basic.flush()
        if Person != Employee:
            print(c.jobs)
