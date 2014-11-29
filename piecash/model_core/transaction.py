from decimal import Decimal

from sqlalchemy import Column, VARCHAR, ForeignKey, BIGINT, cast, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relation, backref, validates

from ..model_common import DeclarativeBaseGuid
from ..sa_extra import _DateTime, CallableList


class Split(DeclarativeBaseGuid):
    __tablename__ = 'splits'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False, index=True)
    action = Column('action', VARCHAR(length=2048), nullable=False, default="")
    lot_guid = Column('lot_guid', VARCHAR(length=32), ForeignKey('lots.guid'))
    memo = Column('memo', VARCHAR(length=2048), nullable=False, default="")

    quantity_denom = Column('quantity_denom', BIGINT(), nullable=False)
    quantity_num = Column('quantity_num', BIGINT(), nullable=False)

    def fset(self, d):
        if isinstance(d, Decimal):
            _, _, exp = d.as_tuple()
            denom = int(d.radix() ** (-exp))
            d = int(d * denom), denom

        self.quantity_num, self.quantity_denom = d
        if self.transaction and self.account:
            if self.transaction.currency == self.account.commodity and self.value != d:
                self.value = d

    quantity = hybrid_property(
        fget=lambda self: (self.quantity_num, self.quantity_denom),
        fset=fset,
        expr=lambda cls: cast(cls.quantity_num, Float) / cls.quantity_denom,
    )
    reconcile_date = Column('reconcile_date', _DateTime())
    reconcile_state = Column('reconcile_state', VARCHAR(length=1), nullable=False, default="n")
    tx_guid = Column('tx_guid', VARCHAR(length=32), ForeignKey('transactions.guid'), nullable=False, index=True)

    value_denom = Column('value_denom', BIGINT(), nullable=False)
    value_num = Column('value_num', BIGINT(), nullable=False)

    def fset(self, d):
        if isinstance(d, Decimal):
            _, _, exp = d.as_tuple()
            denom = int(d.radix() ** (-exp))
            d = int(d * denom), denom

        self.value_num, self.value_denom = d

        if self.transaction and self.account:
            if self.transaction.currency == self.account.commodity and self.quantity != d:
                self.quantity = d

    value = hybrid_property(
        fget=lambda self: (self.value_num, self.value_denom),
        fset=fset,
        expr=lambda cls: cast(cls.value_num, Float) / cls.value_denom,
    )

    # relation definitions
    account = relation('Account', backref=backref('splits',
                                                  cascade='all, delete-orphan',
                                                  collection_class=CallableList,
    ))
    lot = relation('Lot', backref=backref('splits',
                                          cascade='all, delete-orphan',
                                          collection_class=CallableList,
    ))

    def __repr__(self):
        return "<Split {} {}>".format(self.account, self.value)


    @validates("transaction", "account")
    def sync_value_amount(self, key, value):
        acc = self.account
        trx = self.transaction
        if "transaction" == key:
            trx = value
        if "account" == key:
            acc = value

        if acc and trx:
            if trx.currency == acc.commodity:
                if self.value:
                    self.quantity = self.value
                elif self.quantity:
                    self.value = self.quantity

        return value


class Transaction(DeclarativeBaseGuid):
    __tablename__ = 'transactions'

    __table_args__ = {}

    # column definitions
    currency_guid = Column('currency_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    description = Column('description', VARCHAR(length=2048))
    enter_date = Column('enter_date', _DateTime)
    num = Column('num', VARCHAR(length=2048), nullable=False, default="")
    post_date = Column('post_date', _DateTime, index=True)
    splits = relation(Split,
                      backref='transaction',
                      cascade='all, delete-orphan',
                      collection_class=CallableList,
    )


    # relation definitions
    currency = relation('Commodity', backref=backref('transactions',
                                                     cascade='all, delete-orphan',
                                                     collection_class=CallableList,
    ))

    @validates('post_date')
    def validate_post_date(self, key, post_date):
        """Add date-posted as slot
        """
        if post_date:
            self["date-posted"] = post_date
        return post_date


    @classmethod
    def single_transaction(cls,
                           post_date,
                           enter_date,
                           description,
                           value,
                           from_account,
                           to_account):
        num, denom = value
        # currency is derived from "from_account" (as in GUI)
        currency = from_account.commodity
        # currency of other destination account should be identical (as only one value given)
        assert currency == to_account.commodity, "Commodities of accounts should be the same"
        tx = Transaction(
            currency=currency,
            post_date=post_date,
            enter_date=enter_date,
            description=description,
            splits=[
                Split(account=from_account, value=(-num, denom)),
                Split(account=to_account, value=(num, denom)),
            ])
        return tx

    @classmethod
    def stock_transaction(cls,
                          post_date,
                          enter_date,
                          description,
                          order,
                          amount,
                          quantity,
                          unit_price,
                          currency,
                          broker_account,
                          stock_account,
                          commission_account):
        amount100 = int(amount * 100)
        quantity = int(quantity)
        commission100 = int((amount - quantity * unit_price) * 100)
        assert (order == "buy" and commission100 >= 0) or (
            order == "sell" and commission100 <= 0), "{} {} {} {}".format(order, commission100, amount,
                                                                          quantity * unit_price)

        # print broker_account, stock_account
        # print amount100, commission100,
        tx = Transaction(currency=currency,
                         post_date=post_date,
                         enter_date=enter_date,
                         description=description,
                         num="",
                         splits=[Split(account=broker_account,
                                       reconcile_state='n',
                                       value_num=-amount100 if order == "buy" else amount100 - commission100,
                                       value_denom=100,
                                       quantity_num=-amount100 if order == "buy" else amount100 - commission100,
                                       quantity_denom=100,
                                       memo="",
                                       action="",
                         ),
                                 Split(account=stock_account,
                                       reconcile_state='n',
                                       value_num=(+amount100 - commission100) if order == "buy" else -amount100,
                                       value_denom=100,
                                       quantity_num=quantity if order == "buy" else -quantity,
                                       quantity_denom=1,
                                       memo="",
                                       action="",
                                 )] + ([Split(account=commission_account,
                                              reconcile_state='n',
                                              value_num=(commission100),
                                              value_denom=100,
                                              quantity_num=(commission100),
                                              quantity_denom=1,
                                              memo="",
                                              action="",
                         )] if unit_price else []))
        return tx

