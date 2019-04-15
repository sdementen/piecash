import uuid
from sqlalchemy import Column, VARCHAR, BIGINT, INTEGER, ForeignKey
from sqlalchemy.orm import relation

from .._common import hybrid_property_gncnumeric, CallableList
from .._declbase import DeclarativeBaseGuid, DeclarativeBase
from ..sa_extra import ChoiceType


class Taxtable(DeclarativeBaseGuid):
    __tablename__ = 'taxtables'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = Column('name', VARCHAR(length=50), nullable=False)
    refcount = Column('refcount', BIGINT(), nullable=False)
    invisible = Column('invisible', INTEGER(), nullable=False)
    parent_guid = Column('parent', VARCHAR(length=32), ForeignKey('taxtables.guid'))

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

    def __init__(self, name, entries=None):
        self.name = name
        self.refcount = 0
        self.invisible = 0
        if entries is not None:
            self.entries[:] = entries

    def __str__(self):
        if self.entries:
            return "TaxTable<{}:{}>".format(self.name, [te.__str__() for te in self.entries])
        else:
            return "TaxTable<{}>".format(self.name)


class TaxtableEntry(DeclarativeBase):
    __tablename__ = 'taxtable_entries'

    __table_args__ = {'sqlite_autoincrement': True}

    # column definitions
    id = Column('id', INTEGER(), primary_key=True, nullable=False, autoincrement=True)
    taxtable_guid = Column('taxtable', VARCHAR(length=32),
                           ForeignKey('taxtables.guid'), nullable=False)
    account_guid = Column('account', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False)
    _amount_num = Column('amount_num', BIGINT(), nullable=False)
    _amount_denom = Column('amount_denom', BIGINT(), nullable=False)
    amount = hybrid_property_gncnumeric(_amount_num, _amount_denom)
    type = Column('type', ChoiceType({1: "value", 2: "percentage"}), nullable=False)

    # relation definitions
    taxtable = relation('Taxtable', back_populates='entries')
    account = relation('Account')

    def __init__(self, type, amount, account, taxtable=None):
        self.type = type
        self.amount = amount
        self.account = account
        if taxtable:
            self.taxtable = taxtable

    def __str__(self):
        return "TaxEntry<{} {} in {}>".format(self.amount, self.type, self.account.name)
