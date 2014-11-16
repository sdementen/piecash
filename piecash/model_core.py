from decimal import Decimal
import os
import decimal

from sqlalchemy import Column, INTEGER, BIGINT, TEXT, ForeignKey, create_engine, cast, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relation, backref, sessionmaker

from .model_common import DeclarativeBaseGuid, gnclock, GnucashException, _default_session
from .sa_extra import _DateTime, DeclarativeBase
from kvp import KVP_Type


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

    # definition of fields accessible through the kvp system
    _kvp_slots = {
        "notes": KVP_Type.KVP_TYPE_STRING,
    }


    def fullname(self):
        acc = self
        l = []
        while acc:
            l.append(acc.name)
            acc = acc.parent
        return ":".join(l[-2::-1])

    def __init__(self, **kwargs):
        # set description field to name field for convenience (if not defined)
        kwargs.setdefault('description', kwargs['name'])

        super(Account, self).__init__(**kwargs)


    def __repr__(self):
        return "Account<{}>".format(self.fullname())


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

    # definition of fields accessible through the kvp system
    _kvp_slots = {
        "options": KVP_Type.KVP_TYPE_FRAME,
    }



    # ------------ context manager ----------------------------------------------
    # class variable to be used with the context manager "with book:"
    def __enter__(self):
        _default_session.append(self.get_session())

    def __exit__(self, exc_type, exc_val, exc_tb):
        _default_session.pop()

    def save(self):
        self.get_session().commit()

    def cancel(self):
        self.get_session().rollback()


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

    lookup_key = mnemonic


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

    commodity = relation('Commodity', foreign_keys=[commodity_guid])
    currency = relation('Commodity', foreign_keys=[currency_guid])


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
    reconcile_state = Column('reconcile_state', TEXT(length=1), nullable=False)
    tx_guid = Column('tx_guid', TEXT(length=32), ForeignKey('transactions.guid'), nullable=False)

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
    currency_guid = Column('currency_guid', TEXT(length=32), ForeignKey('commodities.guid'), nullable=False)
    description = Column('description', TEXT(length=2048))
    enter_date = Column('enter_date', _DateTime)
    num = Column('num', TEXT(length=2048), nullable=False)
    post_date = Column('post_date', _DateTime)
    splits = relation(Split, backref='transaction',
                      cascade='all, delete-orphan')


    # relation definitions
    currency = relation('Commodity', backref=backref('transactions', cascade='all, delete-orphan'))

    # definition of fields accessible through the kvp system
    _kvp_slots = {
        "notes": KVP_Type.KVP_TYPE_STRING,
    }


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
    # none

    def __repr__(self):
        return "Version<{}={}>".format(self.table_name, self.table_version)


version_supported = {u'Gnucash-Resave': 19920, u'invoices': 3, u'books': 1, u'accounts': 1, u'slots': 3,
                     u'taxtables': 2, u'lots': 2, u'orders': 1, u'vendors': 1, u'customers': 2, u'jobs': 1,
                     u'transactions': 3, u'Gnucash': 2060400, u'budget_amounts': 1, u'billterms': 2, u'recurrences': 2,
                     u'entries': 3, u'prices': 2, u'schedxactions': 1, u'splits': 4, u'taxtable_entries': 3,
                     u'employees': 2, u'commodities': 1, u'budgets': 1}


def open_book_session(sqlite_file=None, postgres_conn=None, readonly=True, open_if_lock=False):
    """
    Open a GnuCash book and return the related SQLAlchemy session

    :param sqlite_file: a path to a sqlite3 file
    :param postgres_conn: a connection string to a postgres database
    :param readonly: open the file as readonly (useful to play with and avoid any unwanted save
    :param open_if_lock: open the file even if it is locked by another user (using open_if_lock=True with readonly=False is not recommended)
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

    # check the versions in the table versions is consistent with the API
    # TODO: improve this in the future to allow more than 1 version
    version_book = {v.table_name: v.table_version for v in s.query(Version).all()}
    for k, v in version_book.iteritems():
        # skip GnuCash
        if k in ("Gnucash"):
            continue
        if version_supported[k] != v:
            print k, v, version_supported[k]
            assert False, "{} {} {}".format(k, v, version_supported[k])


    # flush is a "no op" if readonly
    if readonly:
        def new_flush(*args, **kwargs):
            if s.dirty or s.new or s.deleted:
                s.rollback()
                raise GnucashException, "You cannot change the DB, it is locked !"

        s.flush = new_flush

    return s

def connect_to_gnucash_book(sqlite_file=None, postgres_conn=None, readonly=True, open_if_lock=False):
    s = open_book_session(sqlite_file, postgres_conn, readonly, open_if_lock)
    return s.query(Book).one()

open_book = connect_to_gnucash_book
