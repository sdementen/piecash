import uuid

from sqlalchemy import Column, INTEGER, BIGINT, VARCHAR, ForeignKey
from sqlalchemy.orm import composite, relation


# change of the __doc__ string as getting error in sphinx ==> should be reported to SA project
composite.__doc__ = None  # composite.__doc__.replace(":ref:`mapper_composite`", "")

from .sa_extra import _DateTime, DeclarativeBase
from ._common import Address, CallableList, hybrid_property_gncnumeric
from ._declbase import DeclarativeBaseGuid


class Billterm(DeclarativeBaseGuid):
    __tablename__ = 'billterms'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    cutoff = Column('cutoff', INTEGER())
    description = Column('description', VARCHAR(length=2048), nullable=False)
    discount_denom = Column('discount_denom', BIGINT())
    discount_num = Column('discount_num', BIGINT())
    discountdays = Column('discountdays', INTEGER())
    duedays = Column('duedays', INTEGER())
    invisible = Column('invisible', INTEGER(), nullable=False)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    parent_guid = Column('parent', VARCHAR(length=32), ForeignKey('billterms.guid'))
    refcount = Column('refcount', INTEGER(), nullable=False)
    type = Column('type', VARCHAR(length=2048), nullable=False)

    # relation definitions
    children = relation('Billterm',
                        back_populates='parent',
                        cascade='all, delete-orphan',
                        collection_class=CallableList,
    )
    parent = relation('Billterm',
                      back_populates='children',
                      remote_side=guid,
    )

class Customer(DeclarativeBaseGuid):
    __tablename__ = 'customers'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    addr_addr1 = Column('addr_addr1', VARCHAR(length=1024))
    addr_addr2 = Column('addr_addr2', VARCHAR(length=1024))
    addr_addr3 = Column('addr_addr3', VARCHAR(length=1024))
    addr_addr4 = Column('addr_addr4', VARCHAR(length=1024))
    addr_email = Column('addr_email', VARCHAR(length=256))
    addr_fax = Column('addr_fax', VARCHAR(length=128))
    addr_name = Column('addr_name', VARCHAR(length=1024))
    addr_phone = Column('addr_phone', VARCHAR(length=128))
    addr = composite(Address, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_name, addr_phone)
    credit_denom = Column('credit_denom', BIGINT(), nullable=False)
    credit_num = Column('credit_num', BIGINT(), nullable=False)
    currency_guid = Column('currency', VARCHAR(length=32), ForeignKey('commodities.guid'),nullable=False)
    discount_denom = Column('discount_denom', BIGINT(), nullable=False)
    discount_num = Column('discount_num', BIGINT(), nullable=False)
    id = Column('id', VARCHAR(length=2048), nullable=False)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    notes = Column('notes', VARCHAR(length=2048), nullable=False)
    shipaddr_addr1 = Column('shipaddr_addr1', VARCHAR(length=1024))
    shipaddr_addr2 = Column('shipaddr_addr2', VARCHAR(length=1024))
    shipaddr_addr3 = Column('shipaddr_addr3', VARCHAR(length=1024))
    shipaddr_addr4 = Column('shipaddr_addr4', VARCHAR(length=1024))
    shipaddr_email = Column('shipaddr_email', VARCHAR(length=256))
    shipaddr_fax = Column('shipaddr_fax', VARCHAR(length=128))
    shipaddr_name = Column('shipaddr_name', VARCHAR(length=1024))
    shipaddr_phone = Column('shipaddr_phone', VARCHAR(length=128))
    shipaddr = composite(Address, shipaddr_addr1, shipaddr_addr2, shipaddr_addr3, shipaddr_addr4,
                         shipaddr_email, shipaddr_fax, shipaddr_name, shipaddr_phone)

    tax_included = Column('tax_included', INTEGER())
    tax_override = Column('tax_override', INTEGER(), nullable=False)
    taxtable_guid = Column('taxtable', VARCHAR(length=32), ForeignKey('taxtables.guid'))
    term_guid = Column('terms', VARCHAR(length=32), ForeignKey('billterms.guid'))

    # relation definitions
    taxtable = relation('Taxtable')
    currency= relation('Commodity')
    term = relation('Billterm')


class Employee(DeclarativeBaseGuid):
    __tablename__ = 'employees'

    __table_args__ = {}

    # column definitions
    acl = Column('acl', VARCHAR(length=2048), nullable=False)
    active = Column('active', INTEGER(), nullable=False)
    addr_addr1 = Column('addr_addr1', VARCHAR(length=1024))
    addr_addr2 = Column('addr_addr2', VARCHAR(length=1024))
    addr_addr3 = Column('addr_addr3', VARCHAR(length=1024))
    addr_addr4 = Column('addr_addr4', VARCHAR(length=1024))
    addr_email = Column('addr_email', VARCHAR(length=256))
    addr_fax = Column('addr_fax', VARCHAR(length=128))
    addr_name = Column('addr_name', VARCHAR(length=1024))
    addr_phone = Column('addr_phone', VARCHAR(length=128))
    addr = composite(Address, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_name, addr_phone)
    ccard_guid = Column('ccard_guid', VARCHAR(length=32), ForeignKey('accounts.guid'))
    currency_guid = Column('currency', VARCHAR(length=32), ForeignKey('commodities.guid'),nullable=False)
    id = Column('id', VARCHAR(length=2048), nullable=False)
    language = Column('language', VARCHAR(length=2048), nullable=False)
    rate_denom = Column('rate_denom', BIGINT(), nullable=False)
    rate_num = Column('rate_num', BIGINT(), nullable=False)
    username = Column('username', VARCHAR(length=2048), nullable=False)
    workday_denom = Column('workday_denom', BIGINT(), nullable=False)
    workday_num = Column('workday_num', BIGINT(), nullable=False)

    # relation definitions
    currency= relation('Commodity')
    credit_account = relation('Account')


class Entry(DeclarativeBaseGuid):
    __tablename__ = 'entries'

    __table_args__ = {}

    # column definitions
    action = Column('action', VARCHAR(length=2048))
    b_acct = Column('b_acct', VARCHAR(length=32))
    b_paytype = Column('b_paytype', INTEGER())
    b_price_denom = Column('b_price_denom', BIGINT())
    b_price_num = Column('b_price_num', BIGINT())
    b_taxable = Column('b_taxable', INTEGER())
    b_taxincluded = Column('b_taxincluded', INTEGER())
    b_taxtable = Column('b_taxtable', VARCHAR(length=32))
    bill = Column('bill', VARCHAR(length=32))
    billable = Column('billable', INTEGER())
    billto_guid = Column('billto_guid', VARCHAR(length=32))
    billto_type = Column('billto_type', INTEGER())
    date = Column('date', _DateTime(), nullable=False)
    date_entered = Column('date_entered', _DateTime())
    description = Column('description', VARCHAR(length=2048))
    i_acct = Column('i_acct', VARCHAR(length=32))
    i_disc_how = Column('i_disc_how', VARCHAR(length=2048))
    i_disc_type = Column('i_disc_type', VARCHAR(length=2048))
    i_discount_denom = Column('i_discount_denom', BIGINT())
    i_discount_num = Column('i_discount_num', BIGINT())
    i_price_denom = Column('i_price_denom', BIGINT())
    i_price_num = Column('i_price_num', BIGINT())
    i_taxable = Column('i_taxable', INTEGER())
    i_taxincluded = Column('i_taxincluded', INTEGER())
    i_taxtable = Column('i_taxtable', VARCHAR(length=32))
    invoice = Column('invoice', VARCHAR(length=32))
    notes = Column('notes', VARCHAR(length=2048))
    order_guid = Column('order_guid', VARCHAR(length=32))
    quantity_denom = Column('quantity_denom', BIGINT())
    quantity_num = Column('quantity_num', BIGINT())

    # relation definitions
    # todo: complete relations

class Invoice(DeclarativeBaseGuid):
    __tablename__ = 'invoices'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    billing_id = Column('billing_id', VARCHAR(length=2048))
    billto_guid = Column('billto_guid', VARCHAR(length=32))
    billto_type = Column('billto_type', INTEGER())
    _charge_amt_denom = Column('charge_amt_denom', BIGINT())
    _charge_amt_num = Column('charge_amt_num', BIGINT())
    charge_amt = hybrid_property_gncnumeric(_charge_amt_num, _charge_amt_denom)
    currency_guid = Column('currency', VARCHAR(length=32), ForeignKey('commodities.guid'),nullable=False)
    date_opened = Column('date_opened', _DateTime())
    date_posted = Column('date_posted', _DateTime())
    id = Column('id', VARCHAR(length=2048), nullable=False)
    notes = Column('notes', VARCHAR(length=2048), nullable=False)
    owner_guid = Column('owner_guid', VARCHAR(length=32))
    owner_type = Column('owner_type', INTEGER())
    post_acc_guid = Column('post_acc', VARCHAR(length=32), ForeignKey('accounts.guid'))
    post_lot_guid = Column('post_lot', VARCHAR(length=32), ForeignKey('transactions.guid'))
    post_txn_guid = Column('post_txn', VARCHAR(length=32), ForeignKey('lots.guid'))
    term_guid = Column('terms', VARCHAR(length=32), ForeignKey('billterms.guid'))

    # relation definitions
    # todo: check all relations and understanding of types...
    term = relation('Billterm')
    currency = relation('Commodity')
    post_account = relation('Account')
    post_lot = relation('Lot')
    post_txn = relation('Transaction')


class Job(DeclarativeBaseGuid):
    __tablename__ = 'jobs'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    id = Column('id', VARCHAR(length=2048), nullable=False)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    owner_guid = Column('owner_guid', VARCHAR(length=32))
    owner_type = Column('owner_type', INTEGER())
    reference = Column('reference', VARCHAR(length=2048), nullable=False)

    # relation definitions
    # todo: owner_guid/type links to Vendor or Customer

# This class exists in code but not in the GUI (to confirm?)
#
# class Order(DeclarativeBaseGuid):
#     __tablename__ = 'orders'
#
#     __table_args__ = {}
#
#     # column definitions
#     active = Column('active', INTEGER(), nullable=False)
#     date_closed = Column('date_closed', _DateTime(), nullable=False)
#     date_opened = Column('date_opened', _DateTime(), nullable=False)
#     id = Column('id', VARCHAR(length=2048), nullable=False)
#     notes = Column('notes', VARCHAR(length=2048), nullable=False)
#     owner_guid = Column('owner_guid', VARCHAR(length=32), nullable=False)
#     owner_type = Column('owner_type', INTEGER(), nullable=False)
#     reference = Column('reference', VARCHAR(length=2048), nullable=False)
#
#     # relation definitions
#     # todo: owner_guid/type links to Vendor or Customer


class Vendor(DeclarativeBaseGuid):
    __tablename__ = 'vendors'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    addr_addr1 = Column('addr_addr1', VARCHAR(length=1024))
    addr_addr2 = Column('addr_addr2', VARCHAR(length=1024))
    addr_addr3 = Column('addr_addr3', VARCHAR(length=1024))
    addr_addr4 = Column('addr_addr4', VARCHAR(length=1024))
    addr_email = Column('addr_email', VARCHAR(length=256))
    addr_fax = Column('addr_fax', VARCHAR(length=128))
    addr_name = Column('addr_name', VARCHAR(length=1024))
    addr_phone = Column('addr_phone', VARCHAR(length=128))
    addr = composite(Address, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_name, addr_phone)
    currency_guid = Column('currency', VARCHAR(length=32), ForeignKey('commodities.guid'),nullable=False)
    id = Column('id', VARCHAR(length=2048), nullable=False)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    notes = Column('notes', VARCHAR(length=2048), nullable=False)
    tax_inc = Column('tax_inc', VARCHAR(length=2048))
    tax_override = Column('tax_override', INTEGER(), nullable=False)
    tax_table_guid = Column('tax_table', VARCHAR(length=32), ForeignKey('taxtables.guid'))
    term_guid = Column('terms', VARCHAR(length=32), ForeignKey('billterms.guid'))

    # relation definitions
    taxtable = relation('Taxtable')
    currency= relation('Commodity')
    term = relation('Billterm')


class Taxtable(DeclarativeBaseGuid):
    __tablename__ = 'taxtables'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    invisible = Column('invisible', INTEGER(), nullable=False)
    name = Column('name', VARCHAR(length=50), nullable=False)
    parent_guid = Column('parent', VARCHAR(length=32), ForeignKey('taxtables.guid'))
    refcount = Column('refcount', BIGINT(), nullable=False)

    # relation definitions
    entries = relation('TaxtableEntry',
                       back_populates='taxtable',
                       cascade='all, delete-orphan',
                       collection_class=CallableList,
    )
    children = relation('Taxtable',
                        back_populates='parent',
                        cascade='all, delete-orphan',
                        collection_class=CallableList,
    )
    parent = relation('Taxtable',
                      back_populates='children',
                      remote_side=guid,
    )


class TaxtableEntry(DeclarativeBase):
    __tablename__ = 'taxtable_entries'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account', VARCHAR(length=32), ForeignKey('accounts.guid'),nullable=False)
    amount_denom = Column('amount_denom', BIGINT(), nullable=False)
    amount_num = Column('amount_num', BIGINT(), nullable=False)
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    taxtable_guid = Column('taxtable', VARCHAR(length=32),
                      ForeignKey('taxtables.guid'), nullable=False)
    type = Column('type', INTEGER(), nullable=False)

    # relation definitions
    taxtable = relation('Taxtable', back_populates='entries')
    account = relation('Account')


class Lot(DeclarativeBaseGuid):
    """
    A GnuCash Lot

    Attributes:
        is_closed (int) : todo
        account (:class:`piecash.core.account.Account`): todo
        splits (:class:`piecash.core.transaction.Split`): todo
    """
    __tablename__ = 'lots'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', VARCHAR(length=32), ForeignKey('accounts.guid'))
    is_closed = Column('is_closed', INTEGER(), nullable=False)

    # relation definitions
    account = relation('Account', back_populates='lots', )
    splits = relation('Split',
                      back_populates='lot',
                      cascade='all, delete-orphan',
                      collection_class=CallableList,
    )
