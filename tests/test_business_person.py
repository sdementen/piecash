# coding=utf-8
from __future__ import unicode_literals

from decimal import Decimal

# dummy line to avoid removing unused symbols
from piecash import Address, Employee, Account, Vendor, Customer
from piecash.business import Taxtable, TaxtableEntry
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, Person

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic, Person


class TestBusinessPerson_create_Person(object):
    """
    Person is a parameter taking values in [Customer, Vendor, Employee]
    """

    def test_create_person_noid_nobook(self, book_basic, Person):
        EUR = book_basic.commodities(namespace="CURRENCY")

        # create detached person
        c = Person(name="John Föo", currency=EUR)
        # id should not be set
        assert c.id is None

        # flushing should not set the id as person not added to book
        book_basic.flush()
        assert c.id is None

        # adding the person to the book does not per se set the id
        book_basic.add(c)
        assert c.id == '000001'
        # but validation sets the id if still to None
        assert getattr(book_basic, Person._counter_name) == 1

        book_basic.flush()
        assert c.id == "000001"
        assert getattr(book_basic, Person._counter_name) == 1

    def test_create_person_noid_inbook(self, book_basic, Person):
        EUR = book_basic.commodities(namespace="CURRENCY")

        # create person attached to book
        c = Person(name="John Föo", currency=EUR, book=book_basic)
        # id should have already been set
        assert c.id == "000001"

        # flushing should not change the id
        book_basic.flush()
        assert c.id == "000001"

    def test_create_person_id_inbook(self, book_basic, Person):
        EUR = book_basic.commodities(namespace="CURRENCY")

        # create person attached to book with a specific id
        cust_id = "éyO903"
        c = Person(name="John Föo", currency=EUR, book=book_basic, id=cust_id)
        # id should have already been set
        assert c.id == cust_id

        # flushing should not change the id
        book_basic.flush()
        assert c.id == cust_id

    def test_create_person_id_nobook(self, book_basic, Person):
        EUR = book_basic.commodities(namespace="CURRENCY")

        # create person detached from book with a specific id
        cust_id = "éyO903"
        c = Person(name="John Föo", currency=EUR, id=cust_id)
        # id should have already been set
        assert c.id == cust_id

        # flushing should not change the id (as the person is not yet attached to book)
        book_basic.flush()
        assert c.id == cust_id

        # adding the person to the book and flushing should not change the id
        book_basic.add(c)
        assert c.id == cust_id
        book_basic.flush()
        assert c.id == cust_id

    def test_create_person_address(self, book_basic, Person):
        EUR = book_basic.commodities(namespace="CURRENCY")

        # create person detached from book with a specific id
        addr = Address(name="Héllo", addr1="kap", email="foo@example.com")
        c = Person(name="John Föo", currency=EUR, address=addr, book=book_basic)

        assert c.addr_addr1 == "kap"
        assert c.address.addr1 == "kap"

        addr.addr1 = "pok"
        c2 = Person(name="Jané Döo", currency=EUR, address=addr, book=book_basic)
        book_basic.flush()

        assert c.addr_addr1 == "kap"
        assert c.address.addr1 == "kap"
        assert c2.addr_addr1 == "pok"
        assert c2.address.addr1 == "pok"

    def test_create_person_taxtabme(self, book_basic, Person):
        if Person is Employee:
            return

        EUR = book_basic.commodities(namespace="CURRENCY")

        # create person detached from book with a specific id
        taxtable = Taxtable(name="Local tax", entries=[
            TaxtableEntry(type="percentage",
                          amount=Decimal("6.5"),
                          account=Account(name="MyAcc", parent=book_basic.root_account, commodity=EUR, type="ASSET"))
        ])
        te = TaxtableEntry(type="percentage",
                           amount=Decimal("6.5"),
                           account=Account(name="MyOtherAcc", parent=book_basic.root_account, commodity=EUR,
                                           type="ASSET"),
                           taxtable=taxtable)

        c = Person(name="John Föo", currency=EUR, taxtable=taxtable, book=book_basic)
        assert len(taxtable.entries) == 2
        assert taxtable.entries[0].account.parent == book_basic.root_account

        book_basic.flush()

        assert book_basic.taxtables == [taxtable]
