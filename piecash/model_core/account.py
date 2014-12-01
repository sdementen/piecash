from sqlalchemy import Column, VARCHAR, ForeignKey, INTEGER
from sqlalchemy.orm import relation, backref, validates

from ..model_common import DeclarativeBaseGuid
from piecash.sa_extra import CallableList


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
    account_type = Column('account_type', VARCHAR(length=2048), nullable=False)
    code = Column('code', VARCHAR(length=2048))
    commodity_guid = Column('commodity_guid', VARCHAR(length=32), ForeignKey('commodities.guid'))
    _commodity_scu = Column('commodity_scu', INTEGER(), nullable=False)
    @property
    def commodity_scu(self):
        return self._commodity_scu
    @commodity_scu.setter
    def commodity_scu(self, value):
        self._commodity_scu  = value
        self.non_std_scu = (self.commodity is not None) and (self.commodity.fraction != value)

    description = Column('description', VARCHAR(length=2048))
    guid = DeclarativeBaseGuid.guid
    hidden = Column('hidden', INTEGER(), default=0)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    non_std_scu = Column('non_std_scu', INTEGER(), nullable=False)

    parent_guid = Column('parent_guid', VARCHAR(length=32), ForeignKey('accounts.guid'))
    placeholder = Column('placeholder', INTEGER(), default=0)

    # relation definitions
    commodity = relation('Commodity', backref=backref('accounts',
                                                      cascade='all, delete-orphan',
                                                      collection_class=CallableList))
    children = relation('Account',
                        backref=backref('parent', remote_side=guid),
                        cascade='all, delete-orphan',
                        collection_class=CallableList,
    )


    def __init__(self, *args, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        if "commodity_scu" not in kwargs:
            self.commodity_scu = 100

    @validates('parent_guid', 'name')
    def validate_account_name(self, key, value):
        name = value if key == 'name' else self.name

        if self.parent:
            for acc in self.parent.children:
                if acc.name == name and acc != self:
                    print name, self.parent
                    print acc.name, acc.parent
                    raise ValueError, "{} has two children with the same name {} : {} and {}".format(self.parent, name,
                                                                                                     acc, self)
        return value


    @validates('account_type', 'parent')
    def validate_account_type(self, key, value):
        """Ensure account type is in list
        """
        if key == "account_type":
            if value not in ACCOUNT_TYPES:
                raise ValueError, "Account_type '{}' is not in {}".format(value, ACCOUNT_TYPES)

            if self.parent:
                if not is_parent_child_account_types_consistent(self.parent.account_type, value):
                    raise ValueError, "Child account_type '{}' is not consistent with parent account_type {}".format(
                        value, self.parent.account_type)

        if (key == "parent") and self.account_type:
            if not is_parent_child_account_types_consistent(value.account_type, self.account_type):
                raise ValueError, "Child account_type '{}' is not consistent with parent account_type {}".format(
                    self.account_type, value.account_type)

        return value

    @validates('placeholder')
    def validate_placeholder(self, key, placeholder):
        """Add placeholder as slot and convert to 1/0
        """
        if placeholder:
            self["placeholder"] = "true"
            return 1
        else:
            if "placeholder" in self:
                del self["placeholder"]
            return 0


    @validates('commodity')
    def validate_commodity(self, key, value):
        """Set commodity_scu
        """
        if value is None:
            return
        if self.commodity_scu is None or self.non_std_scu==0:
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
        return "Account<{}>".format(self.fullname())