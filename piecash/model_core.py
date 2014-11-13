from decimal import Decimal
import os

from sqlalchemy import Column, INTEGER, BIGINT, TEXT, REAL, ForeignKey, create_engine
from sqlalchemy.orm import relation, backref, sessionmaker
from enum import Enum

from .model_common import (DeclarativeBaseGuid, DeclarativeBase,
                           _DateTime, _Date,
                           GnucashException,
                           gnclock
)


class Account(DeclarativeBaseGuid):
    __tablename__ = 'accounts'

    __table_args__ = {}

    # column definitions
    account_type = Column('account_type', TEXT(length=2048), nullable=False)
    code = Column('code', TEXT(length=2048))
    commodity_guid = Column('commodity_guid', TEXT(length=32), ForeignKey('commodities.guid'))
    commodity_scu = Column('commodity_scu', INTEGER(), nullable=False, default=100)
    description = Column('description', TEXT(length=2048))
    guid = DeclarativeBaseGuid.guid
    hidden = Column('hidden', INTEGER(), default=False)
    name = Column('name', TEXT(length=2048), nullable=False)
    non_std_scu = Column('non_std_scu', INTEGER(), nullable=False, default=0)
    parent_guid = Column('parent_guid', TEXT(length=32), ForeignKey('accounts.guid'))
    placeholder = Column('placeholder', INTEGER())

    # relation definitions
    commodity = relation('Commodity', backref=backref('accounts', cascade='all, delete-orphan'))
    children = relation('Account',
                        backref=backref('parent', remote_side=guid),
                        cascade='all, delete-orphan',
    )
    slots = relation('Slot',
                     # remote_side='Slot.obj_guid',
                     primaryjoin='Account.guid==foreign(Slot.obj_guid)',
                     cascade='all, delete-orphan')

    def full_name(self):
        acc = self
        l = []
        while acc:
            l.append(acc.name)
            acc = acc.parent
        return ":".join(l[-2::-1])

    def __init__(self, **kwargs):
        kwargs.setdefault('description', kwargs['name'])

        super(Account, self).__init__(**kwargs)


    def __repr__(self):
        return "Account<{}>".format(self.full_name())


class Book(DeclarativeBaseGuid):
    __tablename__ = 'books'

    __table_args__ = {}

    # column definitions
    root_account_guid = Column('root_account_guid', TEXT(length=32),
                               ForeignKey('accounts.guid'), nullable=False)
    root_template_guid = Column('root_template_guid', TEXT(length=32),
                                ForeignKey('accounts.guid'), nullable=False)

    # relation definitions
    root_account = relation('Account', foreign_keys=[root_account_guid],
                            backref=backref('book', cascade='all, delete-orphan'))
    root_template = relation('Account', foreign_keys=[root_template_guid])


class Budget(DeclarativeBaseGuid):
    __tablename__ = 'budgets'

    __table_args__ = {}

    # column definitions
    description = Column('description', TEXT(length=2048))
    name = Column('name', TEXT(length=2048), nullable=False)
    num_periods = Column('num_periods', INTEGER(), nullable=False)

    # relation definitions


class BudgetAmount(DeclarativeBase):
    __tablename__ = 'budget_amounts'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', TEXT(length=32),
                          ForeignKey('accounts.guid'), nullable=False)
    amount_denom = Column('amount_denom', BIGINT(), nullable=False)
    amount_num = Column('amount_num', BIGINT(), nullable=False)
    budget_guid = Column('budget_guid', TEXT(length=32),
                         ForeignKey('budgets.guid'), nullable=False)
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    period_num = Column('period_num', INTEGER(), nullable=False)

    # relation definitions
    account = relation('Account', backref=backref('budget_amounts', cascade='all, delete-orphan'))
    budget = relation('Budget', backref=backref('amounts', cascade='all, delete-orphan'))


class Commodity(DeclarativeBaseGuid):
    __tablename__ = 'commodities'

    __table_args__ = {}

    # column definitions
    cusip = Column('cusip', TEXT(length=2048))
    fraction = Column('fraction', INTEGER(), nullable=False)
    fullname = Column('fullname', TEXT(length=2048))
    mnemonic = Column('mnemonic', TEXT(length=2048), nullable=False)
    namespace = Column('namespace', TEXT(length=2048), nullable=False)
    quote_flag = Column('quote_flag', INTEGER(), nullable=False)
    quote_source = Column('quote_source', TEXT(length=2048))
    quote_tz = Column('quote_tz', TEXT(length=2048))

    # relation definitions


class Price(DeclarativeBaseGuid):
    __tablename__ = 'prices'

    __table_args__ = {}

    # column definitions
    commodity_guid = Column('commodity_guid', TEXT(length=32), ForeignKey('commodities.guid'), nullable=False)
    currency_guid = Column('currency_guid', TEXT(length=32), ForeignKey('commodities.guid'), nullable=False)
    date = Column('date', _DateTime, nullable=False)
    source = Column('source', TEXT(length=2048))
    type = Column('type', TEXT(length=2048))
    value_denom = Column('value_denom', BIGINT(), nullable=False)
    value_num = Column('value_num', BIGINT(), nullable=False)

    # relation definitions
    commodity = relation('Commodity', foreign_keys=[commodity_guid])
    currency = relation('Commodity', foreign_keys=[currency_guid])


class Lot(DeclarativeBaseGuid):
    __tablename__ = 'lots'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', TEXT(length=32), ForeignKey('accounts.guid'))
    is_closed = Column('is_closed', INTEGER(), nullable=False)

    # relation definitions
    account = relation('Account', backref="lots")


class Schedxaction(DeclarativeBaseGuid):
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
    name = Column('name', TEXT(length=2048))
    num_occur = Column('num_occur', INTEGER(), nullable=False)
    rem_occur = Column('rem_occur', INTEGER(), nullable=False)
    start_date = Column('start_date', _Date())
    template_act_guid = Column('template_act_guid', TEXT(length=32), ForeignKey('accounts.guid'), nullable=False)

    # relation definitions


class KVP_Type(Enum):
    KVP_TYPE_INVALID = -1
    KVP_TYPE_GINT64 = 1
    KVP_TYPE_DOUBLE = 2
    KVP_TYPE_NUMERIC = 3
    KVP_TYPE_STRING = 4
    KVP_TYPE_GUID = 5
    KVP_TYPE_TIMESPEC = 6
    KVP_TYPE_BINARY = 7
    KVP_TYPE_GLIST = 8
    KVP_TYPE_FRAME = 9
    KVP_TYPE_GDATE = 10


class Slot(DeclarativeBase):
    __tablename__ = 'slots'

    __table_args__ = {}

    # column definitions
    name = Column('name', TEXT(length=4096), nullable=False)
    id = Column('id', INTEGER(), primary_key=True, nullable=False)
    obj_guid = Column('obj_guid', TEXT(length=32), nullable=False)
    slot_type = Column('slot_type', INTEGER(), nullable=False)

    double_val = Column('double_val', REAL())
    gdate_val = Column('gdate_val', _Date())
    guid_val = Column('guid_val', TEXT(length=32))
    int64_val = Column('int64_val', BIGINT())
    string_val = Column('string_val', TEXT(length=4096))
    timespec_val = Column('timespec_val', _DateTime())
    numeric_val_denom = Column('numeric_val_denom', BIGINT())
    numeric_val_num = Column('numeric_val_num', BIGINT())

    # relation definitions

    def __str__(self):
        return "<slot {}:{}>".format(self.name, self.string_val if self.slot_type == 4 else self.slot_type)


class Split(DeclarativeBaseGuid):
    __tablename__ = 'splits'

    __table_args__ = {}

    # column definitions
    account_guid = Column('account_guid', TEXT(length=32), ForeignKey('accounts.guid'), nullable=False, )
    action = Column('action', TEXT(length=2048), nullable=False)
    # guid = Column('guid', TEXT(length=32), primary_key=True, nullable=False)
    lot_guid = Column('lot_guid', TEXT(length=32), ForeignKey('lots.guid'))
    memo = Column('memo', TEXT(length=2048), nullable=False)
    quantity_denom = Column('quantity_denom', BIGINT(), nullable=False)
    quantity_num = Column('quantity_num', BIGINT(), nullable=False)
    reconcile_date = Column('reconcile_date', _DateTime())
    reconcile_state = Column('reconcile_state', TEXT(length=1), nullable=False)
    tx_guid = Column('tx_guid', TEXT(length=32), ForeignKey('transactions.guid'), nullable=False)
    value_denom = Column('value_denom', BIGINT(), nullable=False)
    value_num = Column('value_num', BIGINT(), nullable=False)

    # relation definitions
    account = relation('Account', backref=backref('splits', cascade='all, delete-orphan'))
    lot = relation('Lot', backref="splits")

    def __repr__(self):
        return "<Split {} {}>".format(self.account, self.value_num/self.value_denom)


class Transaction(DeclarativeBaseGuid):
    __tablename__ = 'transactions'

    __table_args__ = {}

    # column definitions
    currency_guid = Column('currency_guid', TEXT(length=32), ForeignKey('commodities.guid'), nullable=False)
    description = Column('description', TEXT(length=2048))
    enter_date = Column('enter_date', _DateTime)
    num = Column('num', TEXT(length=2048), nullable=False)
    post_date = Column('post_date', _DateTime)
    splits = relation(Split, backref='transaction',
                      cascade='all, delete-orphan')


    # relation definitions
    currency = relation('Commodity', backref=backref('transactions', cascade='all, delete-orphan'))

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


class Version(DeclarativeBase):
    __tablename__ = 'versions'

    __table_args__ = {}

    # column definitions
    table_name = Column('table_name', TEXT(length=50), primary_key=True, nullable=False)
    table_version = Column('table_version', INTEGER(), nullable=False)

    # relation definitions


def connect_to_gnucash_book(sqlite_file=None, postgres_conn=None, readonly=True, open_if_lock=False):
    """
    Open a GnuCash book and return the related SQLAlchemy session

    :param sqlite_file: a path to a sqlite3 file
    :param postgres_conn: a connection string to a postgres database
    :param readonly: open the file as readonly (useful to play with and avoid any unwanted save
    :param open_if_lock: open the file even if it is locked by another user
    (using open_if_lock=True with readonly=False is not recommended)
    :return: a SQLAlchemy session
    """
    engine = None
    if sqlite_file:
        if not os.path.exists(sqlite_file):
            raise GnucashException, "'{}' file does not exist (piecash cannot be used to create" \
                                    "GnuCash books from scratch)".format(sqlite_file)
        engine = create_engine("sqlite:///{}".format(sqlite_file))
    elif postgres_conn:
        engine = create_engine(postgres_conn)
    else:
        raise GnucashException, "Please specify either a sqlite file or a postgres connection"

    locks = list(engine.execute(gnclock.select()))

    # ensure the file is not locked by GnuCash itself
    if locks and not open_if_lock:
        raise GnucashException, "Lock on the file"
    # else:
    # engine.execute(gnclock.insert(), Hostname=socket.gethostname(), PID=os.getpid())

    s = sessionmaker(bind=engine)()
    # flush is a "no op" if readonly
    if readonly:
        def new_flush(*args, **kwargs):
            if s.dirty or s.new or s.deleted:
                s.rollback()
                raise GnucashException, "You cannot change the DB, it is locked !"

        s.flush = new_flush

    return s