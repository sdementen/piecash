import uuid

from sqlalchemy import Column, VARCHAR, ForeignKey, INTEGER
from sqlalchemy.orm import relation, validates

from .._declbase import DeclarativeBaseGuid
from .._common import CallableList
from ..sa_extra import mapped_to_slot_property
from .book import Book


root_types = {"ROOT"}
asset_types = {'RECEIVABLE', 'MUTUAL', 'CASH', 'ASSET', 'BANK', 'STOCK'}
liability_types = {'CREDIT', 'LIABILITY', 'PAYABLE'}
income_types = {"INCOME"}
expense_types = {"EXPENSE"}
trading_types = {'TRADING'}
equity_types = {"EQUITY"}
# : the different types of accounts
ACCOUNT_TYPES = equity_types | income_types | expense_types | asset_types | liability_types | root_types | trading_types

# types that are compatible with other types
incexp_types = income_types | expense_types
assetliab_types = asset_types | liability_types


# types according to the sign of their balance
positive_types = asset_types | expense_types | trading_types
negative_types = liability_types | income_types | equity_types


def _is_parent_child_types_consistent(type_parent, type_child):
    """
    Return True if the child account is consistent with the parent account in terms of types, i.e.:

    1) if the parent is a root account, child can be anything but a root account
    2) if the child is a root account, it must have no parent account
    3) both parent and child are of the same family (asset, equity, income&expense, trading)

    Arguments
        type_parent(str): the type of the parent account
        type_child(str):  the type of the child account

    Returns
        True if both accounts are consistent, False otherwise
    """
    # TODO: if we want to allow multiple root accounts below the ROOT account, relax constrain
    if type_parent in root_types:
        return type_child in (ACCOUNT_TYPES - root_types)

    if type_child in root_types:
        return type_parent is None

    for acc_types in (assetliab_types, equity_types, incexp_types, trading_types):
        if (type_child in acc_types) and (type_parent in acc_types):
            return True

    return False


class Account(DeclarativeBaseGuid):
    """
    A GnuCash Account which is specified by its name, type and commodity.

    Attributes:
        type (str): type of the Account
        sign (int): 1 for accounts with positive balances, -1 for accounts with negative balances
        code (str): code of the Account
        commodity (:class:`piecash.core.commodity.Commodity`): the commodity of the account
        commodity_scu (int): smallest currency unit for the account
        non_std_scu (int): 1 if the scu of the account is NOT the same as the commodity
        description (str): description of the account
        name (str): name of the account
        fullname (str): full name of the account (including name of parent accounts separated by ':')
        placeholder (int): 1 if the account is a placeholder (should not be involved in transactions)
        hidden (int): 1 if the account is hidden
        is_template (bool): True if the account is a template account (ie commodity=template/template)
        parent (:class:`Account`): the parent account of the account (None for the root account of a book)
        children (list of :class:`Account`): the list of the children accounts
        splits (list of :class:`piecash.core.transaction.Split`): the list of the splits linked to the account
        lots (list of :class:`piecash.business.Lot`): the list of lots to which the account is linked
        book (:class:`piecash.core.book.Book`): the book if the account is the root account (else None)
        budget_amounts (list of :class:`piecash.budget.BudgetAmount`): list of budget amounts of the account
        scheduled_transaction (:class:`piecash.core.transaction.ScheduledTransaction`): scheduled transaction linked to the account
    """
    __tablename__ = 'accounts'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    type = Column('account_type', VARCHAR(length=2048), nullable=False)
    commodity_guid = Column('commodity_guid', VARCHAR(length=32), ForeignKey('commodities.guid'))
    _commodity_scu = Column('commodity_scu', INTEGER(), nullable=False)
    _non_std_scu = Column('non_std_scu', INTEGER(), nullable=False)

    @property
    def non_std_scu(self):
        return self._non_std_scu

    @property
    def commodity_scu(self):
        return self._commodity_scu

    @commodity_scu.setter
    def commodity_scu(self, value):
        if value is None:
            self._non_std_scu = 0
            if self.commodity:
                value = self.commodity.fraction
            else:
                value = 0
        else:
            self._non_std_scu = 1

        self._commodity_scu = value


    parent_guid = Column('parent_guid', VARCHAR(length=32), ForeignKey('accounts.guid'))
    code = Column('code', VARCHAR(length=2048))
    description = Column('description', VARCHAR(length=2048))
    hidden = Column('hidden', INTEGER())
    _placeholder = Column('placeholder', INTEGER())
    placeholder = mapped_to_slot_property(_placeholder, slot_name="placeholder",
                                          slot_transform=lambda v: "true" if v else None)

    # relation definitions
    commodity = relation('Commodity', back_populates='accounts')
    children = relation('Account',
                        back_populates='parent',
                        cascade='all, delete-orphan',
                        collection_class=CallableList,
                        )
    parent = relation('Account',
                      back_populates='children',
                      remote_side=guid,
                      )
    splits = relation('Split',
                      back_populates='account',
                      cascade='all, delete-orphan',
                      collection_class=CallableList,
                      )
    lots = relation('Lot',
                    back_populates='account',
                    cascade='all, delete-orphan',
                    collection_class=CallableList,
                    )
    book = relation('Book',
                    back_populates='root_account',
                    foreign_keys=[Book.root_account_guid],
                    cascade='all, delete-orphan',
                    uselist=False,
                    )
    budget_amounts = relation('BudgetAmount',
                              back_populates='account',
                              cascade='all, delete-orphan',
                              collection_class=CallableList,
                              )
    scheduled_transaction = relation('ScheduledTransaction',
                                     back_populates='template_account',
                                     cascade='all, delete-orphan',
                                     uselist=False,
                                     )


    def __init__(self,
                 name,
                 type,
                 commodity,
                 parent=None,
                 description=None,
                 commodity_scu=None,
                 hidden=0,
                 placeholder=0,
                 code=None):
        self.name = name
        self.commodity = commodity
        self.type = type
        self.parent = parent
        self.description = description
        self.hidden = hidden
        self.placeholder = placeholder
        self.code = code
        self.commodity_scu = commodity_scu

    @validates('parent_guid', 'name')
    def validate_account_name(self, key, value):
        """
        Ensure the account name is unique amongst its sibling accounts
        """
        name = value if key == 'name' else self.name

        if self.parent:
            for acc in self.parent.children:
                if acc.name == name and acc != self:
                    raise ValueError("{} has two children with the same name {} : {} and {}".format(self.parent, name,
                                                                                                    acc, self))
        return value


    @validates('type', 'parent')
    def validate_type(self, key, value):
        """
        Ensure the account type is consistent
        """
        if key == "type":
            if value not in ACCOUNT_TYPES:
                raise ValueError("Account_type '{}' is not in {}".format(value, ACCOUNT_TYPES))

            if self.parent:
                if not _is_parent_child_types_consistent(self.parent.type, value):
                    raise ValueError("Child type '{}' is not consistent with parent type {}".format(
                        value, self.parent.type))

        if (key == "parent") and value and self.type:
            if not _is_parent_child_types_consistent(value.type, self.type):
                raise ValueError("Child type '{}' is not consistent with parent type {}".format(
                    self.type, value.type))

        return value

    @validates('commodity')
    def validate_commodity(self, key, value):
        """
        Ensure update of commodity_scu when commodity is changed
        """
        if value is None:
            return
        if self.commodity_scu is None or self.non_std_scu == 0:
            self.commodity_scu = value.fraction

        return value

    @property
    def fullname(self):
        if self.name:
            acc = self
            l = []
            while acc:
                l.append(acc.name)
                acc = acc.parent
            return ":".join(l[-2::-1])


    def get_balance(self):
        """

        Returns
            the balance of the account
        """
        return sum([sp.value for sp in self.splits]) * self.sign

    @property
    def sign(self):
        return 1 if (self.type in positive_types) else -1

    @property
    def is_template(self):
        return self.commodity.namespace == 'template'

    def __repr__(self):
        if self.commodity:
            return "Account<{}[{}]>".format(self.fullname, self.commodity.mnemonic)
        else:
            return "Account<{}>".format(self.fullname)
