from __future__ import division
import uuid

from sqlalchemy import Column, VARCHAR, INTEGER, BIGINT, ForeignKey
from sqlalchemy.orm import relation, backref, foreign

from .sa_extra import DeclarativeBase
from ._declbase import DeclarativeBaseGuid
from ._common import hybrid_property_gncnumeric, Recurrence, CallableList


class Budget(DeclarativeBaseGuid):
    __tablename__ = 'budgets'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    description = Column('description', VARCHAR(length=2048))
    name = Column('name', VARCHAR(length=2048), nullable=False)
    num_periods = Column('num_periods', INTEGER(), nullable=False)

    # # relation definitions
    recurrence = relation(Recurrence,
                          primaryjoin=foreign(Recurrence.obj_guid) == guid,
                          cascade='all, delete-orphan',
                          uselist=False)

    def __repr__(self):
        return "<Budget {}({}) for {} periods following pattern '{}' >".format(self.name, self.description,
                                                                               self.num_periods, self.recurrence)


class BudgetAmount(DeclarativeBase):
    __tablename__ = 'budget_amounts'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', VARCHAR(length=32),
                          ForeignKey('accounts.guid'), nullable=False)
    _amount_denom = Column('amount_denom', BIGINT(), nullable=False)
    _amount_num = Column('amount_num', BIGINT(), nullable=False)
    _amount_denom_basis = None
    amount = hybrid_property_gncnumeric(_amount_num, _amount_denom)

    budget_guid = Column('budget_guid', VARCHAR(length=32),
                         ForeignKey('budgets.guid'), nullable=False)
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    period_num = Column('period_num', INTEGER(), nullable=False)

    # relation definitions
    account = relation('Account', backref=backref('budget_amounts',
                                                  cascade='all, delete-orphan',
                                                  collection_class=CallableList, ))
    budget = relation('Budget', backref=backref('amounts',
                                                cascade='all, delete-orphan',
                                                collection_class=CallableList, ))

    def __repr__(self):
        return "<BudgetAmount {}={}>".format(self.period_num, self.amount)


