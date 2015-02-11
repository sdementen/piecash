from collections import defaultdict
from decimal import Decimal
import datetime
import uuid

from sqlalchemy import Column, VARCHAR, ForeignKey, BIGINT, event, INTEGER
from sqlalchemy.orm import relation, validates, foreign
from sqlalchemy.orm.base import instance_state
from sqlalchemy.orm.exc import NoResultFound

from .._common import GncValidationError, hybrid_property_gncnumeric, Recurrence
from .._declbase import DeclarativeBaseGuid
from .._common import CallableList
from piecash._common import GncImbalanceError
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
    transaction_guid = Column('tx_guid', VARCHAR(length=32), ForeignKey('transactions.guid'), nullable=False,
                              index=True)
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
                 account=None,
                 value=0,
                 quantity=0,
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
        self.quantity = quantity
        self.memo = memo
        self.action = action
        self.reconcile_date = reconcile_date
        self.reconcile_state = reconcile_state
        self.lot = lot

    def __repr__(self):
        try:
            cur = self.transaction.currency.mnemonic
            acc = self.account
            com = acc.commodity.mnemonic
            if com == "template":
                # case of template split from scheduled transaction
                sched_xaction = self["sched-xaction"]
                credit = sched_xaction["credit-formula"].value
                debit = sched_xaction["debit-formula"].value
                return "<SplitTemplate {} {} {}>".format(sched_xaction["account"].value,
                                                         "credit={}".format(credit) if credit else "",
                                                         "debit={}".format(debit) if debit else "",

                )
            elif cur == com:
                # case of same currency split
                return "<Split {} {} {}>".format(acc,
                                                 self.value, cur)
            else:
                # case of non currency split
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

    scheduled_transaction = pure_slot_property('from-sched-xaction')

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
        self.currency = currency
        self.description = description
        self.enter_date = enter_date if enter_date else datetime.datetime.today()
        self.post_date = post_date if post_date \
            else datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        self.num = num
        if notes is not None:
            self.notes = notes
        if splits:
            self.splits = splits

    def __repr__(self):
        return "<Transaction[{}] '{}' on {:%Y-%m-%d}{}>".format(self.currency.mnemonic,
                                                                self.description,
                                                                self.post_date,
                                                                " (from sch tx)" if self.scheduled_transaction else "")

    def ledger_str(self):
        """Return a ledger-cli alike representation of the transaction"""
        s = ["{:%Y/%m/%d} * {}\n".format(self.post_date, self.description)]
        if self.notes:
            s.append(";{}\n".format(self.notes))
        for split in self.splits:
            s.append("\t{:40} ".format(split.account.fullname))
            if split.account.commodity != self.currency:
                s.append("{:10.2f} {} @@ {:.2f} {}".format(
                    split.quantity, split.account.commodity.mnemonic, abs(split.value),
                    self.currency.mnemonic))
            else:
                s.append("{:10.2f} {}".format(split.value, self.currency.mnemonic))
            if split.memo:
                s.append(" ;   {:20}".format(split.memo))
            s.append("\n")
        return "".join(s)

    @validates("currency")
    def validate_currency(self, key, value):
        if value is not None and value.namespace != "CURRENCY":
            raise GncValidationError("You are assigning a non currency commodity to a transaction")
        return value


    def calculate_imbalances(self):
        """Calculate value and quantity imbalances of a transaction"""
        value_imbalance = Decimal(0) # hold imbalance on split.value
        quantity_imbalances = defaultdict(Decimal) # hold imbalance on split.quantity per cdty

        # collect imbalance information
        for sp in self.splits:
            value_imbalance += sp.value
            quantity_imbalances[sp.account.commodity] += sp.quantity

        return value_imbalance, quantity_imbalances

    def normalize_trading_accounts(self):
        # collect imbalance information
        classic_splits =defaultdict(list)
        trading_splits =defaultdict(list)
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

    def validate(self):
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
            value_imbalance, quantity_imbalances = self.calculate_imbalances()
            if value_imbalance:
                # raise exception instead of creating an imbalance entry as probably an error
                # (in the gnucash GUI, another decision taken because need of "save unfinished transaction")
                raise GncImbalanceError("The transaction {} is not balanced on its value".format(self))

            if any(quantity_imbalances.values()) and self.book.use_trading_accounts:
                self.normalize_trading_accounts()

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


@event.listens_for(Session, 'before_flush')
def set_imbalance_on_transaction(session, flush_context, instances):
    # identify transactions to verify
    txs = set()
    for o in session.dirty:
        if isinstance(o, Transaction):
            txs.add(o)
        if isinstance(o, Split):
            if o.transaction:
                txs.add(o.transaction)
    txs = txs.union(o for o in session.new if isinstance(o, Transaction))

    # for each transaction, validate the transaction
    for tx in txs:
        tx.validate()


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

    def __repr__(self):
        return "<ScheduledTransaction '{}' {}>".format(self.name, self.recurrence)


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
                 splits=None):
        self.title = title
        self.account = account
        self.notes = notes
        if splits:
            self.splits[:] = splits

    @validates("splitsentries", "account")
    def validate_account_split_consistency(self, key, value):
        if key == "account" and self.account and self.splits:
            raise ValueError("You cannot change the account of a Lot once a split has already been assigned")
        if key == "splits" and not self.account:
            raise ValueError("You can assign splits to a lot only once the account is set")
        if key == "splits":
            sp = value
            assert sp.lot is None, "The split has already a lot "
            assert sp.account == self.account, "You cannot assign to a lot a split that is not on the account of the lot"

        return value
