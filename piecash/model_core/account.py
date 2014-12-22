import uuid

from sqlalchemy import Column, VARCHAR, ForeignKey, INTEGER
from sqlalchemy.orm import relation, backref, validates

from ..model_declbase import DeclarativeBaseGuid
from ..model_common import CallableList
from ..sa_extra import mapped_to_slot_property


equity_types = {"EQUITY"}
incexp_types = {"INCOME", "EXPENSE"}
asset_types = {'RECEIVABLE', 'MUTUAL', 'CREDIT', 'CASH', 'LIABILITY', 'PAYABLE', 'ASSET', 'BANK', 'STOCK'}
trading_types = {'TRADING'}
root_types = {"ROOT"}
ACCOUNT_TYPES = equity_types | incexp_types | asset_types | root_types | trading_types


def is_parent_child_account_types_consistent(account_type_parent, account_type_child):
    if account_type_parent in root_types:
        return account_type_child in (ACCOUNT_TYPES - root_types)

    if account_type_child in root_types:
        return account_type_parent is None

    for acc_types in (asset_types, equity_types, incexp_types, trading_types):
        if (account_type_child in acc_types) and (account_type_parent in acc_types):
            return True
    else:
        return False


class Account(DeclarativeBaseGuid):
    __tablename__ = 'accounts'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    account_type = Column('account_type', VARCHAR(length=2048), nullable=False)
    code = Column('code', VARCHAR(length=2048))
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

    description = Column('description', VARCHAR(length=2048))
    hidden = Column('hidden', INTEGER())
    name = Column('name', VARCHAR(length=2048), nullable=False)

    parent_guid = Column('parent_guid', VARCHAR(length=32), ForeignKey('accounts.guid'))
    _placeholder = Column('placeholder', INTEGER())
    placeholder = mapped_to_slot_property(_placeholder, slot_name="placeholder",
                                          slot_transform=lambda v: "true" if v else None)

    # relation definitions
    commodity = relation('Commodity',
                         # single_parent=True,
                         backref=backref('accounts',
                                         cascade='all, delete-orphan',
                                         collection_class=CallableList))
    children = relation('Account',
                        backref=backref('parent', remote_side=guid),
                        cascade='all, delete-orphan',
                        collection_class=CallableList,
    )


    def __init__(self,
                 name,
                 account_type,
                 commodity,
                 parent=None,
                 description=None,
                 commodity_scu=None,
                 hidden=0,
                 placeholder=0,
                 code=None):
        self.name = name
        self.commodity = commodity
        self.account_type = account_type
        self.parent = parent
        self.description = description
        self.hidden = hidden
        self.placeholder = placeholder
        self.code = code
        self.commodity_scu = commodity_scu

    @validates('parent_guid', 'name')
    def validate_account_name(self, key, value):
        name = value if key == 'name' else self.name

        if self.parent:
            for acc in self.parent.children:
                if acc.name == name and acc != self:
                    raise ValueError("{} has two children with the same name {} : {} and {}".format(self.parent, name,
                                                                                                    acc, self))
        return value


    @validates('account_type', 'parent')
    def validate_account_type(self, key, value):
        """Ensure account type is in list
        """
        if key == "account_type":
            if value not in ACCOUNT_TYPES:
                raise ValueError("Account_type '{}' is not in {}".format(value, ACCOUNT_TYPES))

            if self.parent:
                if not is_parent_child_account_types_consistent(self.parent.account_type, value):
                    raise ValueError("Child account_type '{}' is not consistent with parent account_type {}".format(
                        value, self.parent.account_type))

        if (key == "parent") and value and self.account_type:
            if not is_parent_child_account_types_consistent(value.account_type, self.account_type):
                raise ValueError("Child account_type '{}' is not consistent with parent account_type {}".format(
                    self.account_type, value.account_type))

        return value

    @validates('commodity')
    def validate_commodity(self, key, value):
        """Set commodity_scu
        """
        if value is None:
            return
        if self.commodity_scu is None or self.non_std_scu == 0:
            self.commodity_scu = value.fraction

        return value


    def fullname(self):
        if self.name:
            acc = self
            l = []
            while acc:
                l.append(acc.name)
                acc = acc.parent
            return ":".join(l[-2::-1])


    def __repr__(self):
        if self.commodity:
            return "Account<{}[{}]>".format(self.fullname(), self.commodity.mnemonic)
        else:
            return "Account<{}>".format(self.fullname())
