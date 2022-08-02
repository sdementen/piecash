import uuid
from sqlalchemy import Column, VARCHAR, BIGINT, INTEGER, ForeignKey
from sqlalchemy.orm import relation

from .._common import hybrid_property_gncnumeric, CallableList
from .._declbase import DeclarativeBaseGuid, DeclarativeBase
from ..sa_extra import ChoiceType

from enum import Enum

class DiscountType(Enum):
    value = "VALUE"
    percent = "PERCENT"

class DiscountHow(Enum):
    pretax = "PRETAX"
    sametime = "SAMETIME"
    posttax = "POSTTAX"

class Taxtable(DeclarativeBaseGuid):
    __tablename__ = "taxtables"

    __table_args__ = {}

    # column definitions
    guid = Column(
        "guid",
        VARCHAR(length=32),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex,
    )
    name = Column("name", VARCHAR(length=50), nullable=False)
    refcount = Column("refcount", BIGINT(), nullable=False)
    invisible = Column("invisible", INTEGER(), nullable=False)
    parent_guid = Column("parent", VARCHAR(length=32), ForeignKey("taxtables.guid"))

    # relation definitions
    entries = relation(
        "TaxtableEntry",
        back_populates="taxtable",
        cascade="all, delete-orphan",
        collection_class=CallableList,
    )
    children = relation(
        "Taxtable",
        back_populates="parent",
        cascade="all, delete-orphan",
        collection_class=CallableList,
    )
    parent = relation(
        "Taxtable",
        back_populates="children",
        remote_side=guid,
    )

    def __init__(self, name, entries=None):
        self.name = name
        self.refcount = 0
        self.invisible = 0
        if entries is not None:
            self.entries[:] = entries

    def __str__(self):
        if self.entries:
            return "TaxTable<{}:{}>".format(
                self.name, [te.__str__() for te in self.entries]
            )
        else:
            return "TaxTable<{}>".format(self.name)

    # adjust the refcount field - called by e.g. Entry
    def _increase_refcount(self, connection, increment=1):
        r = connection.execute(
            self.__table__.
            select().
            where(Taxtable.guid == self.guid))
        refcountval = r.fetchone()[2]
        connection.execute(
            self.__table__.
            update().        
            values(refcount=refcountval+increment).
            where(Taxtable.guid == self.guid))
        
    # adjust the refcount field - called by e.g. Entry
    def _decrease_refcount(self, connection):
        self._increase_refcount(connection, increment=-1)
        
    def calculate_subtotal_and_tax(self, quantity, price, i_disc_how, i_disc_type, i_discount, taxincluded):
    # 12 different permutations depending on i_disc_type (2), i_disc_how (3), taxincluded (2)
    # Basically: pretax + tax - discount = subtotal + tax. What varies is the reference for tax computation, and whether the price already includes tax or not
    # The Taxtable may contain multiple TaxtableEntries, each entry either a percent or a value. The tax is then:
    #   tax = sum(tax value) + pretax * sum(tax percent)
        tax = 0
        subtotal = 0
        pretax = 0
        if self.entries:
            # First need sum(tax values) and sum(tax percent)
            sum_tax_value = sum(entry.amount for entry in self.entries if entry.type=="value")
            sum_tax_percent = sum(entry.amount for entry in self.entries if entry.type=="percentage") / 100

            if taxincluded:
                #tax included with price: need to back off the old tax before adding the new tax
                #quantity * price = pretax + tax = pretax + sum_tax_value + pretax * sum_tax_percent = pretax * (1 + sum_tax_percent) + sum_tax_value
                pretax = (quantity * price - sum_tax_value) / (1 + sum_tax_percent)            
            else:
                pretax = quantity * price

            if i_disc_how == DiscountHow.sametime and i_disc_type == DiscountType.percent and taxincluded:
                #tax and discount based on pretax value. 
                tax = sum_tax_value + pretax * sum_tax_percent
                subtotal = pretax * (1 - i_discount/100)
            elif i_disc_how == DiscountHow.sametime and i_disc_type == DiscountType.percent and not taxincluded:
                #pretax value is the price, and discount and tax applied to pretax value
                tax = sum_tax_value + pretax * sum_tax_percent
                subtotal = pretax * (1 - i_discount/100)                
            elif i_disc_how == DiscountHow.sametime and i_disc_type == DiscountType.value and taxincluded:
                #price includes tax, discount and tax applied to pretax value
                tax = sum_tax_value + pretax * sum_tax_percent
                subtotal = pretax - i_discount
            elif i_disc_how == DiscountHow.sametime and i_disc_type == DiscountType.value and not taxincluded:
                subtotal = pretax - i_discount
                tax = sum_tax_value + pretax * sum_tax_percent
            elif i_disc_how == DiscountHow.pretax and i_disc_type == DiscountType.percent and taxincluded:
                #price includes a tax that needs backing off, and tax to be recomputed after discount applied
                subtotal = pretax * (1 - i_discount/100)
                tax = sum_tax_value + subtotal * sum_tax_percent
            elif i_disc_how == DiscountHow.pretax and i_disc_type == DiscountType.percent and not taxincluded:
                #tax based on subtotal (i.e. after discount)
                subtotal = pretax * (1 - i_discount/100)
                tax = sum_tax_value + subtotal * sum_tax_percent
            elif i_disc_how == DiscountHow.pretax and i_disc_type == DiscountType.value and taxincluded:
                #price includes tax that needs backing off, and tax recomputed based on discounted price
                subtotal = pretax - i_discount
                tax = sum_tax_value + subtotal * sum_tax_percent
            elif i_disc_how == DiscountHow.pretax and i_disc_type == DiscountType.value and not taxincluded:
                subtotal = pretax - i_discount
                tax = sum_tax_value + subtotal * sum_tax_percent
            elif i_disc_how == DiscountHow.posttax and i_disc_type == DiscountType.percent and taxincluded:
                #discount applied to pretax + tax
                subtotal = pretax - quantity * price * i_discount/100
                tax = sum_tax_value + pretax * sum_tax_percent
            elif i_disc_how == DiscountHow.posttax and i_disc_type == DiscountType.percent and not taxincluded:
                #discount calculated based on pretax + tax
                tax = sum_tax_value + pretax * sum_tax_percent
                subtotal = pretax - (pretax + tax) * i_discount/100
            elif i_disc_how == DiscountHow.posttax and i_disc_type == DiscountType.value and taxincluded:
                tax = sum_tax_value + pretax * sum_tax_percent
                subtotal = pretax - i_discount
            elif i_disc_how == DiscountHow.posttax and i_disc_type == DiscountType.value and not taxincluded:
                subtotal = pretax - i_discount
                tax = sum_tax_value + pretax * sum_tax_percent
                
        return subtotal, tax
    
class TaxtableEntry(DeclarativeBase):
    __tablename__ = "taxtable_entries"

    __table_args__ = {"sqlite_autoincrement": True}

    # column definitions
    id = Column("id", INTEGER(), primary_key=True, nullable=False, autoincrement=True)
    taxtable_guid = Column(
        "taxtable", VARCHAR(length=32), ForeignKey("taxtables.guid"), nullable=False
    )
    account_guid = Column(
        "account", VARCHAR(length=32), ForeignKey("accounts.guid"), nullable=False
    )
    _amount_num = Column("amount_num", BIGINT(), nullable=False)
    _amount_denom = Column("amount_denom", BIGINT(), nullable=False)
    amount = hybrid_property_gncnumeric(_amount_num, _amount_denom)
    type = Column("type", ChoiceType({1: "value", 2: "percentage"}), nullable=False)

    # relation definitions
    taxtable = relation("Taxtable", back_populates="entries")
    account = relation("Account")

    def __init__(self, type, amount, account, taxtable=None):
        self.type = type
        self.amount = amount
        self.account = account
        if taxtable:
            self.taxtable = taxtable

    def __str__(self):
        return "TaxEntry<{} {} in {}>".format(self.amount, self.type, self.account.name)
