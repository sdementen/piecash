import uuid

from sqlalchemy import Column, INTEGER, BIGINT, VARCHAR, ForeignKey
from sqlalchemy.orm import composite, relation

from .person import PersonType

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
    _quantity_num = Column('quantity_num', BIGINT())
    _quantity_denom = Column('quantity_denom', BIGINT())
    _quantity_denom_basis = None
    quantity = hybrid_property_gncnumeric(_quantity_num, _quantity_denom)

    i_acct = Column('i_acct', VARCHAR(length=32))
    _i_price_num = Column('i_price_num', BIGINT())
    _i_price_denom = Column('i_price_denom', BIGINT())
    _i_price_denom_basis = None
    i_price = hybrid_property_gncnumeric(_i_price_num, _i_price_denom)

    _i_discount_num = Column('i_discount_num', BIGINT())
    _i_discount_denom = Column('i_discount_denom', BIGINT())
    _i_discount_denom_basis = None
    i_discount = hybrid_property_gncnumeric(_i_discount_num, _i_discount_denom)

    invoice_guid = Column('invoice', VARCHAR(length=32), ForeignKey("invoices.guid"))
    i_disc_type = Column('i_disc_type', VARCHAR(length=2048))
    i_disc_how = Column('i_disc_how', VARCHAR(length=2048))
    i_taxable = Column('i_taxable', INTEGER())
    i_taxincluded = Column('i_taxincluded', INTEGER())
    i_taxtable = Column('i_taxtable', VARCHAR(length=32))

    b_acct = Column('b_acct', VARCHAR(length=32))
    _b_price_num = Column('b_price_num', BIGINT())
    _b_price_denom = Column('b_price_denom', BIGINT())
    _b_price_denom_basis = None
    b_price = hybrid_property_gncnumeric(_b_price_num, _b_price_denom)
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
    invoice = relation('Invoice', back_populates="entries")

    def __str__(self):
        return "Entry<{}>".format(self.description)


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

    # owner = generic_relationship(owner_type, owner_guid,
    #                              map_type2discriminator={"Customer": 2,
    #                                                      "Vendor": 1,
    #                                                      })
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

    entries = relation('Entry',
                       back_populates='invoice',
                       cascade='all, delete-orphan',
                       collection_class=CallableList,
                       )

    def __str__(self):
        return "Invoice<{}>".format(self.id)


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
    def __init__(self, name, owner, reference="", active=1):
        self.name = name
        self.reference = reference
        self.active = active
        self.owner_type = PersonType[type(owner)]
        self.owner_guid = owner.guid
        if owner.book:
            owner.book.add(self)

    def __str__(self):
        return "Job<{self.name}>".format(self=self)

    def on_book_add(self):
        self._assign_id()

    # hold the name of the counter to use for id
    _counter_name = "counter_job"

    def _assign_id(self):
        if not self.id:
            cnt = getattr(self.book, self._counter_name) + 1
            setattr(self.book, self._counter_name, cnt)
            self.id = "{:06d}".format(cnt)


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
