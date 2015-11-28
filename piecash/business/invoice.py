import uuid

from sqlalchemy import Column, INTEGER, BIGINT, VARCHAR, ForeignKey
from sqlalchemy.orm import composite, relation

# change of the __doc__ string as getting error in sphinx ==> should be reported to SA project
composite.__doc__ = None  # composite.__doc__.replace(":ref:`mapper_composite`", "")

from ..sa_extra import _DateTime
from .._common import CallableList, hybrid_property_gncnumeric
from .._declbase import DeclarativeBaseGuid


class Billterm(DeclarativeBaseGuid):
    __tablename__ = 'billterms'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    description = Column('description', VARCHAR(length=2048), nullable=False)
    refcount = Column('refcount', INTEGER(), nullable=False)
    invisible = Column('invisible', INTEGER(), nullable=False)
    parent_guid = Column('parent', VARCHAR(length=32), ForeignKey('billterms.guid'))
    type = Column('type', VARCHAR(length=2048), nullable=False)
    duedays = Column('duedays', INTEGER())
    discountdays = Column('discountdays', INTEGER())
    _discount_num = Column('discount_num', BIGINT())
    _discount_denom = Column('discount_denom', BIGINT())
    discount = hybrid_property_gncnumeric(_discount_num, _discount_denom)
    cutoff = Column('cutoff', INTEGER())

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


class Entry(DeclarativeBaseGuid):
    __tablename__ = 'entries'

    __table_args__ = {}

    # column definitions
    date = Column('date', _DateTime(), nullable=False)
    date_entered = Column('date_entered', _DateTime())
    description = Column('description', VARCHAR(length=2048))
    action = Column('action', VARCHAR(length=2048))
    notes = Column('notes', VARCHAR(length=2048))
    quantity_num = Column('quantity_num', BIGINT())
    quantity_denom = Column('quantity_denom', BIGINT())

    i_acct = Column('i_acct', VARCHAR(length=32))
    i_price_num = Column('i_price_num', BIGINT())
    i_price_denom = Column('i_price_denom', BIGINT())
    i_discount_num = Column('i_discount_num', BIGINT())
    i_discount_denom = Column('i_discount_denom', BIGINT())
    invoice = Column('invoice', VARCHAR(length=32))
    i_disc_type = Column('i_disc_type', VARCHAR(length=2048))
    i_disc_how = Column('i_disc_how', VARCHAR(length=2048))
    i_taxable = Column('i_taxable', INTEGER())
    i_taxincluded = Column('i_taxincluded', INTEGER())
    i_taxtable = Column('i_taxtable', VARCHAR(length=32))

    b_acct = Column('b_acct', VARCHAR(length=32))
    b_price_num = Column('b_price_num', BIGINT())
    b_price_denom = Column('b_price_denom', BIGINT())
    bill = Column('bill', VARCHAR(length=32))
    b_taxable = Column('b_taxable', INTEGER())
    b_taxincluded = Column('b_taxincluded', INTEGER())
    b_taxtable = Column('b_taxtable', VARCHAR(length=32))
    b_paytype = Column('b_paytype', INTEGER())
    billable = Column('billable', INTEGER())
    billto_type = Column('billto_type', INTEGER())
    billto_guid = Column('billto_guid', VARCHAR(length=32))
    order_guid = Column('order_guid', VARCHAR(length=32), ForeignKey("orders.guid"))

    # relation definitions
    order = relation('Order', back_populates="entries")


class Invoice(DeclarativeBaseGuid):
    __tablename__ = 'invoices'

    __table_args__ = {}

    # column definitions
    id = Column('id', VARCHAR(length=2048), nullable=False)
    date_opened = Column('date_opened', _DateTime())
    date_posted = Column('date_posted', _DateTime())
    notes = Column('notes', VARCHAR(length=2048), nullable=False)
    active = Column('active', INTEGER(), nullable=False)
    currency_guid = Column('currency', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    owner_type = Column('owner_type', INTEGER())
    owner_guid = Column('owner_guid', VARCHAR(length=32))
    term_guid = Column('terms', VARCHAR(length=32), ForeignKey('billterms.guid'))
    billing_id = Column('billing_id', VARCHAR(length=2048))
    post_txn_guid = Column('post_txn', VARCHAR(length=32), ForeignKey('lots.guid'))
    post_lot_guid = Column('post_lot', VARCHAR(length=32), ForeignKey('transactions.guid'))
    post_acc_guid = Column('post_acc', VARCHAR(length=32), ForeignKey('accounts.guid'))
    billto_type = Column('billto_type', INTEGER())
    billto_guid = Column('billto_guid', VARCHAR(length=32))
    _charge_amt_num = Column('charge_amt_num', BIGINT())
    _charge_amt_denom = Column('charge_amt_denom', BIGINT())
    charge_amt = hybrid_property_gncnumeric(_charge_amt_num, _charge_amt_denom)

    # relation definitions
    # todo: check all relations and understanding of types...
    term = relation('Billterm')
    currency = relation('Commodity')
    post_account = relation('Account')
    post_lot = relation('Lot')
    post_txn = relation('Transaction')

    def __unirepr__(self):
        return u"Invoice<{}>".format(self.id)


class Job(DeclarativeBaseGuid):
    __tablename__ = 'jobs'

    __table_args__ = {}

    # column definitions
    id = Column('id', VARCHAR(length=2048), nullable=False)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    reference = Column('reference', VARCHAR(length=2048), nullable=False)
    active = Column('active', INTEGER(), nullable=False)
    owner_type = Column('owner_type', INTEGER())
    owner_guid = Column('owner_guid', VARCHAR(length=32))

    # relation definitions
    # todo: owner_guid/type links to Vendor or Customer


# This class exists in code but not in the GUI (to confirm?)

class Order(DeclarativeBaseGuid):
    __tablename__ = 'orders'

    __table_args__ = {}

    # column definitions
    id = Column('id', VARCHAR(length=2048), nullable=False)
    notes = Column('notes', VARCHAR(length=2048), nullable=False)
    reference = Column('reference', VARCHAR(length=2048), nullable=False)
    active = Column('active', INTEGER(), nullable=False)

    date_opened = Column('date_opened', _DateTime(), nullable=False)
    date_closed = Column('date_closed', _DateTime(), nullable=False)
    owner_type = Column('owner_type', INTEGER(), nullable=False)
    owner_guid = Column('owner_guid', VARCHAR(length=32), nullable=False)

    # relation definitions
    # todo: owner_guid/type links to Vendor or Customer
    entries = relation('Entry',
                       back_populates='order',
                       cascade='all, delete-orphan',
                       collection_class=CallableList,
                       )
