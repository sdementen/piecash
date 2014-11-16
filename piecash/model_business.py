from sqlalchemy import Column, INTEGER, BIGINT, TEXT, ForeignKey
from sqlalchemy.orm import composite, relation

# change of the __doc__ string as getting error in sphinx ==> should be reported to SA project
from piecash.sa_extra import Address

composite.__doc__ = composite.__doc__.replace(":ref:`mapper_composite`", "")

from .sa_extra import _Date, _DateTime
from .model_common import DeclarativeBaseGuid


class Billterm(DeclarativeBaseGuid):
    __tablename__ = 'billterms'

    __table_args__ = {}

    # column definitions
    cutoff = Column('cutoff', INTEGER())
    description = Column('description', TEXT(length=2048), nullable=False)
    discount_denom = Column('discount_denom', BIGINT())
    discount_num = Column('discount_num', BIGINT())
    discountdays = Column('discountdays', INTEGER())
    duedays = Column('duedays', INTEGER())
    invisible = Column('invisible', INTEGER(), nullable=False)
    name = Column('name', TEXT(length=2048), nullable=False)
    parent = Column('parent', TEXT(length=32))
    refcount = Column('refcount', INTEGER(), nullable=False)
    type = Column('type', TEXT(length=2048), nullable=False)

    # relation definitions


class Customer(DeclarativeBaseGuid):
    __tablename__ = 'customers'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    addr_addr1 = Column('addr_addr1', TEXT(length=1024))
    addr_addr2 = Column('addr_addr2', TEXT(length=1024))
    addr_addr3 = Column('addr_addr3', TEXT(length=1024))
    addr_addr4 = Column('addr_addr4', TEXT(length=1024))
    addr_email = Column('addr_email', TEXT(length=256))
    addr_fax = Column('addr_fax', TEXT(length=128))
    addr_name = Column('addr_name', TEXT(length=1024))
    addr_phone = Column('addr_phone', TEXT(length=128))
    addr = composite(Address, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_name, addr_phone)
    credit_denom = Column('credit_denom', BIGINT(), nullable=False)
    credit_num = Column('credit_num', BIGINT(), nullable=False)
    currency = Column('currency', TEXT(length=32), nullable=False)
    discount_denom = Column('discount_denom', BIGINT(), nullable=False)
    discount_num = Column('discount_num', BIGINT(), nullable=False)
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    id = Column('id', TEXT(length=2048), nullable=False)
    name = Column('name', TEXT(length=2048), nullable=False)
    notes = Column('notes', TEXT(length=2048), nullable=False)
    shipaddr_addr1 = Column('shipaddr_addr1', TEXT(length=1024))
    shipaddr_addr2 = Column('shipaddr_addr2', TEXT(length=1024))
    shipaddr_addr3 = Column('shipaddr_addr3', TEXT(length=1024))
    shipaddr_addr4 = Column('shipaddr_addr4', TEXT(length=1024))
    shipaddr_email = Column('shipaddr_email', TEXT(length=256))
    shipaddr_fax = Column('shipaddr_fax', TEXT(length=128))
    shipaddr_name = Column('shipaddr_name', TEXT(length=1024))
    shipaddr_phone = Column('shipaddr_phone', TEXT(length=128))
    shipaddr = composite(Address, shipaddr_addr1, shipaddr_addr2, shipaddr_addr3, shipaddr_addr4,
                         shipaddr_email, shipaddr_fax, shipaddr_name, shipaddr_phone)

    tax_included = Column('tax_included', INTEGER())
    tax_override = Column('tax_override', INTEGER(), nullable=False)
    taxtable = Column('taxtable', TEXT(length=32))
    terms = Column('terms', TEXT(length=32))

    # relation definitions


class Employee(DeclarativeBaseGuid):
    __tablename__ = 'employees'

    __table_args__ = {}

    # column definitions
    acl = Column('acl', TEXT(length=2048), nullable=False)
    active = Column('active', INTEGER(), nullable=False)
    addr_addr1 = Column('addr_addr1', TEXT(length=1024))
    addr_addr2 = Column('addr_addr2', TEXT(length=1024))
    addr_addr3 = Column('addr_addr3', TEXT(length=1024))
    addr_addr4 = Column('addr_addr4', TEXT(length=1024))
    addr_email = Column('addr_email', TEXT(length=256))
    addr_fax = Column('addr_fax', TEXT(length=128))
    addr_name = Column('addr_name', TEXT(length=1024))
    addr_phone = Column('addr_phone', TEXT(length=128))
    addr = composite(Address, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_name, addr_phone)
    ccard_guid = Column('ccard_guid', TEXT(length=32))
    currency = Column('currency', TEXT(length=32), nullable=False)
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    id = Column('id', TEXT(length=2048), nullable=False)
    language = Column('language', TEXT(length=2048), nullable=False)
    rate_denom = Column('rate_denom', BIGINT(), nullable=False)
    rate_num = Column('rate_num', BIGINT(), nullable=False)
    username = Column('username', TEXT(length=2048), nullable=False)
    workday_denom = Column('workday_denom', BIGINT(), nullable=False)
    workday_num = Column('workday_num', BIGINT(), nullable=False)

    # relation definitions


class Entry(DeclarativeBaseGuid):
    __tablename__ = 'entries'

    __table_args__ = {}

    # column definitions
    action = Column('action', TEXT(length=2048))
    b_acct = Column('b_acct', TEXT(length=32))
    b_paytype = Column('b_paytype', INTEGER())
    b_price_denom = Column('b_price_denom', BIGINT())
    b_price_num = Column('b_price_num', BIGINT())
    b_taxable = Column('b_taxable', INTEGER())
    b_taxincluded = Column('b_taxincluded', INTEGER())
    b_taxtable = Column('b_taxtable', TEXT(length=32))
    bill = Column('bill', TEXT(length=32))
    billable = Column('billable', INTEGER())
    billto_guid = Column('billto_guid', TEXT(length=32))
    billto_type = Column('billto_type', INTEGER())
    date = Column('date', _DateTime(), nullable=False)
    date_entered = Column('date_entered', _DateTime())
    description = Column('description', TEXT(length=2048))
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    i_acct = Column('i_acct', TEXT(length=32))
    i_disc_how = Column('i_disc_how', TEXT(length=2048))
    i_disc_type = Column('i_disc_type', TEXT(length=2048))
    i_discount_denom = Column('i_discount_denom', BIGINT())
    i_discount_num = Column('i_discount_num', BIGINT())
    i_price_denom = Column('i_price_denom', BIGINT())
    i_price_num = Column('i_price_num', BIGINT())
    i_taxable = Column('i_taxable', INTEGER())
    i_taxincluded = Column('i_taxincluded', INTEGER())
    i_taxtable = Column('i_taxtable', TEXT(length=32))
    invoice = Column('invoice', TEXT(length=32))
    notes = Column('notes', TEXT(length=2048))
    order_guid = Column('order_guid', TEXT(length=32))
    quantity_denom = Column('quantity_denom', BIGINT())
    quantity_num = Column('quantity_num', BIGINT())

    # relation definitions


class Invoice(DeclarativeBaseGuid):
    __tablename__ = 'invoices'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    billing_id = Column('billing_id', TEXT(length=2048))
    billto_guid = Column('billto_guid', TEXT(length=32))
    billto_type = Column('billto_type', INTEGER())
    charge_amt_denom = Column('charge_amt_denom', BIGINT())
    charge_amt_num = Column('charge_amt_num', BIGINT())
    currency = Column('currency', TEXT(length=32), nullable=False)
    date_opened = Column('date_opened', _DateTime())
    date_posted = Column('date_posted', _DateTime())
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    id = Column('id', TEXT(length=2048), nullable=False)
    notes = Column('notes', TEXT(length=2048), nullable=False)
    owner_guid = Column('owner_guid', TEXT(length=32))
    owner_type = Column('owner_type', INTEGER())
    post_acc = Column('post_acc', TEXT(length=32))
    post_lot = Column('post_lot', TEXT(length=32))
    post_txn = Column('post_txn', TEXT(length=32))
    terms = Column('terms', TEXT(length=32))

    # relation definitions


class Job(DeclarativeBaseGuid):
    __tablename__ = 'jobs'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    id = Column('id', TEXT(length=2048), nullable=False)
    name = Column('name', TEXT(length=2048), nullable=False)
    owner_guid = Column('owner_guid', TEXT(length=32))
    owner_type = Column('owner_type', INTEGER())
    reference = Column('reference', TEXT(length=2048), nullable=False)

    # relation definitions


class Order(DeclarativeBaseGuid):
    __tablename__ = 'orders'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    date_closed = Column('date_closed', _DateTime(), nullable=False)
    date_opened = Column('date_opened', _DateTime(), nullable=False)
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    id = Column('id', TEXT(length=2048), nullable=False)
    notes = Column('notes', TEXT(length=2048), nullable=False)
    owner_guid = Column('owner_guid', TEXT(length=32), nullable=False)
    owner_type = Column('owner_type', INTEGER(), nullable=False)
    reference = Column('reference', TEXT(length=2048), nullable=False)

    # relation definitions


class Vendor(DeclarativeBaseGuid):
    __tablename__ = 'vendors'

    __table_args__ = {}

    # column definitions
    active = Column('active', INTEGER(), nullable=False)
    addr_addr1 = Column('addr_addr1', TEXT(length=1024))
    addr_addr2 = Column('addr_addr2', TEXT(length=1024))
    addr_addr3 = Column('addr_addr3', TEXT(length=1024))
    addr_addr4 = Column('addr_addr4', TEXT(length=1024))
    addr_email = Column('addr_email', TEXT(length=256))
    addr_fax = Column('addr_fax', TEXT(length=128))
    addr_name = Column('addr_name', TEXT(length=1024))
    addr_phone = Column('addr_phone', TEXT(length=128))
    addr = composite(Address, addr_addr1, addr_addr2, addr_addr3, addr_addr4,
                     addr_email, addr_fax, addr_name, addr_phone)
    currency = Column('currency', TEXT(length=32), nullable=False)
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    id = Column('id', TEXT(length=2048), nullable=False)
    name = Column('name', TEXT(length=2048), nullable=False)
    notes = Column('notes', TEXT(length=2048), nullable=False)
    tax_inc = Column('tax_inc', TEXT(length=2048))
    tax_override = Column('tax_override', INTEGER(), nullable=False)
    tax_table = Column('tax_table', TEXT(length=32))
    terms = Column('terms', TEXT(length=32))

    # relation definitions


class Taxtable(DeclarativeBaseGuid):
    __tablename__ = 'taxtables'

    __table_args__ = {}

    # column definitions
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    invisible = Column('invisible', INTEGER(), nullable=False)
    name = Column('name', TEXT(length=50), nullable=False)
    parent = Column('parent', TEXT(length=32))
    refcount = Column('refcount', BIGINT(), nullable=False)

    # relation definitions


class TaxtableEntry(DeclarativeBaseGuid):
    __tablename__ = 'taxtable_entries'

    __table_args__ = {}

    # column definitions
    account = Column('account', TEXT(length=32), nullable=False)
    amount_denom = Column('amount_denom', BIGINT(), nullable=False)
    amount_num = Column('amount_num', BIGINT(), nullable=False)
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    taxtable = Column('taxtable', TEXT(length=32), nullable=False)
    type = Column('type', INTEGER(), nullable=False)

    #relation definitions


class Schedxaction(DeclarativeBaseGuid):
    __tablename__ = 'schedxactions'

    __table_args__ = {}

    # column definitions
    adv_creation = Column('adv_creation', INTEGER(), nullable=False)
    adv_notify = Column('adv_notify', INTEGER(), nullable=False)
    auto_create = Column('auto_create', INTEGER(), nullable=False)
    auto_notify = Column('auto_notify', INTEGER(), nullable=False)
    enabled = Column('enabled', INTEGER(), nullable=False)
    end_date = Column('end_date', _Date())
    instance_count = Column('instance_count', INTEGER(), nullable=False)
    last_occur = Column('last_occur', _Date())
    name = Column('name', TEXT(length=2048))
    num_occur = Column('num_occur', INTEGER(), nullable=False)
    rem_occur = Column('rem_occur', INTEGER(), nullable=False)
    start_date = Column('start_date', _Date())
    template_act_guid = Column('template_act_guid', TEXT(length=32), ForeignKey('accounts.guid'), nullable=False)

    # relation definitions


class Lot(DeclarativeBaseGuid):
    __tablename__ = 'lots'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', TEXT(length=32), ForeignKey('accounts.guid'))
    is_closed = Column('is_closed', INTEGER(), nullable=False)

    # relation definitions
    account = relation('Account', backref="lots")