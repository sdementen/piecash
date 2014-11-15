import decimal
from sqlalchemy import Column, TEXT, INTEGER, BIGINT, ForeignKey, cast, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relation, backref

from .model_common import DeclarativeBaseGuid, _Date, dict_decimal


class Budget(DeclarativeBaseGuid):
    __tablename__ = 'budgets'

    __table_args__ = {}

    # column definitions
    description = Column('description', TEXT(length=2048))
    name = Column('name', TEXT(length=2048), nullable=False)
    num_periods = Column('num_periods', INTEGER(), nullable=False)

    # relation definitions


class BudgetAmount(DeclarativeBaseGuid):
    __tablename__ = 'budget_amounts'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', TEXT(length=32),
                          ForeignKey('accounts.guid'), nullable=False)
    amount_denom = Column('amount_denom', BIGINT(), nullable=False)
    amount_num = Column('amount_num', BIGINT(), nullable=False)
    def fset(self, d):
        _, _, exp = d.as_tuple()
        self.amount_denom = denom = int(d.radix() ** (-exp))
        self.amount_num = int(d * denom)
    amount = hybrid_property(
        fget=lambda self: decimal.Decimal(self.amount_num) / decimal.Decimal(self.amount_denom),
        fset=fset,
        expr=lambda cls: cast(cls.amount_num, Float) / cls.amount_denom,
    )
    budget_guid = Column('budget_guid', TEXT(length=32),
                         ForeignKey('budgets.guid'), nullable=False)
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    period_num = Column('period_num', INTEGER(), nullable=False)

    # relation definitions
    account = relation('Account', backref=backref('budget_amounts', cascade='all, delete-orphan'))
    budget = relation('Budget', backref=backref('amounts', cascade='all, delete-orphan'))


class Recurrence(DeclarativeBaseGuid):
    __tablename__ = 'recurrences'

    __table_args__ = {}

    # column definitions
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    obj_guid = Column('obj_guid', TEXT(length=32), nullable=False)
    recurrence_mult = Column('recurrence_mult', INTEGER(), nullable=False)
    recurrence_period_start = Column('recurrence_period_start', _Date(), nullable=False)
    recurrence_period_type = Column('recurrence_period_type', TEXT(length=2048), nullable=False)
    recurrence_weekend_adjust = Column('recurrence_weekend_adjust', TEXT(length=2048), nullable=False)

    #relation definitions
