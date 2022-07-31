import uuid
import datetime
from enum import Enum

from sqlalchemy import Column, INTEGER, BIGINT, VARCHAR, ForeignKey, select, case, text, event
from sqlalchemy.orm import composite, relation, column_property
from sqlalchemy.orm.attributes import get_history

from decimal import Decimal

from .person import PersonType, Person, Customer, Vendor, Employee

# change of the __doc__ string as getting error in sphinx ==> should be reported to SA project

composite.__doc__ = None  # composite.__doc__.replace(":ref:`mapper_composite`", "")

from ..sa_extra import _DateTime
from .._common import CallableList, hybrid_property_gncnumeric
from .._declbase import DeclarativeBaseGuid

from ..kvp import SlotInt, SlotString, SlotFrame, SlotDate, SlotNumeric
from ..core.account import Account, income_types, asset_types, expense_types
from .tax import Taxtable
#from ..core.transaction import Transaction, Split, Lot

class DiscountType(Enum):
    value = "VALUE"
    percent = "PERCENT"

class DiscountHow(Enum):
    pretax = "PRETAX"
    sametime = "SAMETIME"
    posttax = "POSTTAX"

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

    # relation definitions
    # todo: owner_guid/type links to Vendor or Customer

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

    # Retrieve the job rate
    @property
    def rate(self):
        rate_lst = [slot for slot in self.slots if slot._name == 'job-rate']
        if len(rate_lst) > 0:
            return rate_lst[0].value
        else:
            return None

    # Create a slot holding the job rate
    @rate.setter
    def rate(self, rateval):
        if rateval:
            self.slots = [SlotNumeric('job-rate', Decimal(rateval))]
        else:
            self.slots = []

    @property
    def _owner_cls_type(self):
        idx = list(PersonType.values()).index(self.owner_type)
        return list(PersonType.keys())[idx]

    @property
    def owner(self):
        return self.book.get(self._owner_cls_type, guid=self.owner_guid)

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

    _i_acct = Column("i_acct", VARCHAR(length=32))
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

    _b_acct = Column("b_acct", VARCHAR(length=32))
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
    _b_taxtable = relation("Taxtable", foreign_keys=[_b_taxtable_guid])
    _i_taxtable = relation("Taxtable", foreign_keys=[_i_taxtable_guid])

    def __str__(self):
        return "Entry<{}>".format(self.description)

    def __init__(self, 
        invoice,                            #Invoice/bill/expense voucher object
        date=datetime.datetime.now().replace(microsecond=0),   #date item was sold
        date_entered=datetime.datetime.now().replace(microsecond=0), 
        description=None,                   #item or service description
        action=None,                        #user-defined field (cost center information), or Hours, Material, Project 
        notes='',                       
        quantity=None,                      #how many items were sold
        price=0,                            #unit price of item. Note: to specify price, an account also needs to be specified.
        acct=None,                          #income account that is to be credited (invoice) / expense account to charged (bill, expense voucher)
        taxable=True,                       #True/1 - yes, False/0 - no. If taxtable is provided, must be True
        taxincluded=False,                  #tax already included in unit price? True/1 - yes, False/0 - no
        taxtable=None,                      #info re tax percentage and account to which tax is charged
        i_discount=None,                    #total discount
        i_disc_type=DiscountType.percent,   #type of discount; VALUE - monetary value, PERCENT - percentage
        i_disc_how=DiscountHow.pretax,      #computation method; POSTTAX - discount after tax, PRETAX - discount before tax, SAMETIME - discount and tax applied to pretax value
        b_paytype=Paytype.cash,             #Cash or credit account. Applicable for employees only, and requires that a credit account has been set for the employee.
        billable=False):                    #True/1 - yes, False/0 - no - only applicable for bills: ignored for invoices and expense vouchers
        
        #order=None                         #There is no mention of orders in the Gnucash user manual, besides a mention under 'Counters'. Some artifact of something started but abandoned?
        #billto=None                        #Can't see that the Gnucash interface allows to set per-entry bill-to(?). Ignore for now.

        #Check that a valid invoice pas provided.
        if not invoice or not type(invoice) in [Invoice, Bill, Expensevoucher]:
            raise ValueError("Please provide a valid Invoice object.")

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
            self.invoice_guid = invoice.guid        

            self.i_discount = i_discount
            self.i_disc_type = i_disc_type
            self.i_disc_how = i_disc_how
        else:
            self.bill_guid = invoice.guid

            self.i_discount = 0
            self.i_disc_type = DiscountType.percent
            self.i_disc_how = DiscountHow.pretax        

        # flush to set the invoice or bill / expense voucher attributes
        book.flush()
    
        self.acct = acct
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
        if (price and price != 0) and not self.acct:
            #Price without account gives an error message in the GUI if one attempts to edit the entry. 
            raise ValueError("To set the price, please set a valid account first.")
        else:
            setattr(self, this_prefix+'price', Decimal(str(price)))

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

    @i_disc_type.setter
    def i_disc_how(self, i_disc_how):
        if i_disc_how in DiscountHow:
            self._i_disc_how = i_disc_how.value
        else:
            raise ValueError(f"Unrecognised value for i_disc_how: - {i_disc_how} was provided")
    
    @property
    def acct(self):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        return getattr(self, this_prefix+'acct')

    @acct.setter
    def acct(self, acct):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        
        setattr(self, other_prefix+'price', None)
        if not acct:
            setattr(self, this_prefix+'price', None)
        elif (type(self.invoice) is Invoice and not (acct.type in asset_types or acct.type in income_types)) or (type(self.invoice) is not Invoice and not acct.type in expense_types):
            raise ValueError("Please provide a valid income or asset account for invoices, or valid expense account for bills and expensevouchers.")
        else:
            setattr(self, this_prefix+'acct', acct.guid)

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

    @property
    def billto(self):
        this_prefix, other_prefix = self._get_entry_field_prefix()
        return self._billto

    @taxincluded.setter
    def taxincluded(self, taxincluded):
        this_prefix, other_prefix = self._get_entry_field_prefix()

        setattr(self, other_prefix+'taxincluded', False)
        setattr(self, this_prefix+'taxincluded', taxincluded)

    
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

class InvoiceBase(DeclarativeBaseGuid):
    """
    - This class is a superclass for Invoices, Bills, and Expense vouchers. 
    - The type of invoice (Invoice, Bill, Expense voucher) is determined by the Owner of the invoice.
        If Owner is a Customer: Invoice
        If Owner is a Vendor: Bill
        If Owner is an Employee: Expense voucher
    - In addition, a Job may be an Owner. Then the Job's Owner (either a Customer or Vendor) determines the type of invoice (Invoice or Bill).

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
    guid = Column(
        "guid",
        VARCHAR(length=32),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex,
    )
    
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
    post_txn_guid = Column("post_txn", VARCHAR(length=32), ForeignKey("lots.guid"))
    post_lot_guid = Column(
        "post_lot", VARCHAR(length=32), ForeignKey("transactions.guid")
    )
    post_acc_guid = Column("post_acc", VARCHAR(length=32), ForeignKey("accounts.guid"))
    billto_type = Column("billto_type", INTEGER())
    billto_guid = Column("billto_guid", VARCHAR(length=32))
    _charge_amt_num = Column("charge_amt_num", BIGINT())
    _charge_amt_denom = Column("charge_amt_denom", BIGINT())
    charge_amt = hybrid_property_gncnumeric(_charge_amt_num, _charge_amt_denom)

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
        back_populates="invoice",
        cascade="all, delete-orphan",
        collection_class=CallableList,
        foreign_keys=Entry.bill_guid
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

    __mapper_args__ = {
        "polymorphic_identity": "invoices",
        "polymorphic_on": _end_owner_type,
    }

    job = relation(Job, uselist=False, primaryjoin='Job.guid == InvoiceBase.owner_guid', foreign_keys=Job.guid)

    @property
    def entries(self):
        if type(self) is Invoice:
            return self._invoice_entries
        elif type(self) in [Bill, Expensevoucher]:
            return self._bill_entries
 
    def _create_invoice(self, 
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
 
        #Although not required to add invoice to the database, the invoice won't be found in the GnuCash GUI without an owner attached
        if not (type(owner) in [Customer, Vendor, Employee, Job]):
            raise ValueError(f'Unknown owner type - {owner}')
        elif type(self) is Invoice and not (type(owner) is Customer or (type(owner) is Job and type(owner.owner) is Customer)):
            raise ValueError(f"Only Customers and Customer Jobs can create invoices - {owner} was provided.")
        elif type(self) is Bill and not (type(owner) is Vendor or (type(owner) is Job and type(owner.owner) is Vendor)):
            raise ValueError(f"Only Vendors and Vendor Jobs can create bills - {owner} was provided.")
        elif type(self) is Expensevoucher and not type(owner) is Employee:
            raise ValueError(f"Only Employees can create expense vouchers - {owner} was provided.")

        #Chargeback only available to Vendors and Employees
        if billto and not (isinstance(owner, Vendor) or isinstance(owner, Employee) or (isinstance(owner, Job) and isinstance(owner.owner, Vendor))):
            raise ValueError("Customer invoices cannot have chargebacks")
            
        #Chargeback: can only chargeback to a Customer or a Job belonging to a Customer
        if billto and not (isinstance(billto, Customer) or (isinstance(billto, Job) and isinstance(billto.owner, Customer))):
            raise ValueError("Either provide a Customer, or a Job belonging to a Customer, or omit.")

        if term and not isinstance(term, Billterm):
            raise ValueError("Either provide a valid term, or omit.")

        book = book or (owner and owner.book)
        if not book:
            raise ValueError("Could not find a book to attach the invoice to")
        
        #Unless a valid currency was passed in, set the invoice currency
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
        self.date_opened = date_opened
        self.notes = notes
        self.active = active
        self.owner_type = OwnerType[type(owner)]
        self.charge_amt = 0
        self._invoice_entries = []
        self._bill_entries = []
        
        if billto:
            self.billto_type = OwnerType[type(billto)]
            self.billto_guid = billto.guid
        
        #Finally, create a slot indicating if credit-note or not
        self.is_credit_note = is_credit_note

        book.add(self)
        book.flush()

    def add_entry(self, entries):
        if type(entries) is list:
            for entry in entries:
                self.entries.append(Entry(self, **entry))
        else:
            self.entries.append(Entry(self, **entries))

    @property
    def is_credit_note(self):
        credit_note_lst = [slot for slot in self.slots if slot._name == 'credit-note']
        if len(credit_note_lst) > 0:
            return credit_note_lst[0].value
        else:
            return False

    @is_credit_note.setter
    def is_credit_note(self, is_credit_note):
        self.slots = [SlotInt('credit-note', is_credit_note)]        

    def on_book_add(self):
        self._assign_id()
            
    # hold the name of the counter to use for id: set by subclasses
    _counter_name = None

    def _assign_id(self):
        if not self.id:
            cnt = getattr(self.book, self._counter_name) + 1
            setattr(self.book, self._counter_name, cnt)
            self.id = "{:06d}".format(cnt)

    @property
    def _owner_cls_type(self):
        idx = list(OwnerType.values()).index(self.owner_type)
        return list(OwnerType.keys())[idx]

    @property
    def owner(self):
        return self.book.get(self._owner_cls_type, guid=self.owner_guid)

    @property
    def _billto_cls_type(self):
        if self.billto_type:
            idx = list(OwnerType.values()).index(self.billto_type)
            clstype = list(OwnerType.keys())[idx]
        else:
            clstype = None
        return clstype

    @property
    def billto(self):
        if self.billto_cls_type:
            return self.book.get(self._billto_cls_type, guid=self.billto_guid)

    @property
    def end_owner(self):
        if isinstance(self.owner, Job):
            return self.owner.owner
        else:
            return self.owner

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

#todo - work in progress !!!!!
##    def post_invoice(self, 
##        post_account, 
##        post_date=datetime.datetime.now().replace(microsecond=0), 
##        due_date=datetime.date.today(),
##        description='', 
##        accumulateSplits=True):
        
        #TODO:
            #slots
            #coded for invoice. Not checked for bills, nor for bills with charge-through.
        
##        self.post_account = post_account
##        self.date_posted = post_date
#        owner = self.get_owner()
##        owner = self.owner()
##        charge_amt = sum(entry.quantity * entry.i_price for entry in self.entries)

#        if len(self.slots) > 0:
#            if self.slots[0].name == 'credit-note' and not self.slots[0].value:
#                if type(owner) == Customer:
#                    action = 'Invoice'
#                else:
#                    action = 'Undefined'
#            else:
#                action = 'Credit note'
##        action = self.get_type_string()

##        if accumulateSplits:
            #check that all entries refer to the same account
##            same_account = all(entry.i_acct == self.entries[0].i_acct for entry in self.entries)

        #prepare splits
##        splits = []
##        if accumulateSplits and same_account:
##            splits.append(Split(
##                account=self.book.get(Account, guid=self.entries[0].i_acct),
##                value=-charge_amt,
##                quantity=-charge_amt,
##                transaction=None,
##                memo=description,
##                action=action,
##                lot=None))
##        else:
##            for entry in self.entries:
##                splits.append(Split(
##                    account=self.book.get(Account, guid=entry.i_acct), 
##                    value=-entry.quantity*entry.i_price,
##                    quantity=-entry.quantity*entry.i_price,      #are these always equal?
##                    transaction=None,
##                    memo=entry.description,
##                    action=action,
##                    lot=None))

            #add balancing split
##        splits.append(Split(post_account,
##                 value=charge_amt,
##                 quantity=charge_amt,
##                 transaction=None,
##                 memo=description,
##                 action=action))

#        self.post_txn = Transaction(self.currency, description=owner.name, notes=None, splits=splits, post_date=post_date.date(), num=self.id)
#        self.post_lot = Lot(title=action + ' ' + str(self.id), account=post_account, splits=[splits[-1]], is_closed=-1)

##        tr = Transaction(self.currency, description=owner.name, notes=None, splits=splits, post_date=post_date.date(), num=self.id)
##        lot = Lot(title=action + ' ' + str(self.id), account=post_account, splits=[splits[-1]], is_closed=-1)
##        self.book.add(tr)
##        self.book.add(lot)
##        self.book.flush()

##        self.post_txn_guid = tr.guid
##        self.post_lot_guid = lot.guid
        
#        self.post_txn.slots = 
#        from pprint import pprint
#        pprint(vars(self.post_txn.slots[0]))
#        self.post_txn.slots = [
#            SlotDate('date-posted', post_date)
#            ]

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
