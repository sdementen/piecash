from decimal import Decimal
import datetime

from sqlalchemy import Column, VARCHAR, ForeignKey, BIGINT, event, INTEGER

from sqlalchemy.orm import relation, validates
from sqlalchemy.orm.base import instance_state
from sqlalchemy.orm.exc import NoResultFound

from .._common import GncValidationError, hybrid_property_gncnumeric

from .._declbase import DeclarativeBaseGuid
from .._common import CallableList
from ..sa_extra import _Date, _DateTime, Session, mapped_to_slot_property, pure_slot_property
from .book import Book
from .account import Account


"""
Examples of transaction and splits (with value and quantity) for several transactions,
some mono-currency (in default or foreign currency), some multi-currency

Commodity<CURRENCY:EUR>    salary
    [Commodity<CURRENCY:EUR>] -1000 / -1000 for Account<Income>
    [Commodity<CURRENCY:EUR>] 1000 / 1000 for Account<Assets:Current Assets:Checking Account>
Commodity<CURRENCY:EUR>    transfert to US account
    [Commodity<CURRENCY:EUR>] -400 / -400 for Account<Assets:Current Assets:Checking Account>
    [Commodity<CURRENCY:USD>] 400 / 448.15 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:USD>] -400 / -448.15 for Account<Trading:CURRENCY:USD>
    [Commodity<CURRENCY:EUR>] 400 / 400 for Account<Trading:CURRENCY:EUR>
Commodity<CURRENCY:EUR>    other transfer + expense
    [Commodity<CURRENCY:EUR>] -210 / -210 for Account<Assets:Current Assets:Checking Account>
    [Commodity<CURRENCY:USD>] 182.85 / 213.21 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:USD>] -182.85 / -213.21 for Account<Trading:CURRENCY:USD>
    [Commodity<CURRENCY:EUR>] 182.85 / 182.85 for Account<Trading:CURRENCY:EUR>
    [Commodity<CURRENCY:EUR>] 17.15 / 17.15 for Account<Expenses>
    [Commodity<CURRENCY:EUR>] 10 / 10 for Account<Imbalance-EUR>
Commodity<CURRENCY:USD>    bonus
    [Commodity<CURRENCY:USD>] -150 / -150 for Account<Income:income in usd>
    [Commodity<CURRENCY:USD>] 150 / 150 for Account<Assets:Current Assets:CheckAcc USD>
Commodity<CURRENCY:USD>    retransfer
    [Commodity<CURRENCY:USD>] -100 / -100 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:EUR>] 100 / 90 for Account<Assets:Current Assets:Checking Account>
    [Commodity<CURRENCY:EUR>] -100 / -90 for Account<Trading:CURRENCY:EUR>
    [Commodity<CURRENCY:USD>] 100 / 100 for Account<Trading:CURRENCY:USD>
Commodity<CURRENCY:CAD>    cross CAD to USD transfer
    [Commodity<CURRENCY:CAD>] 30 / 30 for Account<Assets:Current Assets:CheckAcc CAD>
    [Commodity<CURRENCY:USD>] -30 / -26.27 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:USD>] 30 / 26.27 for Account<Trading:CURRENCY:USD>
    [Commodity<CURRENCY:CAD>] -30 / -30 for Account<Trading:CURRENCY:CAD>
Commodity<CURRENCY:USD>    cross CAD to USD transfer (initiated from USD account)
    [Commodity<CURRENCY:USD>] -26.27 / -26.27 for Account<Assets:Current Assets:CheckAcc USD>
    [Commodity<CURRENCY:CAD>] 26.27 / 30 for Account<Assets:Current Assets:CheckAcc CAD>
    [Commodity<CURRENCY:CAD>] -26.27 / -30 for Account<Trading:CURRENCY:CAD>
    [Commodity<CURRENCY:USD>] 26.27 / 26.27 for Account<Trading:CURRENCY:USD>
    """


class Split(DeclarativeBaseGuid):
    """
    A GnuCash Split.

    Attributes:
        transaction(:class:`piecash.core.transaction.Transaction`): transaction of the split
        account(:class:`piecash.core.account.Account`): account of the split
        lot(:class:`piecash.business.Lot`): lot to which the split pertains
        memo(str): memo of the split
        value(:class:`decimal.Decimal`): amount express in the currency of the transaction of the split
        quantity(:class:`decimal.Decimal`): amount express in the commodity of the account of the split
        reconcile_state(str): 'n', 'c' or 'y'
        reconcile_date(:class:`datetime.datetime`): time
        action(str): new in GnuCash 2.6. usage not yet understood
    """
    __tablename__ = 'splits'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False, index=True)
    action = Column('action', VARCHAR(length=2048), nullable=False, default="")
    lot_guid = Column('lot_guid', VARCHAR(length=32), ForeignKey('lots.guid'))
    memo = Column('memo', VARCHAR(length=2048), nullable=False, default="")

    _quantity_denom = Column('quantity_denom', BIGINT(), nullable=False)
    _quantity_denom_basis = None
    _quantity_num = Column('quantity_num', BIGINT(), nullable=False)
    quantity = hybrid_property_gncnumeric(_quantity_num, _quantity_denom)

    reconcile_date = Column('reconcile_date', _DateTime())
    reconcile_state = Column('reconcile_state', VARCHAR(length=1), nullable=False, default="n")
    tx_guid = Column('tx_guid', VARCHAR(length=32), ForeignKey('transactions.guid'), nullable=False, index=True)

    _value_denom = Column('value_denom', BIGINT(), nullable=False)
    _value_num = Column('value_num', BIGINT(), nullable=False)
    _value_denom_basis = None
    value = hybrid_property_gncnumeric(_value_num, _value_denom)

    # relation definitions
    account = relation('Account', back_populates='splits')
    lot = relation('Lot', back_populates='splits')
    transaction = relation('Transaction', back_populates='splits')

    def __init__(self,
                 account=None,
                 value=0,
                 quantity=0,
                 transaction=None,
                 memo="",
                 reconcile_date=None,
                 reconcile_state="n",
                 lot=None,
    ):
        self.transaction = transaction
        self.account = account
        self.value = value
        self.quantity = quantity
        self.memo = memo
        self.reconcile_date = reconcile_date
        self.reconcile_state = reconcile_state
        self.lot = lot

    def __repr__(self):
        try:
            cur = self.transaction.currency.mnemonic
            acc = self.account
            com = acc.commodity.mnemonic
            if cur == com:
                return "<Split {} {} {}>".format(acc,
                                                 self.value, cur)
            else:
                return "<Split {} {} {} [{} {}]>".format(acc,
                                                         self.value, cur,
                                                         self.quantity, com)
        except AttributeError:
            return "<Split {}>".format(self.account)

    @validates("transaction", "account")
    def set_denom_basis(self, key, value):
        if value is None:
            return value
        if key == "transaction":
            self._value_denom_basis = value.currency.fraction
            self.value = self.value
            trx = value
            acc = self.account
        if key == "account":
            # check that account is not a placeholder
            if value.placeholder != 0:
                raise ValueError("Account {} is a placeholder (or unknown)".format(value))

            # if the account is already defined
            if self.account:
                # check that we keep the same commodity across the account change
                if self.account.commodity != value.commodity:
                    raise GncValidationError(
                        "The commodity of the new account of this split is not the same as the old account")
                if self.account.commodity_scu > value.commodity_scu:
                    raise GncValidationError(
                        "The commodity_scu of the new account of this split is lower than the one of the old account")

            self._quantity_denom_basis = value.commodity_scu
            self.quantity = self.quantity
            trx = self.transaction
            acc = value

        if trx and acc:
            if trx.currency == acc.commodity:
                self.quantity = self.value
                # if the quantity has different rounding that value, then reassign the quantity to the value
                if self.quantity != self.value:
                    self.value = self.quantity

        return value


class Transaction(DeclarativeBaseGuid):
    """
    A GnuCash Transaction.

    Attributes:
        currency (:class:`piecash.core.commodity.Commodity`): currency of the transaction. This attribute is
            write-once (i.e. one cannot change it after being set)
        description (str): description of the transaction
        enter_date (:class:`datetime.datetime`): time at which transaction is entered
        post_date (:class:`datetime.datetime`): day on which transaction is posted
        num (str): user provided transaction number
        splits (list of :class:`Split`): list of the splits of the transaction
    """
    __tablename__ = 'transactions'

    __table_args__ = {}

    # column definitions
    currency_guid = Column('currency_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    description = Column('description', VARCHAR(length=2048))
    enter_date = Column('enter_date', _DateTime)
    num = Column('num', VARCHAR(length=2048), nullable=False)
    _post_date = Column('post_date', _DateTime, index=True)
    post_date = mapped_to_slot_property(_post_date,
                                        slot_name="date-posted",
                                        slot_transform=lambda x: x.date() if x else None)
    scheduled_transaction = pure_slot_property('from-sched-xaction')

    # relation definitions
    currency = relation('Commodity',
                        back_populates='transactions',
    )
    splits = relation('Split',
                      back_populates="transaction",
                      single_parent=True,
                      cascade='all, delete-orphan',
                      collection_class=CallableList,
    )


    def __init__(self,
                 currency,
                 description="",
                 splits=None,
                 enter_date=None,
                 post_date=None,
                 num="",
    ):
        self.currency = currency
        self.description = description
        self.enter_date = enter_date if enter_date else datetime.datetime.today()
        self.post_date = post_date if post_date \
            else datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        self.num = num
        if splits:
            self.splits = splits


    @validates("currency")
    def validate_currency(self, key, value):
        if value is not None and value.namespace != "CURRENCY":
            raise GncValidationError("You are assigning a non currency commodity to a transaction")
        return value

    def validate(self, session):
        old = instance_state(self).committed_state

        # check all accounts related to the splits of the transaction are not placeholder(=frozen)
        for sp in self.splits:
            if sp.account.placeholder != 0:
                raise GncValidationError("Account '{}' used in the transaction is a placeholder".format(sp.account))

        # check same currency
        if "currency" in old and old["currency"] is not None:
            raise GncValidationError("You cannot change the currency of a transaction once it has been set")

        # validate the splits
        if "splits" in old:
            imbalance = Decimal(0)
            c = self.currency
            for sp in self.splits:
                if sp.account.commodity != c:
                    raise GncValidationError("Only single currency transactions are supported")

                sp.quantity = sp.value
                if sp.quantity != sp.value:
                    sp.value = sp.quantity

                imbalance += sp.value

            # if there is an imbalance, add an imbalance split to the transaction
            if imbalance:
                # retrieve imbalance account
                imb_acc_name = "Imbalance-{}".format(c.mnemonic)
                try:
                    acc = session.query(Account).filter_by(name=imb_acc_name).one()
                except NoResultFound:
                    book = session.query(Book).one()
                    acc = Account(name=imb_acc_name,
                                  parent=book.root_account,
                                  commodity=c,
                                  type="BANK")

                Split(value=-imbalance,
                      quantity=-imbalance,
                      account=acc,
                      transaction=self)


    @classmethod
    def single_transaction(cls,
                           post_date,
                           enter_date,
                           description,
                           value,
                           from_account,
                           to_account):
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
                Split(account=from_account, value=-value),
                Split(account=to_account, value=value),
            ])
        return tx

    def __repr__(self):
        return "<Transaction in {} on {} ({})>".format(self.currency, self.post_date, self.enter_date)


@event.listens_for(Session, 'before_flush')
def set_imbalance_on_transaction(session, flush_context, instances):
    # identify transactions to verify
    txs = set()
    for o in session.dirty:
        if isinstance(o, Transaction):
            txs.add(o)
        if isinstance(o, Split):
            txs.add(o.transaction)
    txs = txs.union(o for o in session.new if isinstance(o, Transaction))

    # for each transaction, validate the transaction
    for tx in txs:
        tx.validate(session)


class ScheduledTransaction(DeclarativeBaseGuid):
    __tablename__ = 'schedxactions'

    __table_args__ = {}

    # column definitions
    adv_creation = Column('adv_creation', INTEGER(), nullable=False)
    adv_notify = Column('adv_notify', INTEGER(), nullable=False)
    auto_create = Column('auto_create', INTEGER(), nullable=False)
    auto_notify = Column('auto_notify', INTEGER(), nullable=False)
    enabled = Column('enabled', INTEGER(), nullable=False)
    end_date = Column('end_date', _Date())
    instance_count = Column('instance_count', INTEGER(), nullable=False)
    last_occur = Column('last_occur', _Date())
    name = Column('name', VARCHAR(length=2048))
    num_occur = Column('num_occur', INTEGER(), nullable=False)
    rem_occur = Column('rem_occur', INTEGER(), nullable=False)
    start_date = Column('start_date', _Date())
    template_act_guid = Column('template_act_guid', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False)

    # relation definitions
    template_act = relation('Account')  # todo: add a backref/back_populates ?