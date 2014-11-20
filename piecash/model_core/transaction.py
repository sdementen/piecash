from decimal import Decimal
import decimal

from sqlalchemy import Column, VARCHAR, ForeignKey, BIGINT, cast, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relation, backref, validates

from ..kvp import KVP_Type
from ..model_common import DeclarativeBaseGuid
from ..sa_extra import _DateTime


class Split(DeclarativeBaseGuid):
    __tablename__ = 'splits'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False, index=True)
    action = Column('action', VARCHAR(length=2048), nullable=False)
    # guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False)
    lot_guid = Column('lot_guid', VARCHAR(length=32), ForeignKey('lots.guid'))
    memo = Column('memo', VARCHAR(length=2048), nullable=False)

    quantity_denom = Column('quantity_denom', BIGINT(), nullable=False)
    quantity_num = Column('quantity_num', BIGINT(), nullable=False)

    def fset(self, d):
        _, _, exp = d.as_tuple()
        self.quantity_denom = denom = int(d.radix() ** (-exp))
        self.quantity_num = int(d * denom)

    quantity = hybrid_property(
        fget=lambda self: decimal.Decimal(self.quantity_num) / decimal.Decimal(self.quantity_denom),
        fset=fset,
        expr=lambda cls: cast(cls.quantity_num, Float) / cls.quantity_denom,
    )
    reconcile_date = Column('reconcile_date', _DateTime())
    reconcile_state = Column('reconcile_state', VARCHAR(length=1), nullable=False)
    tx_guid = Column('tx_guid', VARCHAR(length=32), ForeignKey('transactions.guid'), nullable=False, index=True)

    value_denom = Column('value_denom', BIGINT(), nullable=False)
    value_num = Column('value_num', BIGINT(), nullable=False)

    def fset(self, d):
        _, _, exp = d.as_tuple()
        self.value_denom = denom = int(d.radix() ** (-exp))
        self.value_num = int(d * denom)

    value = hybrid_property(
        fget=lambda self: decimal.Decimal(self.value_num) / decimal.Decimal(self.value_denom),
        fset=fset,
        expr=lambda cls: cast(cls.value_num, Float) / cls.value_denom,
    )

    # relation definitions
    account = relation('Account', backref=backref('splits', cascade='all, delete-orphan'))
    lot = relation('Lot', backref="splits")

    def __repr__(self):
        return "<Split {} {}>".format(self.account, self.value)


class Transaction(DeclarativeBaseGuid):
    __tablename__ = 'transactions'

    __table_args__ = {}

    # column definitions
    currency_guid = Column('currency_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    description = Column('description', VARCHAR(length=2048))
    enter_date = Column('enter_date', _DateTime)
    num = Column('num', VARCHAR(length=2048), nullable=False)
    post_date = Column('post_date', _DateTime, index=True)
    splits = relation(Split, backref='transaction',
                      cascade='all, delete-orphan')


    # relation definitions
    currency = relation('Commodity', backref=backref('transactions', cascade='all, delete-orphan'))

    # definition of fields accessible through the kvp system
    _kvp_slots = {
        "notes": KVP_Type.KVP_TYPE_STRING,
        "date-posted": KVP_Type.KVP_TYPE_GDATE,
    }

    @validates('post_date')
    def validate_post_date(self, key, post_date):
        """Add date-posted as slot
        """
        self.set_kvp("date-posted", post_date)
        return post_date


    @classmethod
    def single_transaction(cls,
                           post_date,
                           enter_date,
                           description,
                           value,
                           currency,
                           from_account,
                           to_account):
        amount100 = int(Decimal(value) * 100)

        tx = Transaction(
            currency=currency,
            post_date=post_date,
            enter_date=enter_date,
            description=description,
            num="",
            splits=[
                Split(
                    account=from_account,
                    reconcile_state='n',
                    value_num=-amount100,
                    value_denom=100,
                    quantity_num=-amount100,
                    quantity_denom=100,
                    memo="",
                    action="",
                ), Split(
                    account=to_account,
                    reconcile_state='n',
                    value_num=amount100,
                    value_denom=100,
                    quantity_num=amount100,
                    quantity_denom=100,
                    memo="",
                    action="",
                )])
        return tx

    # > I'm looking at the XML of my gnucash file and was wondering about the
    # > <split:value> and <split:quantity> fields.
    # > I'm taking a guess but it seems that <split:value> is in the currency
    # > of of the transaction <trn:currency> and
    # > that <split:quantity> is in the currency of the account associated to
    # > the split (<split:account>)

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

