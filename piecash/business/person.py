from decimal import Decimal

from sqlalchemy import Column, VARCHAR, INTEGER, BIGINT, ForeignKey
from sqlalchemy.orm import composite, relation, foreign

from .._common import hybrid_property_gncnumeric, CallableList
from .._declbase import DeclarativeBaseGuid
from ..sa_extra import ChoiceType

TaxIncludedType = [
    (1, "YES"),
    (2, "NO"),
    (3, "USEGLOBAL")
]


class Address(object):
    """An Address object encapsulates information regarding an address in GnuCash.

    Attributes:
        name (str): self explanatory
        addr1 (str): self explanatory
        addr2 (str): self explanatory
        addr3 (str): self explanatory
        addr4 (str): self explanatory
        email (str): self explanatory
        fax (str): self explanatory
        phone (str): self explanatory
    """
    _address_fields = ['name', 'addr1', 'addr2', 'addr3', 'addr4', 'email', 'fax', 'phone']

    def __init__(self, name="", addr1="", addr2="", addr3="", addr4="", email="", fax="", phone=""):
        self.name = name
        self.addr1 = addr1
        self.addr2 = addr2
        self.addr3 = addr3
        self.addr4 = addr4
        self.email = email
        self.fax = fax
        self.phone = phone

    def __composite_values__(self):
        return (getattr(self, fld) for fld in Address._address_fields)

    def __eq__(self, other):
        return isinstance(other, Address) and all(
            getattr(other, fld) == getattr(self, fld) for fld in Address._address_fields)

    def __ne__(self, other):
        return not self.__eq__(other)


class Customer(DeclarativeBaseGuid):
    """
    A GnuCash Customer

    Attributes:
        name (str): name of the Customer
        id (str): autonumber id with 5 digits (initialised to book.counter_customer + 1)
        notes (str): notes
        active (int): 1 if the customer is active, 0 otherwise
        discount (:class:`decimal.Decimal`): see Gnucash documentation
        credit (:class:`decimal.Decimal`): see Gnucash documentation
        currency (:class:`piecash.core.commodity.Commodity`): the currency of the customer
        tax_override (int): 1 if tax override, 0 otherwise
        address (:class:`Address`): the address of the customer
        shipping_address (:class:`Address`): the shipping address of the customer
        tax_included (str): 'yes', 'no', 'use global'
        taxtable (:class:`piecash.business.tax.TaxTable`): tax table of the customer
        term (:class:`piecash.business.invoice.Billterm`): bill term of the customer
    """
    __tablename__ = 'customers'

    __table_args__ = {}

    # column definitions
    name = Column('name', VARCHAR(length=2048), nullable=False)
    # id is nullable as it is set during validation (happening after flush)
    id = Column('id', VARCHAR(length=2048), nullable=True)
    notes = Column('notes', VARCHAR(length=2048), nullable=False)
    active = Column('active', INTEGER(), nullable=False)
    _discount_num = Column('discount_num', BIGINT())
    _discount_denom = Column('discount_denom', BIGINT())
    discount = hybrid_property_gncnumeric(_discount_num, _discount_denom)
    _credit_num = Column('credit_num', BIGINT(), nullable=False)
    _credit_denom = Column('credit_denom', BIGINT(), nullable=False)
    credit = hybrid_property_gncnumeric(_credit_num, _credit_denom)
    currency_guid = Column('currency', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    tax_override = Column('tax_override', INTEGER(), nullable=False)

    addr_name = Column('addr_name', VARCHAR(length=1024))
    addr_addr1 = Column('addr_addr1', VARCHAR(length=1024))
    addr_addr2 = Column('addr_addr2', VARCHAR(length=1024))
    addr_addr3 = Column('addr_addr3', VARCHAR(length=1024))
    addr_addr4 = Column('addr_addr4', VARCHAR(length=1024))
    addr_phone = Column('addr_phone', VARCHAR(length=128))
    addr_fax = Column('addr_fax', VARCHAR(length=128))
    addr_email = Column('addr_email', VARCHAR(length=256))
    address = composite(Address, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                        addr_email, addr_fax, addr_phone)

    shipaddr_name = Column('shipaddr_name', VARCHAR(length=1024))
    shipaddr_addr1 = Column('shipaddr_addr1', VARCHAR(length=1024))
    shipaddr_addr2 = Column('shipaddr_addr2', VARCHAR(length=1024))
    shipaddr_addr3 = Column('shipaddr_addr3', VARCHAR(length=1024))
    shipaddr_addr4 = Column('shipaddr_addr4', VARCHAR(length=1024))
    shipaddr_phone = Column('shipaddr_phone', VARCHAR(length=128))
    shipaddr_fax = Column('shipaddr_fax', VARCHAR(length=128))
    shipaddr_email = Column('shipaddr_email', VARCHAR(length=256))
    shipping_address = composite(Address, shipaddr_name, shipaddr_addr1, shipaddr_addr2, shipaddr_addr3, shipaddr_addr4,
                                 shipaddr_email, shipaddr_fax, shipaddr_phone)

    term_guid = Column('terms', VARCHAR(length=32), ForeignKey('billterms.guid'))
    tax_included = Column('tax_included', ChoiceType(TaxIncludedType))
    taxtable_guid = Column('taxtable', VARCHAR(length=32), ForeignKey('taxtables.guid'))

    # relation definitions
    taxtable = relation('Taxtable')
    currency = relation('Commodity')
    term = relation('Billterm')

    @classmethod
    def __declare_last__(cls):
        from .invoice import Job
        cls.jobs = relation('Job',
                            primaryjoin=cls.guid == foreign(Job.owner_guid),
                            cascade='all, delete-orphan',
                            collection_class=CallableList,
                            )

    def __init__(self,
                 name,
                 currency,
                 id=None,
                 notes="",
                 active=1,
                 tax_override=0,
                 credit=Decimal(0),
                 discount=Decimal(0),
                 taxtable=None,
                 address=None,
                 shipping_address=None,
                 tax_included="USEGLOBAL",
                 book=None):
        self.name = name
        self.currency = currency
        self.notes = notes
        self.active = active
        self.credit = credit
        self.discount = discount
        self.tax_included = tax_included
        self.taxtable = taxtable
        self.tax_override = tax_override
        if address is None:
            address = Address(name=name)
        self.address = address
        if shipping_address is None:
            shipping_address = Address("")
        self.shipping_address = shipping_address

        if book and id is None:
            self._assign_id(book)
            book.add(self)
        elif id is not None:
            if isinstance(id, int):
                self.id = str(id)
            else:
                self.id = id

    def _assign_id(self, book):
        book.counter_customer = cnt = book.counter_customer + 1
        self.id = "{:06d}".format(cnt)

    def object_to_validate(self, change):
        yield self

    def validate(self):
        if not self.id:
            self._assign_id(self.book)

    def __unirepr__(self):
        return u"Customer<{}:{}>".format(self.id, self.name)


class Employee(DeclarativeBaseGuid):
    """
    A GnuCash Employee

    Attributes:
        name (str): name of the Employee
        id (str): autonumber id with 5 digits (initialised to book.counter_employee + 1)
        language (str): language
        active (int): 1 if the employee is active, 0 otherwise
        workday (:class:`decimal.Decimal`): see Gnucash documentation
        rate (:class:`decimal.Decimal`): see Gnucash documentation
        currency (:class:`piecash.core.commodity.Commodity`): the currency of the employee
        address (:class:`Address`): the address of the employee
        creditcard_account (:class:`piecash.core.account.Account`): credit card account for the employee

    """
    __tablename__ = 'employees'

    __table_args__ = {}

    # column definitions
    name = Column('username', VARCHAR(length=2048), nullable=False)
    # id is nullable as it is set during validation (happening after flush)
    id = Column('id', VARCHAR(length=2048), nullable=True)
    language = Column('language', VARCHAR(length=2048), nullable=False)
    acl = Column('acl', VARCHAR(length=2048), nullable=False)
    active = Column('active', INTEGER(), nullable=False)
    currency_guid = Column('currency', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    ccard_guid = Column('ccard_guid', VARCHAR(length=32), ForeignKey('accounts.guid'))
    _workday_num = Column('workday_num', BIGINT(), nullable=False)
    _workday_denom = Column('workday_denom', BIGINT(), nullable=False)
    workday = hybrid_property_gncnumeric(_workday_num, _workday_denom)
    _rate_num = Column('rate_num', BIGINT(), nullable=False)
    _rate_denom = Column('rate_denom', BIGINT(), nullable=False)
    rate = hybrid_property_gncnumeric(_rate_num, _rate_denom)

    addr_name = Column('addr_name', VARCHAR(length=1024))
    addr_addr1 = Column('addr_addr1', VARCHAR(length=1024))
    addr_addr2 = Column('addr_addr2', VARCHAR(length=1024))
    addr_addr3 = Column('addr_addr3', VARCHAR(length=1024))
    addr_addr4 = Column('addr_addr4', VARCHAR(length=1024))
    addr_phone = Column('addr_phone', VARCHAR(length=128))
    addr_fax = Column('addr_fax', VARCHAR(length=128))
    addr_email = Column('addr_email', VARCHAR(length=256))
    address = composite(Address, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                        addr_email, addr_fax, addr_phone)

    # relation definitions
    currency = relation('Commodity')
    creditcard_account = relation('Account')

    def __init__(self,
                 name,
                 currency,
                 creditcard_account=None,
                 id=None,
                 active=1,
                 acl="",
                 language="",
                 workday=Decimal(0),
                 rate=Decimal(0),
                 address=None,
                 book=None):
        self.name = name
        self.currency = currency
        self.active = active
        self.workday = workday
        self.rate = rate
        self.acl = acl
        self.language = language
        self.creditcard_account = creditcard_account
        if address is None:
            address = Address(name=name)
        self.address = address

        if book and id is None:
            self._assign_id(book)
            book.add(self)
        elif id is not None:
            if isinstance(id, int):
                self.id = str(id)
            else:
                self.id = id

    def _assign_id(self, book):
        book.counter_employee = cnt = book.counter_employee + 1
        self.id = "{:06d}".format(cnt)

    def object_to_validate(self, change):
        yield self

    def validate(self):
        if not self.id:
            self._assign_id(self.book)

    def __unirepr__(self):
        return u"Employee<{}:{}>".format(self.id, self.name)


class Vendor(DeclarativeBaseGuid):
    """
    A GnuCash Vendor

    Attributes:
        name (str): name of the Vendor
        id (str): autonumber id with 5 digits (initialised to book.counter_vendor + 1)
        notes (str): notes
        active (int): 1 if the vendor is active, 0 otherwise
        currency (:class:`piecash.core.commodity.Commodity`): the currency of the vendor
        tax_override (int): 1 if tax override, 0 otherwise
        address (:class:`Address`): the address of the vendor
        tax_included (str): 'YES', 'NO', 'USEGLOBAL'
        taxtable (:class:`piecash.business.tax.TaxTable`): tax table of the vendor
        term (:class:`piecash.business.invoice.Billterm`): bill term of the vendor
    """
    __tablename__ = 'vendors'

    __table_args__ = {}

    # column definitions
    name = Column('name', VARCHAR(length=2048), nullable=False)
    # id is nullable as it is set during validation (happening after flush)
    id = Column('id', VARCHAR(length=2048), nullable=True)
    notes = Column('notes', VARCHAR(length=2048), nullable=False)
    currency_guid = Column('currency', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    active = Column('active', INTEGER(), nullable=False)
    tax_override = Column('tax_override', INTEGER(), nullable=False)

    addr_name = Column('addr_name', VARCHAR(length=1024))
    addr_addr1 = Column('addr_addr1', VARCHAR(length=1024))
    addr_addr2 = Column('addr_addr2', VARCHAR(length=1024))
    addr_addr3 = Column('addr_addr3', VARCHAR(length=1024))
    addr_addr4 = Column('addr_addr4', VARCHAR(length=1024))
    addr_phone = Column('addr_phone', VARCHAR(length=128))
    addr_fax = Column('addr_fax', VARCHAR(length=128))
    addr_email = Column('addr_email', VARCHAR(length=256))
    address = composite(Address, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                        addr_email, addr_fax, addr_phone)
    term_guid = Column('terms', VARCHAR(length=32), ForeignKey('billterms.guid'))
    tax_included = Column('tax_inc', VARCHAR(length=2048))
    tax_table_guid = Column('tax_table', VARCHAR(length=32), ForeignKey('taxtables.guid'))

    # relation definitions
    taxtable = relation('Taxtable')
    currency = relation('Commodity')
    term = relation('Billterm')

    def __init__(self,
                 name,
                 currency,
                 id=None,
                 notes="",
                 active=1,
                 tax_override=0,
                 taxtable=None,
                 credit=Decimal(0),
                 discount=Decimal(0),
                 address=None,
                 tax_included="USEGLOBAL",
                 book=None):
        self.name = name
        self.currency = currency
        self.notes = notes
        self.active = active
        self.credit = credit
        self.discount = discount
        self.tax_included = tax_included
        self.taxtable = taxtable
        self.tax_override = tax_override
        if address is None:
            address = Address(name=name)
        self.address = address

        if book and id is None:
            self._assign_id(book)
            book.add(self)
        elif id is not None:
            if isinstance(id, int):
                self.id = str(id)
            else:
                self.id = id

    def _assign_id(self, book):
        book.counter_vendor = cnt = book.counter_vendor + 1
        self.id = "{:06d}".format(cnt)

    def object_to_validate(self, change):
        yield self

    def validate(self):
        if not self.id:
            self._assign_id(self.book)

    def __unirepr__(self):
        return u"Vendor<{}:{}>".format(self.id, self.name)
