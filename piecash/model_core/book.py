from sqlalchemy import Column, VARCHAR, ForeignKey, create_engine
from sqlalchemy.orm import relation, backref, sessionmaker
from sqlalchemy.sql.ddl import DropConstraint
from sqlalchemy_utils import database_exists

from .account import Account
from ..kvp import KVP_Type
from ..model_common import DeclarativeBaseGuid, _default_session, GnucashException
from .transaction import Transaction
from .model_core import gnclock, Version
from ..sa_extra import DeclarativeBase, get_foreign_keys


version_supported = {u'Gnucash-Resave': 19920, u'invoices': 3, u'books': 1, u'accounts': 1, u'slots': 3,
                     u'taxtables': 2, u'lots': 2, u'orders': 1, u'vendors': 1, u'customers': 2, u'jobs': 1,
                     u'transactions': 3, u'Gnucash': 2060400, u'budget_amounts': 1, u'billterms': 2, u'recurrences': 2,
                     u'entries': 3, u'prices': 2, u'schedxactions': 1, u'splits': 4, u'taxtable_entries': 3,
                     u'employees': 2, u'commodities': 1, u'budgets': 1}


class Book(DeclarativeBaseGuid):
    __tablename__ = 'books'

    __table_args__ = {}

    # column definitions
    root_account_guid = Column('root_account_guid', VARCHAR(length=32),
                               ForeignKey('accounts.guid'), nullable=False)
    root_template_guid = Column('root_template_guid', VARCHAR(length=32),
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


def create_book(sqlite_file=None, uri_conn=None, overwrite=False):
    """
    Create a new empty GnuCash book. If both sqlite_file and uri_conn are None, then an "in memory" sqlite book is created.

    :param sqlite_file: a path to an sqlite file
    :param uri_conn: a sqlalchemy connection string
    :param overwrite: True if book should be deleted if it exists already and recreated
    :return: a sqlalchemy session with a 'book' attribute and 'save' and 'cancel' methods
    """
    from sqlalchemy_utils.functions import database_exists, create_database, drop_database

    if uri_conn is None:
        if sqlite_file:
            uri_conn = "sqlite:///{}".format(sqlite_file)
        else:
            uri_conn = "sqlite:///:memory:"

    # create database (if not sqlite in memory
    if uri_conn != "sqlite:///:memory:":
        if database_exists(uri_conn):
            if overwrite:
                drop_database(uri_conn)
            else:
                raise GnucashException, "'{}' db already exists".format(uri_conn)
        create_database(uri_conn)
    engine = create_engine(uri_conn)

    # create all (tables, fk, ...)
    DeclarativeBase.metadata.create_all(engine)

    # remove all foreign keys
    for fk in get_foreign_keys(DeclarativeBase.metadata, engine):
        if fk.name:
            engine.execute(DropConstraint(fk))

    # start session to create initial objects
    s = sessionmaker(bind=engine)()

    # create all rows in version table
    for table_name, table_version in version_supported.iteritems():
        s.add(Version(table_name=table_name, table_version=table_version))

    # create Book and initial accounts
    b = Book(root_account=Account(name="Root Account", account_type="ROOT"),
             root_template=Account(name="Template Root", account_type="ROOT"),
    )
    s.add(b)
    s.commit()
    return GncSession(s)


def open_book(sqlite_file=None, uri_conn=None, readonly=True, open_if_lock=False):
    """
    Open a GnuCash book and return the related SQLAlchemy session

    :param sqlite_file: a path to a sqlite3 file
    :param uri_conn: a SA connection string to a database
    :param readonly: open the file as readonly (useful to play with and avoid any unwanted save
    :param open_if_lock: open the file even if it is locked by another user (using open_if_lock=True with readonly=False is not recommended)
    :return: a wrapped SA session
    """
    if uri_conn is None:
        if sqlite_file:
            uri_conn = "sqlite:///{}".format(sqlite_file)
        else:
            raise ValueError, "One sqlite_file and uri_conn arguments should be given."

    # create database (if not sqlite in memory
    if not database_exists(uri_conn):
        raise GnucashException, "Database '{}' does not exist (please use create_book to create " \
                                "GnuCash books from scratch)".format(uri_conn)
    engine = create_engine(uri_conn)

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

    return GncSession(s)


class GncSession(object):
    def __init__(self, session):
        self.sa_session = session

    def save(self):
        self.sa_session.commit()

    def cancel(self):
        self.sa_session.rollback()

    @property
    def book(self):
        return self.sa_session.query(Book).one()

    @property
    def transactions(self):
        return self.sa_session.query(Transaction).all()



open_book_session = open_book
connect_to_gnucash_book = open_book
