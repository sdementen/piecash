from __future__ import division

import uuid

from sqlalchemy import Column, VARCHAR, INTEGER, BIGINT, ForeignKey
from sqlalchemy.orm import relation, foreign

from ._common import hybrid_property_gncnumeric, Recurrence, CallableList
from ._declbase import DeclarativeBaseGuid
from .sa_extra import DeclarativeBase


class Budget(DeclarativeBaseGuid):
    """
    A GnuCash Budget

    Attributes:
        name (str): name of the budget
        description (str): description of the budget
        amounts (list of :class:`piecash.budget.BudgetAmount`): list of amounts per account
    """
    __tablename__ = 'budgets'

    __table_args__ = {}

    # column definitions
    # keep this line as we reference it in the primaryjoin
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = Column('name', VARCHAR(length=2048), nullable=False)
    description = Column('description', VARCHAR(length=2048))
    num_periods = Column('num_periods', INTEGER(), nullable=False)

    # # relation definitions
    recurrence = relation(Recurrence,
                          primaryjoin=foreign(Recurrence.obj_guid) == guid,
                          cascade='all, delete-orphan',
                          uselist=False)

    amounts = relation('BudgetAmount',
                       back_populates="budget",
                       cascade='all, delete-orphan',
                       collection_class=CallableList,
    )


    def __str__(self):
        return "Budget<{}({}) for {} periods following pattern '{}' >".format(self.name, self.description,
                                                                               self.num_periods, self.recurrence)


class BudgetAmount(DeclarativeBase):
    """
    A GnuCash BudgetAmount

    Attributes:
        amount (:class:`decimal.Decimal`): the budgeted amount
        account (:class:`piecash.core.account.Account`): the budgeted account
        budget (:class:`Budget`): the budget of the amount
    """
    __tablename__ = 'budget_amounts'

    __table_args__ = {'sqlite_autoincrement': True}

    # column definitions
    id = Column('id', INTEGER(), primary_key=True, autoincrement=True,nullable=False)
    budget_guid = Column('budget_guid', VARCHAR(length=32),
                         ForeignKey('budgets.guid'), nullable=False)
    account_guid = Column('account_guid', VARCHAR(length=32),
                          ForeignKey('accounts.guid'), nullable=False)
    period_num = Column('period_num', INTEGER(), nullable=False)
    _amount_num = Column('amount_num', BIGINT(), nullable=False)
    _amount_denom = Column('amount_denom', BIGINT(), nullable=False)
    amount = hybrid_property_gncnumeric(_amount_num, _amount_denom)


    # relation definitions
    account = relation('Account', back_populates='budget_amounts')
    budget = relation('Budget', back_populates="amounts")

    def __str__(self):
        return "BudgetAmount<{}={}>".format(self.period_num, self.amount)


