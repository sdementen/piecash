import datetime
import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import Column, VARCHAR, ForeignKey, BIGINT, INTEGER
from sqlalchemy.orm import relation, validates, foreign
from sqlalchemy.orm.base import NEVER_SET

from .._common import CallableList, GncImbalanceError
from .._common import GncValidationError, hybrid_property_gncnumeric, Recurrence
from .._declbase import DeclarativeBaseGuid
from ..sa_extra import _Date, _DateTime, mapped_to_slot_property, pure_slot_property


class Split(DeclarativeBaseGuid):
    """
    A GnuCash Split.

    .. note::

        A split used in a scheduled transaction has its main attributes in form of slots.

    Attributes:
        transaction(:class:`piecash.core.transaction.Transaction`): transaction of the split
        account(:class:`piecash.core.account.Account`): account of the split
        lot(:class:`piecash.business.Lot`): lot to which the split pertains
        memo(str): memo of the split
        value(:class:`decimal.Decimal`): amount express in the currency of the transaction of the split
        quantity(:class:`decimal.Decimal`): amount express in the commodity of the account of the split
        reconcile_state(str): 'n', 'c' or 'y'
        reconcile_date(:class:`datetime.datetime`): time
        action(str): describe the type of action behind the split (free form string but with dropdown in the GUI
    """
    __tablename__ = 'splits'

    __table_args__ = {}

    # column definitions
    # the transaction_guid is not mandatory at construction time because it can be set through a tr.splits.append(...) operation
    # however, in the validation of the object, we raise an error if there is no transaction set at that time
    transaction_guid = Column('tx_guid', VARCHAR(length=32), ForeignKey('transactions.guid'), index=True)
    account_guid = Column('account_guid', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False, index=True)
    memo = Column('memo', VARCHAR(length=2048), nullable=False)
    action = Column('action', VARCHAR(length=2048), nullable=False)

    reconcile_state = Column('reconcile_state', VARCHAR(length=1), nullable=False)
    reconcile_date = Column('reconcile_date', _DateTime())

    _value_num = Column('value_num', BIGINT(), nullable=False)
    _value_denom = Column('value_denom', BIGINT(), nullable=False)
    _value_denom_basis = None
    value = hybrid_property_gncnumeric(_value_num, _value_denom)
    _quantity_num = Column('quantity_num', BIGINT(), nullable=False)
    _quantity_denom = Column('quantity_denom', BIGINT(), nullable=False)
    _quantity_denom_basis = None
    quantity = hybrid_property_gncnumeric(_quantity_num, _quantity_denom)

    lot_guid = Column('lot_guid', VARCHAR(length=32), ForeignKey('lots.guid'))

    # relation definitions
    account = relation('Account', back_populates='splits')
    lot = relation('Lot', back_populates='splits')
    transaction = relation('Transaction', back_populates='splits')

    def __init__(self,
                 account,
                 value,
                 quantity=None,
                 transaction=None,
                 memo="",
                 action="",
                 reconcile_date=None,
                 reconcile_state="n",
                 lot=None,
                 ):
        self.transaction = transaction
        self.account = account
        self.value = value
        self.quantity = value if quantity is None else quantity
        self.memo = memo
        self.action = action
        self.reconcile_date = reconcile_date
        self.reconcile_state = reconcile_state
        self.lot = lot

    def __unirepr__(self):
        try:
            cur = self.transaction.currency.mnemonic
            acc = self.account
            com = acc.commodity.mnemonic
            if com == "template":
                # case of template split from scheduled transaction
                sched_xaction = self["sched-xaction"]
                credit = sched_xaction["credit-formula"].value
                debit = sched_xaction["debit-formula"].value
                return u"SplitTemplate<{} {} {}>".format(sched_xaction["account"].value,
                                                         "credit={}".format(credit) if credit else "",
                                                         "debit={}".format(debit) if debit else "",

                                                         )
            elif cur == com:
                # case of same currency split
                return u"Split<{} {} {}>".format(acc,
                                                 self.value, cur)
            else:
                # case of non currency split
                return u"Split<{} {} {} [{} {}]>".format(acc,
                                                         self.value, cur,
                                                         self.quantity, com)
        except AttributeError:
            return u"Split<{}>".format(self.account)

    def object_to_validate(self, change):
        yield self
        if self.transaction:
            yield self.transaction
        if self.lot:
            yield self.lot

    def validate(self):
        old = self.get_all_changes()

        if old["STATE_CHANGES"][-1] == "deleted":
            return

        if '_quantity_num' in old or '_value_num' in old:
            self.transaction._recalculate_balance = True

        if self.transaction_guid is None:
            raise GncValidationError("The split is not linked to a transaction")

        if self.transaction.currency == self.account.commodity:
            if self.quantity != self.value:
                raise GncValidationError("The split has a quantity diffeerent from value "
                                         "while the transaction currency and the account commodity is the same")
        else:
            if self.quantity is None:
                raise GncValidationError("The split quantity is not defined while the split is on a commodity different from the transaction")
            if self.quantity.is_signed() != self.value.is_signed():
                raise GncValidationError("The split quantity has not the same sign as the split value")

        # everything is fine, let us normalise the value with respect to the currency/commodity precisions
        self._quantity_denom_basis = self.account.commodity_scu
        self._value_denom_basis = self.transaction.currency.fraction

        if self.transaction.currency != self.account.commodity:
            # let us also add a Price
            # TODO: check if price already exist at that tme
            from piecash import Price

            value = (self.value / self.quantity).quantize(Decimal("0.000001"))
            try:
                # find existing price if any
                pr = self.book.prices(commodity=self.account.commodity,
                                      currency=self.transaction.currency,
                                      date=self.transaction.post_date,
                                      type="transaction",
                                      source="user:split-register")
                pr.value = value
            except KeyError:
                pr = Price(commodity=self.account.commodity,
                           currency=self.transaction.currency,
                           date=self.transaction.post_date,
                           value=value,
                           type="transaction",
                           source="user:split-register")

            # and an action if not yet defined
            if self.action == "":
                self.action = "Sell" if self.quantity.is_signed() else "Buy"


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
        scheduled_transaction  (:class:`ScheduledTransaction`): scheduled transaction behind the transaction
        notes (str): notes on the transaction (provided via a slot)
    """
    __tablename__ = 'transactions'

    __table_args__ = {}

    # column definitions
    currency_guid = Column('currency_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    num = Column('num', VARCHAR(length=2048), nullable=False)
    _post_date = Column('post_date', _DateTime, index=True)
    post_date = mapped_to_slot_property(_post_date,
                                        slot_name="date-posted",
                                        slot_transform=lambda x: x.date() if x else None)
    enter_date = Column('enter_date', _DateTime)
    description = Column('description', VARCHAR(length=2048))
    notes = pure_slot_property('notes')

    scheduled_transaction = pure_slot_property('from-sched-xaction', ignore_invalid_slot=True)

    # relation definitions
    currency = relation('Commodity',
                        back_populates='transactions',
                        )
    splits = relation('Split',
                      back_populates="transaction",
                      cascade='all, delete-orphan',
                      collection_class=CallableList,
                      )

    def __init__(self,
                 currency,
                 description="",
                 notes=None,
                 splits=None,
                 enter_date=None,
                 post_date=None,
                 num="",
                 ):

        assert enter_date is None or isinstance(enter_date, datetime.datetime), "enter_date should be a datetime object"
        assert post_date is None or isinstance(post_date, datetime.datetime), "post_date should be a datetime object"

        self.currency = currency
        self.description = description
        self.enter_date = (enter_date if enter_date else datetime.datetime.today()) \
            .replace(microsecond=0)
        self.post_date = (post_date if post_date else datetime.datetime.today()) \
            .replace(hour=11, minute=0, second=0, microsecond=0)
        self.num = num
        if notes is not None:
            self.notes = notes
        if splits:
            self.splits = splits

    def __unirepr__(self):
        return u"Transaction<[{}] '{}' on {:%Y-%m-%d}{}>".format(self.currency.mnemonic,
                                                                 self.description,
                                                                 self.post_date,
                                                                 " (from sch tx)" if self.scheduled_transaction else "")

    def object_to_validate(self, change):
        yield self

    def validate(self):
        old = self.get_all_changes()

        if old["STATE_CHANGES"][-1] == "deleted":
            return

        if self.currency.namespace != "CURRENCY":
            raise GncValidationError("You are assigning a non currency commodity to a transaction")

        # check all accounts related to the splits of the transaction are not placeholder(=frozen)
        for sp in self.splits:
            if sp.account.placeholder != 0:
                raise GncValidationError("Account '{}' used in the transaction is a placeholder".format(sp.account))

        # check same currency
        if "currency" in old and old["currency"] is not NEVER_SET:
            raise GncValidationError("You cannot change the currency of a transaction once it has been set")

        # validate the splits
        if hasattr(self, "_recalculate_balance"):
            del self._recalculate_balance
            value_imbalance, quantity_imbalances = self.calculate_imbalances()
            if value_imbalance:
                # raise exception instead of creating an imbalance entry as probably an error
                # (in the gnucash GUI, another decision taken because need of "save unfinished transaction")
                raise GncImbalanceError("The transaction {} is not balanced on its value".format(self))

            if any(quantity_imbalances.values()) and self.book.use_trading_accounts:
                self.normalize_trading_accounts()

        # normalise post_date to 11:00AM
        if self.post_date:
            self.post_date = self.post_date.replace(hour=11, minute=0, second=0, microsecond=0)

    def calculate_imbalances(self):
        """Calculate value and quantity imbalances of a transaction"""
        value_imbalance = Decimal(0)  # hold imbalance on split.value
        quantity_imbalances = defaultdict(Decimal)  # hold imbalance on split.quantity per cdty

        # collect imbalance information
        for sp in self.splits:
            value_imbalance += sp.value
            quantity_imbalances[sp.account.commodity] += sp.quantity

        return value_imbalance, quantity_imbalances

    def normalize_trading_accounts(self):
        # collect imbalance information
        classic_splits = defaultdict(list)
        trading_splits = defaultdict(list)
        trading_target_value = defaultdict(Decimal)
        trading_target_quantity = defaultdict(Decimal)

        for sp in self.splits:
            cdty = sp.account.commodity

            if sp.account.type == "TRADING":
                trading_splits[cdty].append(sp)
            else:
                classic_splits[cdty].append(sp)
            trading_target_value[cdty] += sp.value
            trading_target_quantity[cdty] += sp.quantity

        root = self.book.root_account
        # imbalance in quantities to be settled using trading accounts
        for cdty, v in trading_target_value.items():
            q = trading_target_quantity[cdty]

            # if commodity is balanced, do not do anything
            if (v == q == 0): continue

            # otherwise, look if there is some trading imbalance (ie a split with the trading account already exists!)
            if cdty in trading_splits:
                # and adjust the related split to rebalance
                sp, = trading_splits[cdty]
                sp.value -= v
                sp.quantity -= q
            else:
                # otherwise, we must create the split related to the trading account
                # assume trading account exists
                t_acc = self.book.trading_account(cdty)
                sp = Split(account=t_acc,
                           value=-v,
                           quantity=-q,
                           transaction=self,
                           )


class ScheduledTransaction(DeclarativeBaseGuid):
    """
    A GnuCash Scheduled Transaction.

    Attributes
        adv_creation (int) : days to create in advance (0 if disabled)
        adv_notify (int) : days to notify in advance (0 if disabled)
        auto_create (bool) :
        auto_notify (bool) :
        enabled (bool) :
        start_date (:class:`datetime.datetime`) : date to start the scheduled transaction
        last_occur (:class:`datetime.datetime`) : date of last occurence of the schedule transaction
        end_date (:class:`datetime.datetime`) : date to end the scheduled transaction (num/rem_occur should be 0)
        instance_count (int) :
        name (str) : name of the scheduled transaction
        num_occur (int) : number of occurences in total (end_date should be null)
        rem_occur (int) : number of remaining occurences (end_date should be null)
        template_account (:class:`piecash.core.account.Account`): template account of the transaction
    """
    __tablename__ = 'schedxactions'

    __table_args__ = {}

    # column definitions
    guid = Column('guid', VARCHAR(length=32), primary_key=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = Column('name', VARCHAR(length=2048))
    enabled = Column('enabled', INTEGER(), nullable=False)
    start_date = Column('start_date', _Date())
    end_date = Column('end_date', _Date())
    last_occur = Column('last_occur', _Date())
    num_occur = Column('num_occur', INTEGER(), nullable=False)
    rem_occur = Column('rem_occur', INTEGER(), nullable=False)
    auto_create = Column('auto_create', INTEGER(), nullable=False)
    auto_notify = Column('auto_notify', INTEGER(), nullable=False)
    adv_creation = Column('adv_creation', INTEGER(), nullable=False)
    adv_notify = Column('adv_notify', INTEGER(), nullable=False)
    instance_count = Column('instance_count', INTEGER(), nullable=False)
    template_act_guid = Column('template_act_guid', VARCHAR(length=32), ForeignKey('accounts.guid'), nullable=False)

    # relation definitions
    template_account = relation('Account')
    recurrence = relation('Recurrence',
                          primaryjoin=guid == foreign(Recurrence.obj_guid),
                          cascade='all, delete-orphan',
                          uselist=False,
                          )

    def __unirepr__(self):
        return u"ScheduledTransaction<'{}' {}>".format(self.name, self.recurrence)


class Lot(DeclarativeBaseGuid):
    """
    A GnuCash Lot. Each lot is linked to an account. Splits in this account can be associated to a Lot. Whenever
    the balance of the splits goes to 0, the Lot is closed (otherwise it is opened)

    Attributes:
        is_closed (int) : 1 if lot is closed, 0 otherwise
        account (:class:`piecash.core.account.Account`): account of the Lot
        splits (:class:`piecash.core.transaction.Split`): splits associated to the Lot
    """
    __tablename__ = 'lots'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', VARCHAR(length=32), ForeignKey('accounts.guid'))
    is_closed = Column('is_closed', INTEGER(), nullable=False)

    title = pure_slot_property('title')
    notes = pure_slot_property('notes')

    # relation definitions
    account = relation('Account', back_populates='lots', )
    splits = relation('Split',
                      back_populates='lot',
                      collection_class=CallableList,
                      )

    def __init__(self,
                 title,
                 account,
                 notes="",
                 splits=None,
                 is_closed=0):
        self.title = title
        self.account = account
        self.notes = notes
        if splits:
            self.splits[:] = splits
        self.is_closed = is_closed

    @validates("splits", "account")
    def check_no_change_if_lot_is_close(self, key, value):
        if self.is_closed:
            raise ValueError("Lot is closed and cannot be changed (adding splits or changing account")
        return value

    def object_to_validate(self, change):
        yield self

    def validate(self):
        # check all splits have same account
        for sp in self.splits:
            if sp.account != self.account:
                raise ValueError("Split {} is not in the same commodity of the lot {}".format(sp, self))

    def __unirepr__(self):
        return u"Lot<'{}' on {}>".format(self.title, self.account.name)
