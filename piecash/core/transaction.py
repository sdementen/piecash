import datetime
import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import Column, VARCHAR, ForeignKey, BIGINT, INTEGER, Index
from sqlalchemy.orm import relation, validates, foreign
from sqlalchemy.orm.base import NEVER_SET

from .._common import CallableList, GncImbalanceError
from .._common import GncValidationError, hybrid_property_gncnumeric, Recurrence
from .._declbase import DeclarativeBaseGuid
from ..sa_extra import (
    _Date,
    _DateTime,
    mapped_to_slot_property,
    pure_slot_property,
    _DateAsDateTime,
)


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

    __tablename__ = "splits"

    __table_args__ = (
        # indices
        Index("splits_tx_guid_index", "tx_guid"),
        Index("splits_account_guid_index", "account_guid"),
    )

    # column definitions
    # the transaction_guid is not mandatory at construction time because it can be set through a tr.splits.append(...) operation
    # however, in the validation of the object, we raise an error if there is no transaction set at that time
    transaction_guid = Column(
        "tx_guid", VARCHAR(length=32), ForeignKey("transactions.guid")
    )
    account_guid = Column(
        "account_guid", VARCHAR(length=32), ForeignKey("accounts.guid"), nullable=False
    )
    memo = Column("memo", VARCHAR(length=2048), nullable=False)
    action = Column("action", VARCHAR(length=2048), nullable=False)

    reconcile_state = Column("reconcile_state", VARCHAR(length=1), nullable=False)
    reconcile_date = Column("reconcile_date", _DateTime())

    _value_num = Column("value_num", BIGINT(), nullable=False)
    _value_denom = Column("value_denom", BIGINT(), nullable=False)
    _value_denom_basis = None
    value = hybrid_property_gncnumeric(_value_num, _value_denom)
    _quantity_num = Column("quantity_num", BIGINT(), nullable=False)
    _quantity_denom = Column("quantity_denom", BIGINT(), nullable=False)
    _quantity_denom_basis = None
    quantity = hybrid_property_gncnumeric(_quantity_num, _quantity_denom)

    lot_guid = Column("lot_guid", VARCHAR(length=32), ForeignKey("lots.guid"))

    # relation definitions
    account = relation("Account", back_populates="splits")
    lot = relation("Lot", back_populates="splits")
    transaction = relation(
        "Transaction", back_populates="splits", cascade="refresh-expire"
    )

    @property
    def is_credit(self):
        return self.value < 0

    @property
    def is_debit(self):
        return self.value > 0

    def __init__(
        self,
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

    def __str__(self):
        try:
            cur = self.transaction.currency.mnemonic
            acc = self.account
            com = acc.commodity.mnemonic
            if com == "template":
                # case of template split from scheduled transaction
                sched_xaction = self["sched-xaction"]
                credit = sched_xaction["credit-formula"].value
                debit = sched_xaction["debit-formula"].value
                return "SplitTemplate<{} {} {}>".format(
                    sched_xaction["account"].value,
                    "credit={}".format(credit) if credit else "",
                    "debit={}".format(debit) if debit else "",
                )
            elif cur == com:
                # case of same currency split
                return "Split<{} {} {}>".format(acc, self.value, cur)
            else:
                # case of non currency split
                return "Split<{} {} {} [{} {}]>".format(
                    acc, self.value, cur, self.quantity, com
                )
        except AttributeError:
            return "Split<{}>".format(self.account)

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

        if "_quantity_num" in old or "_value_num" in old:
            self.transaction._recalculate_balance = True

        if self.transaction_guid is None:
            raise GncValidationError("The split is not linked to a transaction")

        if self.transaction.currency == self.account.commodity:
            if self.quantity != self.value:
                raise GncValidationError(
                    "The split has a quantity different from value "
                    "while the transaction currency and the account commodity is the same"
                )
        else:
            if self.quantity is None:
                raise GncValidationError(
                    "The split quantity is not defined while the split is on a commodity different from the transaction"
                )
            # Allow for either value to be 0.0 (or -0.0).
            if self.quantity * self.value < 0:
                raise GncValidationError(
                    "The split quantity has not the same sign as the split value"
                )

        # everything is fine, let us normalise the value with respect to the currency/commodity precisions
        self._quantity_denom_basis = self.account.commodity_scu
        self._value_denom_basis = self.transaction.currency.fraction

        if self.transaction.currency != self.account.commodity and self.quantity:
            # let us also add a Price
            from piecash import Price

            value = (self.value / self.quantity).quantize(Decimal("0.000001"))
            try:
                # find existing price if any and if so, do nothing
                pr = self.book.prices(
                    commodity=self.account.commodity,
                    currency=self.transaction.currency,
                    date=self.transaction.post_date,
                )

            except KeyError:
                # otherwise, add a price in the database
                pr = Price(
                    commodity=self.account.commodity,
                    currency=self.transaction.currency,
                    date=self.transaction.post_date,
                    value=value,
                    type="transaction",
                    source="user:split-register",
                )

            # and an action if not yet defined
            if self.action == "":
                self.action = "Sell" if self.quantity.is_signed() else "Buy"


# @event.listens_for(Split.transaction, "set")
# def set_item(obj, value, previous, initiator):
#     print("hello",obj,value,previous,initiator)
#     if obj.transaction is not None:
#         previous = None if previous == attributes.NO_VALUE else previous
#         print(obj.transaction.splits)
#         # obj.transaction.splits.append([value] = obj
#         # obj.transaction.splits.pop(previous)


class Transaction(DeclarativeBaseGuid):
    """
    A GnuCash Transaction.

    Attributes:
        currency (:class:`piecash.core.commodity.Commodity`): currency of the transaction. This attribute is
            write-once (i.e. one cannot change it after being set)
        description (str): description of the transaction
        enter_date (:class:`datetime.datetime`): datetimetime at which transaction is entered
        post_date (:class:`datetime.date`): day on which transaction is posted
        num (str): user provided transaction number
        splits (list of :class:`Split`): list of the splits of the transaction
        scheduled_transaction  (:class:`ScheduledTransaction`): scheduled transaction behind the transaction
        notes (str): notes on the transaction (provided via a slot)
    """

    __tablename__ = "transactions"

    __table_args__ = (Index("tx_post_date_index", "post_date"),)

    # column definitions
    currency_guid = Column(
        "currency_guid",
        VARCHAR(length=32),
        ForeignKey("commodities.guid"),
        nullable=False,
    )
    num = Column("num", VARCHAR(length=2048), nullable=False)
    _post_date = Column("post_date", _DateAsDateTime(neutral_time=True))
    post_date = mapped_to_slot_property(
        _post_date,
        slot_name="date-posted",
        # slot_transform=lambda x: x.date() if x else None
    )
    enter_date = Column("enter_date", _DateTime)
    description = Column("description", VARCHAR(length=2048))
    notes = pure_slot_property("notes")

    scheduled_transaction = pure_slot_property(
        "from-sched-xaction", ignore_invalid_slot=True
    )

    # relation definitions
    currency = relation(
        "Commodity",
        back_populates="transactions",
    )
    splits = relation(
        "Split",
        back_populates="transaction",
        cascade="all, delete-orphan",
        collection_class=CallableList,
    )

    def __init__(
        self,
        currency,
        description="",
        notes=None,
        splits=None,
        enter_date=None,
        post_date=None,
        num="",
    ):

        if not (enter_date is None or type(enter_date) is datetime.datetime):
            raise GncValidationError("enter_date should be a datetime object")
        if not (post_date is None or type(post_date) is datetime.date):
            raise GncValidationError("post_date should be a date object")

        self.currency = currency
        self.description = description
        self.enter_date = (
            enter_date if enter_date else datetime.datetime.now()
        ).replace(microsecond=0)
        self.post_date = post_date if post_date else datetime.date.today()
        self.num = num
        if notes is not None:
            self.notes = notes
        if splits:
            self.splits = splits

    def __str__(self):
        return "Transaction<[{}] '{}' on {:%Y-%m-%d}{}>".format(
            self.currency.mnemonic,
            self.description,
            self.post_date,
            " (from sch tx)" if self.scheduled_transaction else "",
        )

    def object_to_validate(self, change):
        yield self

    def validate(self):
        old = self.get_all_changes()

        if old["STATE_CHANGES"][-1] == "deleted":
            return

        if not self.currency.is_currency():
            raise GncValidationError(
                "You are assigning a non currency commodity to a transaction"
            )

        # check all accounts related to the splits of the transaction are not placeholder(=frozen)
        for sp in self.splits:
            if sp.account.placeholder != 0:
                raise GncValidationError(
                    "Account '{}' used in the transaction is a placeholder".format(
                        sp.account
                    )
                )

        # check same currency
        if "currency" in old and old["currency"] is not NEVER_SET:
            raise GncValidationError(
                "You cannot change the currency of a transaction once it has been set"
            )

        # validate the splits
        if hasattr(self, "_recalculate_balance"):
            del self._recalculate_balance
            value_imbalance, quantity_imbalances = self.calculate_imbalances()
            if value_imbalance:
                # raise exception instead of creating an imbalance entry as probably an error
                # (in the gnucash GUI, another decision taken because need of "save unfinished transaction")
                raise GncImbalanceError(
                    "The transaction {} is not balanced on its value (delta={})".format(
                        self, value_imbalance
                    )
                )

            if any(quantity_imbalances.values()) and self.book.use_trading_accounts:
                self.normalize_trading_accounts()

        # normalise post_date to 10:59AM
        # if self.post_date:
        #    self.post_date = self.post_date.replace(hour=10, minute=59, second=0, microsecond=0, tzinfo=utc)

    def calculate_imbalances(self):
        """Calculate value and quantity imbalances of a transaction"""
        value_imbalance = Decimal(0)  # hold imbalance on split.value
        quantity_imbalances = defaultdict(
            Decimal
        )  # hold imbalance on split.quantity per cdty

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
            if v == q == 0:
                continue

            # otherwise, look if there is some trading imbalance (ie a split with the trading account already exists!)
            if cdty in trading_splits:
                # and adjust the related split to rebalance
                (sp,) = trading_splits[cdty]
                sp.value -= v
                sp.quantity -= q
            else:
                # otherwise, we must create the split related to the trading account
                # assume trading account exists
                t_acc = self.book.trading_account(cdty)
                sp = Split(
                    account=t_acc,
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

    __tablename__ = "schedxactions"

    __table_args__ = {}

    # column definitions
    guid = Column(
        "guid",
        VARCHAR(length=32),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex,
    )
    name = Column("name", VARCHAR(length=2048))
    enabled = Column("enabled", INTEGER(), nullable=False)
    start_date = Column("start_date", _Date())
    end_date = Column("end_date", _Date())
    last_occur = Column("last_occur", _Date())
    num_occur = Column("num_occur", INTEGER(), nullable=False)
    rem_occur = Column("rem_occur", INTEGER(), nullable=False)
    auto_create = Column("auto_create", INTEGER(), nullable=False)
    auto_notify = Column("auto_notify", INTEGER(), nullable=False)
    adv_creation = Column("adv_creation", INTEGER(), nullable=False)
    adv_notify = Column("adv_notify", INTEGER(), nullable=False)
    instance_count = Column("instance_count", INTEGER(), nullable=False)
    template_act_guid = Column(
        "template_act_guid",
        VARCHAR(length=32),
        ForeignKey("accounts.guid"),
        nullable=False,
    )

    # relation definitions
    template_account = relation("Account")
    recurrence = relation(
        "Recurrence",
        primaryjoin=guid == foreign(Recurrence.obj_guid),
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __str__(self):
        return "ScheduledTransaction<'{}' {}>".format(self.name, self.recurrence)


class Lot(DeclarativeBaseGuid):
    """
    A GnuCash Lot. Each lot is linked to an account. Splits in this account can be associated to a Lot. Whenever
    the balance of the splits goes to 0, the Lot is closed (otherwise it is opened)

    Attributes:
        is_closed (int) : 1 if lot is closed, 0 otherwise
        account (:class:`piecash.core.account.Account`): account of the Lot
        splits (:class:`piecash.core.transaction.Split`): splits associated to the Lot
    """

    __tablename__ = "lots"

    __table_args__ = {}

    # column definitions
    account_guid = Column(
        "account_guid", VARCHAR(length=32), ForeignKey("accounts.guid")
    )
    is_closed = Column("is_closed", INTEGER(), nullable=False)

    title = pure_slot_property("title")
    notes = pure_slot_property("notes")

    # relation definitions
    account = relation(
        "Account",
        back_populates="lots",
    )
    splits = relation(
        "Split",
        back_populates="lot",
        collection_class=CallableList,
    )

    def __init__(self, title, account, notes="", splits=None, is_closed=0):
        self.title = title
        self.account = account
        self.notes = notes
        if splits:
            self.splits[:] = splits
        self.is_closed = is_closed

    @property
    def quantity(self):
        """Returns the sum of the quantities of the splits associated with the lot."""
        return sum([split.quantity for split in self.splits])

    @property
    def value(self):
        """Returns the sum of the values of the splits associated with the lot."""
        return sum([split.value for split in self.splits])

    def add_split(self, split):
        """Add split to lot. If the split could close the lot, the split is sub-split;
        one part to close the lot, and a remainder which is returned.

        Attributes:
            split (Split): the split to add to the lot
        
        Returns:
            split (Split): excess split, if any
        """
        s = None

        # Split may overfill lot - sub-split split if required
        if self.quantity * (self.quantity + split.quantity) < 0:
            # Create a new split with the overfill.
            new_qty = (split.quantity + self.quantity)

            s = Split(
                account=split.account,
                value=split.value / split.quantity * new_qty,
                quantity=new_qty,
                transaction=split.transaction,
                memo=split.memo,
                action=split.action,
                reconcile_date=split.reconcile_date,
                reconcile_state=split.reconcile_state,
                lot=None,
            )

            # Adjust the old split.
            split.value = abs(split.value) / split.quantity * self.quantity
            split.quantity = -self.quantity

            # Slots - set date and link the peer splits to each other.
            self.book.flush()

            # Set the slot for date if not already set
            try:
                split["lot-split/date"]
            except KeyError:
                split["lot-split/date"] = datetime.datetime.now().replace(microsecond=0)
            split["lot-split/peer_guid"] = s
            s["lot-split/peer_guid"] = split
            s["lot-split/date"] = datetime.datetime.now().replace(microsecond=0)

        # Add split to lot
        split.lot = self

        # Return the sub-split
        return s

    def scrub_lot(self):
        """Add a transaction capturing gains/losses.
        
        A transaction is added for each realisation, with quantity of zero but value matching
        the gains/losses. A realisation is any split with a value/quantity sign opposite the
        opening split. Normally, the lot will hold a single 'buy' split and one or more 'sell'
        splits, but the code below supports multiple 'buys' and 'sells'.

        Attributes:
            None
        
        Returns:
            None
        """
        # Check that all splits were made with the same currency
        if len(self.splits) > 1 and not all(self.splits[0].transaction.currency == sp.transaction.currency for sp in self.splits):
            raise ValueError("Lot contains splits with mixed currencies. Cannot proceed - aborting.")

        # Get the gains_losses_account associated with this lot's account
        gains_losses_account = list(self.account["lot-mgmt/gains-acct"].value.values())[0]

        # Check that the gains/losses account has the same currency as the transactions
        if gains_losses_account and not all(gains_losses_account.commodity == sp.transaction.currency for sp in self.splits if sp.value != 0):
            raise ValueError(f"The currency of the provided gains/losses account ({gains_losses_account}) does not match "
                             "the currency of the transactions in the lot. Aborting.")

        # Create an empty queue for holding the opening split, and any following 'buy' splits.
        lst = []

        # Get splits that are not assigned to a lot and not void.
        splits = [split for split in self.splits if split.quantity != 0 and split.reconcile_state != "v"]

        # Sort the splits by transaction post_date ascending
        splits.sort(key=lambda sp: sp.transaction.post_date)

        for split in splits:
            if split.quantity * splits[0].quantity > 0:
                # if same sign as opening split, add (value, quantity) tuple to queue
                lst.append((split.value, split.quantity))
            else:
                # if different sign, gains/losses were realised
                quantity = split.quantity
                gain = -split.value

                while quantity != 0 and lst:
                    val, qty = lst.pop(0)
                    excess = (quantity + qty) if (quantity * (quantity + qty)) < 0 else 0

                    if excess != 0:
                        # stick excess back in queue
                        lst.insert(0, (val / qty * excess, excess))
                        
                    # Deduct the purchase value from the sales value
                    gain -= val * (qty - excess) / qty
                    quantity += qty - excess

                # Check that the split that realised a gain/loss hasn't already been 
                # added to the lot. If not, create a transaction with the gains/losses.
                if gain != 0 and "gains-split" not in split:
                    post_date = split.transaction.post_date
                    memo = "Realised Gain/Loss"
                    currency = split.transaction.currency

                    tr = Transaction(
                            post_date = post_date,
                            currency = currency,
                            description = memo,
                            splits=[
                                Split(account=gains_losses_account, memo=memo, value=-gain),
                                Split(account=self.account, memo=memo, value=gain, quantity=0, lot=self)
                            ])

                    # Set slots
                    self.book.flush()
                    tr.splits[1]["gains-source"] = split
                    split["gains-split"] = tr.splits[1]

    @validates("splits", "account")
    def check_no_change_if_lot_is_close(self, key, value):
        if self.is_closed:
            raise ValueError(
                "Lot is closed and cannot be changed (adding splits or changing account"
            )
        return value

    def object_to_validate(self, change):
        yield self

    def validate(self):
        # check all splits have same account
        for sp in self.splits:
            if sp.account != self.account:
                raise ValueError(
                    "Split {} is not in the same commodity of the lot {}".format(
                        sp, self
                    )
                )

    def __str__(self):
        return "Lot<'{}' on {}>".format(self.title, self.account.name)
