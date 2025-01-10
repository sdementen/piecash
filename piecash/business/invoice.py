import uuid
import datetime
from enum import Enum

from sqlalchemy import Column, INTEGER, BIGINT, VARCHAR, ForeignKey, select, case, text, event, exists
from sqlalchemy.orm import composite, relation, column_property
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.ext.hybrid import hybrid_property
from decimal import Decimal

from .person import PersonType, Person, Customer, Vendor, Employee

# change of the __doc__ string as getting error in sphinx ==> should be reported to SA project

composite.__doc__ = None  # composite.__doc__.replace(":ref:`mapper_composite`", "")

from ..sa_extra import _DateTime, pure_slot_property
from .._common import CallableList, hybrid_property_gncnumeric
from .._declbase import DeclarativeBaseGuid

from ..core.account import Account, income_types, asset_types, expense_types
from ..core.transaction import Transaction, Split, Lot
from .tax import Taxtable, DiscountType, DiscountHow

class Paytype(Enum):
    cash = 1
    credit = 2

class Termtype(Enum):
    days = "GNC_TERM_TYPE_DAYS"
    proximo = "GNC_TERM_TYPE_PROXIMO"

class Job(DeclarativeBaseGuid):
    __tablename__ = "jobs"

    __table_args__ = {}

    # column definitions
    id = Column("id", VARCHAR(length=2048), nullable=False)
    name = Column("name", VARCHAR(length=2048), nullable=False)
    reference = Column("reference", VARCHAR(length=2048), nullable=False)
    active = Column("active", INTEGER(), nullable=False)
    owner_type = Column("owner_type", INTEGER())
    owner_guid = Column("owner_guid", VARCHAR(length=32))

    rate = pure_slot_property(slot_name="job-rate", slot_transform=float)

    # relation definitions
    # todo: owner_guid/type links to Vendor or Customer
    _customer = relation(Customer, uselist=False, primaryjoin='Customer.guid == Job.owner_guid', foreign_keys=Customer.guid)
    _vendor = relation(Vendor, uselist=False, primaryjoin='Vendor.guid == Job.owner_guid', foreign_keys=Vendor.guid)

    def __init__(self, name, owner, reference="", active=1, rate=0):
        #At least a name and owner need to be specified
        if not name:
            raise ValueError('Need a name for the job')
            
        if not (owner and (isinstance(owner, Customer) or isinstance(owner, Vendor))):
            raise ValueError("Need a valid owner (Customer or Vendor) for job.")

        self.name = name
        self.reference = reference
        self.active = active
        self.owner_type = PersonType[type(owner)]
        self.owner_guid = owner.guid
        if owner.book:
            owner.book.add(self)

        self.rate = rate

    @property
    def owner(self):
        return self._customer or self._vendor

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

class Billterm(DeclarativeBaseGuid):
    __tablename__ = "billterms"

    __table_args__ = {}

    # column definitions
    guid = Column(
        "guid",
        VARCHAR(length=32),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex,
    )
    name = Column("name", VARCHAR(length=2048), nullable=False)
    description = Column("description", VARCHAR(length=2048), nullable=False)
    refcount = Column("refcount", INTEGER(), nullable=False)
    invisible = Column("invisible", INTEGER(), nullable=False)
    parent_guid = Column("parent", VARCHAR(length=32), ForeignKey("billterms.guid"))
    type = Column("type", VARCHAR(length=2048), nullable=False)
    duedays = Column("duedays", INTEGER())
    discountdays = Column("discountdays", INTEGER())
    _discount_num = Column("discount_num", BIGINT())
    _discount_denom = Column("discount_denom", BIGINT())
    discount = hybrid_property_gncnumeric(_discount_num, _discount_denom)
    cutoff = Column("cutoff", INTEGER())

    # relation definitions
    children = relation(
        "Billterm",
        back_populates="parent",
        cascade="all, delete-orphan",
        collection_class=CallableList,
    )
    parent = relation(
        "Billterm",
        back_populates="children",
        remote_side=guid,
    )

    def __str__(self):
        return "Billterm<{}>".format(self.name)
    
    def __init__(self, name, description='', term_type=Termtype.days, duedays=30, discountdays=0, discount=0, cutoff=0, book=None):
        if not name:
            raise ValueError("Please provide a name for the Billterm")
        if not term_type in Termtype:
            raise ValueError(f"term_type must be one of {Termtype}")

        self.name = name
        self.description = description
        self.type = term_type.value
        self.duedays = duedays
        self.discountdays = discountdays
        self.discount = 0
        self.refcount = 0
        self.invisible = 0
        if term_type == Termtype.proximo:
            self.cutoff = cutoff
        else:
            self.cutoff = 0
        
        if book:
            book.add(self)
            book.flush()
    
    # adjust the refcount field - called by e.g. Person and Invoice/Bill/Expensevoucher
    def _increase_refcount(self, connection, increment=1):
        r = connection.execute(
            self.__table__.
            select().
            where(Billterm.guid == self.guid))
        refcountval = r.fetchone()[3]
        connection.execute(
            self.__table__.
            update().        
            values(refcount=refcountval+increment).
            where(Billterm.guid == self.guid))
        
    # adjust the refcount field - called by e.g. Person and Invoice/Bill/Expensevoucher
    def _decrease_refcount(self, connection):
        self._increase_refcount(connection, increment=-1)

class Entry(DeclarativeBaseGuid):
    __tablename__ = "entries"

    __table_args__ = {}

    # column definitions
    date = Column("date", _DateTime(), nullable=False)
    date_entered = Column("date_entered", _DateTime())
    description = Column("description", VARCHAR(length=2048))
    action = Column("action", VARCHAR(length=2048))
    notes = Column("notes", VARCHAR(length=2048))
    _quantity_num = Column("quantity_num", BIGINT())
    _quantity_denom = Column("quantity_denom", BIGINT())
    _quantity_denom_basis = None
    quantity = hybrid_property_gncnumeric(_quantity_num, _quantity_denom)

    _i_acct = Column("i_acct", VARCHAR(length=32), ForeignKey("accounts.guid"))
    _i_price_num = Column("i_price_num", BIGINT())
    _i_price_denom = Column("i_price_denom", BIGINT())
    _i_price_denom_basis = None
    _i_price = hybrid_property_gncnumeric(_i_price_num, _i_price_denom)

    _i_discount_num = Column("i_discount_num", BIGINT())
    _i_discount_denom = Column("i_discount_denom", BIGINT())
    _i_discount_denom_basis = None
    _i_discount = hybrid_property_gncnumeric(_i_discount_num, _i_discount_denom)

    invoice_guid = Column("invoice", VARCHAR(length=32), ForeignKey("invoices.guid"))
    _i_disc_type = Column("i_disc_type", VARCHAR(length=2048))
    _i_disc_how = Column("i_disc_how", VARCHAR(length=2048))
    _i_taxable = Column("i_taxable", INTEGER())
    _i_taxincluded = Column("i_taxincluded", INTEGER())
    _i_taxtable_guid = Column("i_taxtable", VARCHAR(length=32), ForeignKey("taxtables.guid"))

    _b_acct = Column("b_acct", VARCHAR(length=32), ForeignKey("accounts.guid"))
    _b_price_num = Column("b_price_num", BIGINT())
    _b_price_denom = Column("b_price_denom", BIGINT())
    _b_price_denom_basis = None
    _b_price = hybrid_property_gncnumeric(_b_price_num, _b_price_denom)

    bill_guid = Column("bill", VARCHAR(length=32), ForeignKey("invoices.guid"))

    _b_taxable = Column("b_taxable", INTEGER())
    _b_taxincluded = Column("b_taxincluded", INTEGER())
    _b_taxtable_guid = Column("b_taxtable", VARCHAR(length=32), ForeignKey("taxtables.guid"))
    _b_paytype = Column("b_paytype", INTEGER())
    billable = Column("billable", INTEGER())
    _billto_type = Column("billto_type", INTEGER())
    _billto_guid = Column("billto_guid", VARCHAR(length=32))
    _order_guid = Column("order_guid", VARCHAR(length=32), ForeignKey("orders.guid"))

    # relation definitions
    order = relation("Order", back_populates="entries")
    invoice = relation("InvoiceBase", foreign_keys=[invoice_guid], back_populates="_invoice_entries")
    bill = relation("InvoiceBase", foreign_keys=[bill_guid], back_populates="_bill_entries")
    _i_taxtable = relation("Taxtable", foreign_keys=[_i_taxtable_guid])
    _b_taxtable = relation("Taxtable", foreign_keys=[_b_taxtable_guid])
    _i_account = relation("Account", foreign_keys=[_i_acct])
    _b_account = relation("Account", foreign_keys=[_b_acct])

    def __str__(self):
        return "Entry<{}>".format(self.description)

    def __init__(self, 
        invoice,                            #Invoice/bill/expense voucher object
        date=datetime.datetime.now().replace(microsecond=0),   #date item was sold
        date_entered=datetime.datetime.now().replace(microsecond=0), 
        description='',                     #item or service description
        action='',                          #user-defined field (cost center information), or Hours, Material, Project 
        notes='',                       
        quantity=None,                      #how many items were sold
        price=0,                            #unit price of item. Note: to specify price, an account also needs to be specified (issues in GUI otherwise)
        account=None,                       #income account that is to be credited (invoice) / expense account to charged (bill, expense voucher)
        taxable=True,                       #True/1 - yes, False/0 - no. If taxtable is provided, must be True
        taxincluded=False,                  #tax already included in unit price? True/1 - yes, False/0 - no
        taxtable=None,                      #info re tax percentage and account to which tax is charged
        i_discount=0,                       #total discount
        i_disc_type=DiscountType.percent,   #type of discount; VALUE - monetary value, PERCENT - percentage
        i_disc_how=DiscountHow.pretax,      #computation method; POSTTAX - discount after tax, PRETAX - discount before tax, SAMETIME - discount and tax applied to pretax value
        b_paytype=Paytype.cash,             #Cash or credit account. Applicable for employees only, and requires that a credit account has been set for the employee.
        billable=False):                    #True/1 - yes, False/0 - no - only applicable for bills: ignored for invoices and expense vouchers
        
        #order=None                         #There is no mention of orders in the Gnucash user manual, besides a mention under 'Counters'. Some artifact of something started but abandoned?
        #billto=None                        #Can't see that the Gnucash interface allows to set per-entry bill-to(?). Ignore for now.

        #Check that a valid invoice pas provided.
        if not invoice or not type(invoice) in [Invoice, Bill, Expensevoucher]:
            raise ValueError(f"Please provide a valid invoice, bill, or expense voucher - {invoice} provided.")

        book = (invoice and invoice.book)
        if book:
            book.add(self)

        self.quantity = quantity            
        self.date = date
        self.date_entered = date_entered
        self.description = description
        self.action = action
        self.notes = notes
        self.order_guid = None
    
        if type(invoice) is Invoice:
            self.invoice = invoice
            
            self.i_discount = i_discount
            self.i_disc_type = i_disc_type
            self.i_disc_how = i_disc_how
        else:
            self.bill = invoice

            self.i_discount = 0
            self.i_disc_type = DiscountType.percent
            self.i_disc_how = DiscountHow.pretax        
    
        self.account = account
        self.price = price
        self.taxtable = taxtable
        self.taxincluded = taxincluded
        self.taxable = taxable
        
        #gnucash sets these fields irrespective of invoice/bill/expense voucher
        self.b_paytype = b_paytype
        self.billable = billable

    def _get_entry_field_prefix(self):
        # convenience method to set the i-half or b-half of the entry row depending on Invoice or Bill/Expensevoucher
        # assume dealing with invoice
        this_prefix = '_i_'
        other_prefix = '_b_'

        # if neccessary, swap
        if not self.invoice:        #then we have a bill
            this_prefix, other_prefix = other_prefix, this_prefix

        return this_prefix, other_prefix

    @property
    def price(self):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        return getattr(self, this_prefix+'price')

    @price.setter
    def price(self, price):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        setattr(self, other_prefix+'price', 0)
        if (price and price != 0) and not self.account:
            #Price without account gives an error message in the GUI if one attempts to edit the entry. 
            raise ValueError("To set the price, please set a valid account first.")
        else:
            setattr(self, this_prefix+'price', price)

    @property
    def i_discount(self):
        return self._i_discount

    @i_discount.setter
    def i_discount(self, i_discount):
        self._i_discount = i_discount
    
    @property
    def i_disc_type(self):
        return DiscountType(self._i_disc_type)

    @i_disc_type.setter
    def i_disc_type(self, i_disc_type):
        if i_disc_type in DiscountType:
            self._i_disc_type = i_disc_type.value
        else:
            raise ValueError(f"Unrecognised value for i_disc_type: - {i_disc_type} was provided")

    @property
    def i_disc_how(self):
        return DiscountHow(self._i_disc_how)

    @i_disc_how.setter
    def i_disc_how(self, i_disc_how):
        if i_disc_how in DiscountHow:
            self._i_disc_how = i_disc_how.value
        else:
            raise ValueError(f"Unrecognised value for i_disc_how: - {i_disc_how} was provided")
    
    @property
    def account(self):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        return getattr(self, this_prefix+'account')

    @account.setter
    def account(self, accnt):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        
        setattr(self, other_prefix+'account', None)
        if not accnt:
            setattr(self, this_prefix+'account', None)
        else:
            setattr(self, this_prefix+'account', accnt)

    @property
    def taxable(self):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        return getattr(self, this_prefix+'taxable')

    @taxable.setter
    def taxable(self, taxable):
        this_prefix, other_prefix = self._get_entry_field_prefix()

        setattr(self, other_prefix+'taxable', True)
        if (not taxable) and self.taxtable:
            raise ValueError("Cannot set taxable to False while also specifying taxtable. Please unset taxtable first.") 
        else:
            setattr(self, this_prefix+'taxable', taxable)

    @property
    def taxtable(self):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        return getattr(self, this_prefix+'taxtable')

    @taxtable.setter
    def taxtable(self, taxtable):
        this_prefix, other_prefix = self._get_entry_field_prefix()

        setattr(self, other_prefix+'taxtable', None)
        if taxtable and type(taxtable) is not Taxtable:
            raise ValueError("Please provide a valid taxtable.")        
        else:
            setattr(self, this_prefix+'taxtable', taxtable)
            
    @property
    def taxincluded(self):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        return getattr(self, this_prefix+'taxincluded')

    @taxincluded.setter
    def taxincluded(self, taxincluded):
        this_prefix, other_prefix = self._get_entry_field_prefix()

        setattr(self, other_prefix+'taxincluded', False)
        setattr(self, this_prefix+'taxincluded', taxincluded)

    @property
    def b_paytype(self):
        return Paytype(self._b_paytype)

    @b_paytype.setter
    def b_paytype(self, b_paytype):
        if b_paytype == Paytype.credit and (type(self.bill) is not Expensevoucher):
            raise ValueError("Please provide a valid employee to use a paytype of type credit.")
        elif b_paytype == Paytype.credit and type(self.bill.end_owner.creditcard_account) is not Account:
            raise ValueError(f"Please set a credit account for employee {self.bill.end_owner} before using a paytype of type credit.")
        elif b_paytype in Paytype:
            self._b_paytype = b_paytype.value
        else:
            raise ValueError(f"Unrecognised value for b_paytype: - {b_paytype} was provided")
    
    @classmethod
    def __declare_last__(cls):
        # add listeners to update the Taxtable.refcount field
        if hasattr(cls, "taxtable"):
            event.listen(cls, "after_insert", cls._changed)
            event.listen(cls, "after_update", cls._changed)
            event.listen(cls, "after_delete", cls._deleted)

    def _changed(mapper, connection, target):
        # check if the taxtable field changed, obtain new and old value, and update the refcount for the taxtable
        newval, _, oldval = get_history(target, '_i_taxtable')
        if newval and (newval[0] is not None):
            newval[0]._increase_refcount(connection)
        if oldval and (oldval[0] is not None):
            oldval[0]._decrease_refcount(connection)

        newval, _, oldval = get_history(target, '_b_taxtable')
        if newval and (newval[0] is not None):
            newval[0]._increase_refcount(connection)
        if oldval and (oldval[0] is not None):
            oldval[0]._decrease_refcount(connection)
            
    def _deleted(mapper, connection, target):
        # only one of i_taxtable and b_taxtable should ever be set for a single entry 
        if target._i_taxtable:
            target._i_taxtable._decrease_refcount(connection)
        elif target._b_taxtable:
            target._b_taxtable._decrease_refcount(connection)

    @property
    def subtotal_and_tax(self):
        tax = 0
        subtotal = 0
        tax_per_taxaccount = {}
        if self.taxable and self.taxtable:
            subtotal, tax, tax_per_taxaccount = self.taxtable.calculate_subtotal_and_tax(self.quantity, self.price, self.i_disc_how, self.i_disc_type, self.i_discount, self.taxincluded)
        else:   #not taxable or don't have the means to calculate taxes
            if self.i_disc_type == DiscountType.percent:
                subtotal = self.quantity * self.price * (1 - self.i_discount/100)
            else:
                subtotal = self.quantity * self.price - self.i_discount
        return subtotal, tax, tax_per_taxaccount
        
class InvoiceBase(DeclarativeBaseGuid):
    """
    - This class is a superclass for Invoices, Bills, and Expense vouchers. 
    - An Invoice is owned by a Customer, a Bill is owned by a Vendor, and an Expensevoucher is owned by an Employee
    - An Invoice may be owned by a Job, provided the Job's owner is a Customer
    - A Bill may be owned by a Job, provided the Job's owner is a Vendor

    Attributes:
        id (str): autonumber id with 6 digits (initialised to book.counter_employee + 1)
        date_opened (DateTime): date and time the invoice was established
        date_posted (DateTime): date and time the invoice was posted
        notes (str): optional field for notes 
        active (int): 1 if the invoice is active, 0 otherwise
        currency (:class:`piecash.core.commodity.Commodity`): the currency of the invoice
        owner (:class:'piecash.business.person.Customer' or piecash.business.person.Vendor' or piecash.business.person.Employee' or piecash.business.invoice.Job'
        term (:class:'piecash.business.invoice.Billterm'): optional terms for the invoice
        billing_id (str): optional field for a billing id
        billto (:class:'piecash.business.person.Customer' or 'piecash.business.invoice.Job' (where Job's owner is a Customer)
        is_credit_note (int): 1 if the invoice is a credit note, 0 otherwise
    """
    __tablename__ = "invoices"

    __table_args__ = {}

    # column definitions
    id = Column("id", VARCHAR(length=2048), nullable=False)
    date_opened = Column("date_opened", _DateTime())
    date_posted = Column("date_posted", _DateTime())
    notes = Column("notes", VARCHAR(length=2048), nullable=False)
    active = Column("active", INTEGER(), nullable=False)
    currency_guid = Column(
        "currency", VARCHAR(length=32), ForeignKey("commodities.guid"), nullable=False
    )

    owner_type = Column("owner_type", INTEGER())    
    owner_guid = Column("owner_guid", VARCHAR(length=32))

    # owner = generic_relationship(owner_type, owner_guid,
    #                              map_type2discriminator={"Customer": 2,
    #                                                      "Vendor": 1,
    #                                                      })

    term_guid = Column("terms", VARCHAR(length=32), ForeignKey("billterms.guid"))
    billing_id = Column("billing_id", VARCHAR(length=2048))
    post_txn_guid = Column("post_txn", VARCHAR(length=32), ForeignKey("transactions.guid"))
    post_lot_guid = Column(
        "post_lot", VARCHAR(length=32), ForeignKey("lots.guid")
    )
    post_acc_guid = Column("post_acc", VARCHAR(length=32), ForeignKey("accounts.guid"))
    billto_type = Column("billto_type", INTEGER())
    billto_guid = Column("billto_guid", VARCHAR(length=32))
    _charge_amt_num = Column("charge_amt_num", BIGINT())
    _charge_amt_denom = Column("charge_amt_denom", BIGINT())
    charge_amt = hybrid_property_gncnumeric(_charge_amt_num, _charge_amt_denom)

    is_credit_note = pure_slot_property("credit-note")

    # relation definitions
    # todo: check all relations and understanding of types...
    term = relation("Billterm")
    currency = relation("Commodity")
    post_account = relation("Account")
    post_lot = relation("Lot")
    post_txn = relation("Transaction")

    _invoice_entries = relation(
        "Entry",
        back_populates="invoice",
        cascade="all, delete-orphan",
        collection_class=CallableList,
        foreign_keys=Entry.invoice_guid
    )

    _bill_entries = relation(
        "Entry",
        back_populates="bill",
        cascade="all, delete-orphan",
        collection_class=CallableList,
        foreign_keys=Entry.bill_guid
    )

    _payment_split = column_property(
        select([Split.guid]).\
        where(Split.lot_guid==post_lot_guid).\
        where(Split.action=='Payment')
    )

    is_paid = column_property(
        exists().\
        where(Split.lot_guid==post_lot_guid).\
        where(Split.action=='Payment')
    )

    _job_owner_type = column_property(
        select([Job.owner_type]).\
        where(Job.guid==owner_guid).\
        correlate_except(Job))

    _end_owner_type = column_property(
        case(
            [
                (owner_type == text('3'), _job_owner_type),
            ],
            else_=owner_type
        )
    )

    from ..sa_extra import tz, utc
    is_posted = column_property(
        case(
            [
                (date_posted == None, False),
                (date_posted == utc.localize(datetime.datetime(1970, 1, 1, 0, 0, 0)).astimezone(tz), False),
            ],
            else_=True
        )
    )

    __mapper_args__ = {
        "polymorphic_identity": "invoices",
        "polymorphic_on": _end_owner_type,
    }

    job = relation(Job, uselist=False, primaryjoin='Job.guid == InvoiceBase.owner_guid', foreign_keys=Job.guid)
    _customer = relation(Customer, uselist=False, primaryjoin='Customer.guid == InvoiceBase.owner_guid', foreign_keys=Customer.guid)
    _vendor = relation(Vendor, uselist=False, primaryjoin='Vendor.guid == InvoiceBase.owner_guid', foreign_keys=Vendor.guid)
    _employee = relation(Employee, uselist=False, primaryjoin='Employee.guid == InvoiceBase.owner_guid', foreign_keys=Employee.guid)
    _billto_customer = relation(Customer, uselist=False, primaryjoin='Customer.guid == InvoiceBase.billto_guid', foreign_keys=Customer.guid)
    _billto_job = relation(Job, uselist=False, primaryjoin='Job.guid == InvoiceBase.billto_guid', foreign_keys=Job.guid)

    @property
    def entries(self):
        if type(self) is Invoice:
            return self._invoice_entries
        elif type(self) in [Bill, Expensevoucher]:
            return self._bill_entries
 
    def _create_invoice(self, 
        owner,                  #Either a customer (for invoices), vendor (for bills), or employee (for expenses), or job
        currency,
        date_opened=datetime.datetime.now().replace(microsecond=0), 
        notes='', 
        term=None, 
        billing_id='', 
        book=None, 
        active=True,
        billto=None,
        is_credit_note=False):    
 
        #Although not required to add invoice to the database, the invoice won't be found in the GnuCash GUI without an owner attached
        if not (type(owner) in [Customer, Vendor, Employee, Job]):
            raise ValueError(f'Unknown owner type - {owner}')
        elif type(self) is Invoice and not (type(owner) is Customer or (type(owner) is Job and type(owner.owner) is Customer)):
            raise ValueError(f"Only Customers and Customer Jobs can create invoices - {owner} was provided.")
        elif type(self) is Bill and not (type(owner) is Vendor or (type(owner) is Job and type(owner.owner) is Vendor)):
            raise ValueError(f"Only Vendors and Vendor Jobs can create bills - {owner} was provided.")
        elif type(self) is Expensevoucher and not type(owner) is Employee:
            raise ValueError(f"Only Employees can create expense vouchers - {owner} was provided.")
            
        if term and not isinstance(term, Billterm):
            raise ValueError("Either provide a valid term, or omit.")

        book = book or (owner and owner.book)
        if not book:
            raise ValueError("Could not find a book to attach the invoice to")
        
        #Check valid currency passed in
        if not currency:
            raise ValueError("Need a valid currency for the invoice/bill/expense voucher")
        elif currency and not currency.namespace == 'CURRENCY':
            raise ValueError("Either pass a valid currency, or omit parameter and owner's default currency will be used. Failing that, book's default currency will be used.")  
        
        if currency:
            self.currency = currency
        
        if term:
            self.term = term

        if billing_id:
            self.billing_id = billing_id
            
        self.owner_guid = owner.guid
        self.owner_type = OwnerType[type(owner)]
        self.date_opened = date_opened
        self.notes = notes
        self.active = active
        self.charge_amt = 0
        self._invoice_entries = []
        self._bill_entries = []
        
        if type(owner) is Job:
            self.job = owner
        elif type(owner) is Customer:
            self._customer = owner
        elif type(owner) is Vendor:
            self._vendor = owner
        else:
            self._employee = owner

        if billto:
            self.billto = billto
        
        #Finally, update slot indicating if credit-note or not
        self.is_credit_note = is_credit_note

        book.add(self)

    def on_book_add(self):
        self._assign_id()
            
    # hold the name of the counter to use for id: set by subclasses
    _counter_name = None

    def _assign_id(self):
        if not self.id:
            cnt = getattr(self.book, self._counter_name) + 1
            setattr(self.book, self._counter_name, cnt)
            self.id = "{:06d}".format(cnt)

    @hybrid_property
    def owner(self):
        return self._customer or self._vendor or self._employee or self.job

    @hybrid_property
    def end_owner(self):
        if isinstance(self.owner, Job):
            return self.owner.owner
        else:
            return self.owner

    @property
    def billto(self):
        return self._billto_customer or self._billto_job

    @billto.setter
    def billto(self, billto):
        #Chargeback only available to Vendors and Employees
        if billto and (isinstance(self.owner, Customer) or (isinstance(self.owner, Job) and isinstance(self.owner.owner, Customer))):
            raise ValueError("Customer invoices cannot have chargebacks")

        #Chargeback: can only chargeback to a Customer or a Job belonging to a Customer
        if billto and not (isinstance(billto, Customer) or (isinstance(billto, Job) and isinstance(billto.owner, Customer))):
            raise ValueError(f"Can only charge to a Customer, or a Job belonging to a Customer. {billto} provided.")

        if isinstance(billto, Customer):
            self._billto_customer = billto
        else:
            self._billto_job = billto

        self.billto_type = OwnerType[type(billto)]
        self.billto_guid = billto.guid

    # if the term field is modified, adjust the Billterm.refcount
    def _changed(mapper, connection, target):
        # check if the term field changed, obtain new and old value, and update the refcount for the terms
        newval, _, oldval = get_history(target, 'term')
        if newval and (newval[0] is not None):
            newval[0]._increase_refcount(connection)
        if oldval and (oldval[0] is not None):
            oldval[0]._decrease_refcount(connection)
            
    # if the term field is deleted, adjust the Billterm.refcount
    def _deleted(mapper, connection, target):
        if target.term:
            target.term._decrease_refcount(connection)    
    
    @property
    def tax_per_taxaccount(self):
        # get the taxes for each tax acount
        tax_per_taxaccount = {}
        for entry in self.entries:
            entry_subtotal, entry_tax, entry_tax_per_taxaccount = entry.subtotal_and_tax
            for acct in entry_tax_per_taxaccount:
                tax_per_taxaccount[acct] = tax_per_taxaccount.get(acct, 0) + entry_tax_per_taxaccount[acct]
        return tax_per_taxaccount

    def _accumulate_splits(self, splits):
        #all splits to same account will be collected in a single split
        #only the first split's action, memo, notes, etc. will be preserved
        tmp = {}
        for split in splits:
            if tmp.get(split.account):  
                tmp[split.account].quantity += split.quantity
                tmp[split.account].value += split.value
                split.account = None        #set to None, otherwise unused splits trigger an attribute error
            else:
                tmp[split.account] = split
        return list(tmp.values())

    @property
    def due_date(self):
        if self.post_txn and self.post_txn['trans-date-due']:
            return self.post_txn['trans-date-due'].value
        else:
            return None
            
    def post(self, 
        post_account,                   #account to post to (Receivable for invoices, Payable for bills and expensevouchers. 
        post_date=datetime.datetime.now().replace(microsecond=0), 
        due_date=datetime.datetime.now().replace(microsecond=0),
        description='', 
        accumulate_splits=True,         #whether or not entries should be accumulated by account
        prices=[]):                     #list of Price objects to use if any currency conversion is required. All entry values are in the invoice's currency, but taxes and entries could be to other currencies.
        
        if self.is_posted:
            raise ValueError(f'{self} has already been posted - cannot re-post.')

        if type(self) is Invoice and not post_account.sign == +1:
            raise ValueError(f'Please provide a valid Accounts Receivable - {post_account} provided')
        elif type(self) in [Bill, Expensevoucher] and not post_account.sign == -1:
            raise ValueError(f'Please provide a valid Accounts Payable - {post_account} provided')

        if not post_account.commodity == self.currency:
            raise ValueError(f"Post account currency does not match invoice/bill/expensevoucher currency")

        #prepare a dict of exchange rates to use, if relevant
        price_dict = {}
        for price in prices:
            if price.commodity == self.currency:
                price_dict[price.currency] = price.value
            elif price.currency == self.currency:
                price_dict[price.commodity] = 1/price.value
            else:
                pass    #discard - only support direct conversion for now

        #action
        if self.is_credit_note:
            action = 'Credit Note'
        elif type(self) is Invoice:
            action = 'Invoice'
        elif type(self) is Bill:
            action = 'Bill'
        elif type(self) is Expensevoucher:
            action = 'Expense'

        #taxtables - duplicate referenced taxtables complete with taxtableentries
        taxtables = list(set([entry.taxtable for entry in self.entries if entry.taxtable]))
        for taxtable in taxtables:
            taxtable_clone = taxtable.create_copy_as_child()

        #lot
        lot = Lot(title=action + ' ' + str(self.id), account=post_account, splits=None, is_closed=False)
        self.post_lot = lot
        
        #transaction/splits
            #entries & taxes
        entry_splits = []
        tax_splits = []        
        sign = -post_account.sign

        try:    
            for entry in self.entries:
                entry_subtotal, entry_tax, tax_per_account = entry.subtotal_and_tax
                value = entry_subtotal*sign
                quantity = value*price_dict[entry.account.commodity] if not entry.account.commodity == self.currency else None
                entry_splits.append(Split(entry.account, value=value, quantity=quantity, action=action, memo=description))

                for tax_account in tax_per_account:
                    value = tax_per_account[tax_account]*sign
                    quantity = value*price_dict[tax_account.commodity] if not entry.account.commodity == self.currency else None
                    tax_splits.append(Split(account=tax_account, value=value, quantity=quantity, action=action, memo=description))
        except KeyError as ex:
            raise ValueError(f"Conversion rate not found for {ex.args[0].mnemonic} -> {self.currency.mnemonic} - use the prices parameter")
            
        tax_splits = self._accumulate_splits(tax_splits)    #taxes always accumulated
        if accumulate_splits:
            entry_splits = self._accumulate_splits(entry_splits)
 
        txn = Transaction(self.currency, description=self.owner.name, splits=tax_splits+entry_splits, post_date=post_date.date(), num=self.id)

            #posted account - create a balancing split
        value = -sum([split.value for split in txn.splits])        
        Split(account=post_account, value=value, action=action, lot=lot, transaction=txn, memo=description)

        #slots
        txn['date-posted'] = post_date
        txn['trans-date-due'] = due_date
        txn['trans-read-only'] = 'Generated from an invoice. Try unposting the invoice.'
        txn['trans-txn-type'] = 'I'                         #same irrespective of Invoice/Bill/Expensevoucher
        txn['gncInvoice/invoice-guid'] = self               #same irrespective of Invoice/Bill/Expensevoucher

        lot['gncInvoice/invoice-guid'] = self               #same irrespective of Invoice/Bill/Expensevoucher
               
        #self
        self.date_posted = post_date        
        self.post_account = post_account
        self.post_txn = txn
        self.post_lot = lot

        #lock lot
        lot.is_closed = '-1'
        
class Invoice(InvoiceBase):
    __mapper_args__ = {
        "polymorphic_identity": 2,
    }

    _counter_name = "counter_invoice"
    
    def __str__(self):
        return "Invoice<{}>".format(self.id)

    @classmethod
    def __declare_last__(cls):
        if hasattr(cls, "term"):
            event.listen(cls, "after_insert", cls._changed)
            event.listen(cls, "after_update", cls._changed)
            event.listen(cls, "after_delete", cls._deleted)

    #billto is not available for customer invoices
    def __init__(self, 
        owner,                  #Either a customer (for invoices), vendor (for bills), or employee (for expenses)
        currency,
        date_opened=datetime.datetime.now().replace(microsecond=0), 
        notes='', 
        term=None, 
        billing_id='', 
        book=None, 
        active=True,
        is_credit_note=False):
        
        self._create_invoice(owner=owner, currency=currency, date_opened=date_opened, notes=notes, term=term, billing_id=billing_id, book=book, active=active, billto=None, is_credit_note=is_credit_note)
        
class Bill(InvoiceBase):
    __mapper_args__ = {
        "polymorphic_identity": 4,
    }

    _counter_name = "counter_bill"
    
    def __str__(self):
        return "Bill<{}>".format(self.id)

    @classmethod
    def __declare_last__(cls):
        if hasattr(cls, "term"):
            event.listen(cls, "after_insert", cls._changed)
            event.listen(cls, "after_update", cls._changed)
            event.listen(cls, "after_delete", cls._deleted)

    def __init__(self, 
        owner,                  #Either a customer (for invoices), vendor (for bills), or employee (for expenses)
        currency,
        date_opened=datetime.datetime.now().replace(microsecond=0), 
        notes='', 
        term=None, 
        billing_id='', 
        book=None, 
        active=True,
        billto=None,
        is_credit_note=False):
        
        self._create_invoice(owner=owner, currency=currency, date_opened=date_opened, notes=notes, term=term, billing_id=billing_id, book=book, active=active, billto=billto, is_credit_note=is_credit_note)

class Expensevoucher(InvoiceBase):
    __mapper_args__ = {
        "polymorphic_identity": 5,
    }

    _counter_name = "counter_exp_voucher"

    def __str__(self):
        return "Expensevoucher<{}>".format(self.id)

    @classmethod
    def __declare_last__(cls):
        if hasattr(cls, "term"):
            event.listen(cls, "after_insert", cls._changed)
            event.listen(cls, "after_update", cls._changed)
            event.listen(cls, "after_delete", cls._deleted)

    def __init__(self, 
        owner,                  #Either a customer (for invoices), vendor (for bills), or employee (for expenses)
        currency,
        date_opened=datetime.datetime.now().replace(microsecond=0), 
        notes='', 
        term=None, 
        billing_id='', 
        book=None, 
        active=True,
        billto=None,
        is_credit_note=False):
        
        self._create_invoice(owner=owner, date_opened=date_opened, notes=notes, term=term, billing_id=billing_id, book=book, currency=currency, active=active, billto=billto, is_credit_note=is_credit_note)

# This class exists in code but not in the GUI (to confirm?)


class Order(DeclarativeBaseGuid):
    __tablename__ = "orders"

    __table_args__ = {}

    # column definitions
    id = Column("id", VARCHAR(length=2048), nullable=False)
    notes = Column("notes", VARCHAR(length=2048), nullable=False)
    reference = Column("reference", VARCHAR(length=2048), nullable=False)
    active = Column("active", INTEGER(), nullable=False)

    date_opened = Column("date_opened", _DateTime(), nullable=False)
    date_closed = Column("date_closed", _DateTime(), nullable=False)
    owner_type = Column("owner_type", INTEGER(), nullable=False)
    owner_guid = Column("owner_guid", VARCHAR(length=32), nullable=False)

    # relation definitions
    # todo: owner_guid/type links to Vendor or Customer
    entries = relation(
        "Entry",
        back_populates="order",
        cascade="all, delete-orphan",
        collection_class=CallableList,
    )

OwnerType = PersonType.copy()
OwnerType[Job] = 3
