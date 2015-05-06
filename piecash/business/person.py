from decimal import Decimal

from sqlalchemy import Column, VARCHAR, INTEGER, BIGINT, ForeignKey, types
from sqlalchemy.orm import composite, relation
from sqlalchemy_utils.types import choice

from piecash._common import hybrid_property_gncnumeric, Address
from piecash._declbase import DeclarativeBaseGuid


TaxIncludedType = [
    (1, "yes"),
    (2, "no"),
    (3, "use global")
]

class ChoiceType(types.TypeDecorator):

    impl = types.INTEGER()

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.iteritems() if v == value][0]

    def process_result_value(self, value, dialect):
        return self.choices[value]

class Customer(DeclarativeBaseGuid):
    __tablename__ = 'customers'

    __table_args__ = {}

    # column definitions
    name = Column('name', VARCHAR(length=2048), nullable=False)
    id = Column('id', VARCHAR(length=2048), nullable=False)
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
    addr = composite(Address, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_phone)

    shipaddr_name = Column('shipaddr_name', VARCHAR(length=1024))
    shipaddr_addr1 = Column('shipaddr_addr1', VARCHAR(length=1024))
    shipaddr_addr2 = Column('shipaddr_addr2', VARCHAR(length=1024))
    shipaddr_addr3 = Column('shipaddr_addr3', VARCHAR(length=1024))
    shipaddr_addr4 = Column('shipaddr_addr4', VARCHAR(length=1024))
    shipaddr_phone = Column('shipaddr_phone', VARCHAR(length=128))
    shipaddr_fax = Column('shipaddr_fax', VARCHAR(length=128))
    shipaddr_email = Column('shipaddr_email', VARCHAR(length=256))
    shipaddr = composite(Address, shipaddr_name, shipaddr_addr1, shipaddr_addr2, shipaddr_addr3, shipaddr_addr4,
                         shipaddr_email, shipaddr_fax, shipaddr_phone)

    term_guid = Column('terms', VARCHAR(length=32), ForeignKey('billterms.guid'))
    tax_included = Column('tax_included', ChoiceType(TaxIncludedType))
    taxtable_guid = Column('taxtable', VARCHAR(length=32), ForeignKey('taxtables.guid'))

    # relation definitions
    taxtable = relation('Taxtable')
    currency = relation('Commodity')
    term = relation('Billterm')

    def __init__(self,
                 name,
                 currency,
                 notes="",
                 active=1,
                 tax_override=0,
                 credit=Decimal(0),
                 discount=Decimal(0),
                 address=None,
                 shipping_address=None,
                 tax_included="use global"):
        self.name = name
        self.currency = currency
        self.notes = notes
        self.active = active
        self.credit = credit
        self.discount=discount
        self.tax_included = tax_included
        self.tax_override = tax_override
        if address is None:
            address=Address(name=name)
        self.addr = address
        if shipping_address is None:
            shipping_address=Address("")
        self.shipaddr = shipping_address

    def object_to_validate(self, change):
        yield self

    def validate(self):
        try:
            cnt = self.book["counters/gncCustomer"].value + 1
        except KeyError:
            cnt = 1
        self.id = "{:06d}".format(cnt)
        self.book["counters/gncCustomer"] = cnt

    def __unirepr__(self):
        return u"Customer<{}>".format(self.name)


class Employee(DeclarativeBaseGuid):
    __tablename__ = 'employees'

    __table_args__ = {}

    # column definitions
    username = Column('username', VARCHAR(length=2048), nullable=False)
    id = Column('id', VARCHAR(length=2048), nullable=False)
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
    addr = composite(Address, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_phone)

    # relation definitions
    currency = relation('Commodity')
    credit_account = relation('Account')


class Vendor(DeclarativeBaseGuid):
    __tablename__ = 'vendors'

    __table_args__ = {}

    # column definitions
    name = Column('name', VARCHAR(length=2048), nullable=False)
    id = Column('id', VARCHAR(length=2048), nullable=False)
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
    addr = composite(Address, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_phone)
    term_guid = Column('terms', VARCHAR(length=32), ForeignKey('billterms.guid'))
    tax_inc = Column('tax_inc', VARCHAR(length=2048))
    tax_table_guid = Column('tax_table', VARCHAR(length=32), ForeignKey('taxtables.guid'))

    # relation definitions
    taxtable = relation('Taxtable')
    currency = relation('Commodity')
    term = relation('Billterm')