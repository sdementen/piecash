import os
import socket

from sqlalchemy import event, create_engine, Column, VARCHAR, INTEGER, Table
from sqlalchemy.sql.ddl import DropConstraint
from sqlalchemy_utils import database_exists

from .book import Book
from .commodity import Commodity
from .._common import CallableList
from piecash.core import factories
from ..sa_extra import DeclarativeBase, get_foreign_keys, Session
from .._common import GnucashException


version_supported = {u'Gnucash-Resave': 19920, u'invoices': 3, u'books': 1, u'accounts': 1, u'slots': 3,
                     u'taxtables': 2, u'lots': 2, u'orders': 1, u'vendors': 1, u'customers': 2, u'jobs': 1,
                     u'transactions': 3, u'Gnucash': 2060400, u'budget_amounts': 1, u'billterms': 2, u'recurrences': 2,
                     u'entries': 3, u'prices': 2, u'schedxactions': 1, u'splits': 4, u'taxtable_entries': 3,
                     u'employees': 2, u'commodities': 1, u'budgets': 1}

# this is not a declarative as it is used before binding the session to an engine.
gnclock = Table(u'gnclock', DeclarativeBase.metadata,
                Column('hostname', VARCHAR(length=255)),
                Column('pid', INTEGER()),
)


class Version(DeclarativeBase):
    """The declarative class for the 'versions' table.
    """
    __tablename__ = 'versions'

    __table_args__ = {}

    # column definitions
    #: The name of the table
    table_name = Column('table_name', VARCHAR(length=50), primary_key=True, nullable=False)
    #: The version for the table
    table_version = Column('table_version', INTEGER(), nullable=False)

    def __init__(self, table_name, table_version):
        self.table_name=table_name
        self.table_version=table_version

    def __repr__(self):
        return "Version<{}={}>".format(self.table_name, self.table_version)


def create_book(sqlite_file=None, uri_conn=None, currency="EUR", overwrite=False, keep_foreign_keys=False, **kwargs):
    """Create a new empty GnuCash book. If both sqlite_file and uri_conn are None, then an "in memory" sqlite book is created.

    :param str sqlite_file: a path to an sqlite3 file
    :param str uri_conn: a sqlalchemy connection string
    :param str currency: the ISO symbol of the default currency of the book
    :param bool overwrite: True if book should be deleted and recreated if it exists already
    :param bool keep_foreign_keys: True if the foreign keys should be kept (may not work at all with GnuCash)

    :return: the document as a gnucash session
    :rtype: :class:`GncSession`

    :raises GnucashException: if document already exists and overwrite is False
    """
    from sqlalchemy_utils.functions import database_exists, create_database, drop_database

    if uri_conn is None:
        if sqlite_file:
            uri_conn = "sqlite:///{}".format(sqlite_file)
        else:
            uri_conn = "sqlite:///:memory:"

    # create database (if DB is not a sqlite in memory)
    if uri_conn != "sqlite:///:memory:":
        if database_exists(uri_conn):
            if overwrite:
                drop_database(uri_conn)
            else:
                raise GnucashException("'{}' db already exists".format(uri_conn))
        create_database(uri_conn)

    engine = create_engine(uri_conn, **kwargs)

    # create all (tables, fk, ...)
    DeclarativeBase.metadata.create_all(engine)

    # remove all foreign keys
    if not keep_foreign_keys:
        for fk in get_foreign_keys(DeclarativeBase.metadata, engine):
            if fk.name:
                engine.execute(DropConstraint(fk))

    # start session to create initial objects
    s = Session(bind=engine)

    # create all rows in version table
    for table_name, table_version in version_supported.items():
        s.add(Version(table_name=table_name, table_version=table_version))

    # create Book and initial accounts
    from .account import Account

    b = Book(root_account=Account(name="Root Account", type="ROOT",
                                  commodity=factories.create_currency_from_ISO(currency)),
             root_template=Account(name="Template Root", type="ROOT", commodity=None),
    )
    s.add(b)
    s.commit()

    adapt_session(s, book=b, readonly=False)

    return b


def open_book(sqlite_file=None, uri_conn=None, acquire_lock=True, readonly=True, open_if_lock=False, **kwargs):
    """Open an existing GnuCash book

    :param str sqlite_file: a path to an sqlite3 file
    :param str uri_conn: a sqlalchemy connection string
    :param bool acquire_lock: acquire a lock on the file
    :param bool readonly: open the file as readonly (useful to play with and avoid any unwanted save)
    :param bool open_if_lock: open the file even if it is locked by another user
        (using open_if_lock=True with readonly=False is not recommended)

    :return: the document as a gnucash session
    :rtype: :class:`GncSession`
    :raises GnucashException: if the document does not exist
    :raises GnucashException: if there is a lock on the file and open_if_lock is False

    """
    if uri_conn is None:
        if sqlite_file:
            uri_conn = "sqlite:///{}".format(sqlite_file)
        else:
            raise ValueError("One sqlite_file and uri_conn arguments should be given.")

    # create database (if not sqlite in memory
    if not database_exists(uri_conn):
        raise GnucashException("Database '{}' does not exist (please use create_book to create " \
                               "GnuCash books from scratch)".format(uri_conn))

    engine = create_engine(uri_conn, **kwargs)

    locks = list(engine.execute(gnclock.select()))

    # ensure the file is not locked by GnuCash itself
    if locks and not open_if_lock:
        raise GnucashException("Lock on the file")

    s = Session(bind=engine)

    # check the versions in the table versions is consistent with the API
    # TODO: improve this in the future to allow more than 1 version
    version_book = {v.table_name: v.table_version for v in s.query(Version).all()}
    for k, v in version_book.items():
        # skip GnuCash
        if k in ("Gnucash"):
            continue
        assert version_supported[k] == v, "Unsupported version for table {} : got {}, supported {}".format(k, v,
                                                                                                           version_supported[
                                                                                                               k])
    book = s.query(Book).one()
    adapt_session(s, book=book, readonly=readonly)

    return book


def adapt_session(session, book, readonly):
    """
    Change the SA session object to add some features.

    :param session: the SA session object that will be modified in place
    :param book: the gnucash singleton book linked to the SA session
    :param readonly: True if the session should not allow commits.
    :return:
    """
    # link session and book together
    book.session = session
    session.book = book

    # def new_flush(*args, **kwargs):
    # if session.dirty or session.new or session.deleted:
    #         session.rollback()
    #         raise GnucashException("You cannot change the DB, it is locked !")

    # add logic to make session readonly
    def readonly_commit(*args, **kwargs):
        # session.rollback()
        raise GnucashException("You cannot change the DB, it is locked !")

    if readonly:
        session.commit = readonly_commit

    # add logic to create/delete GnuCash locks
    def delete_lock():
        session.execute(gnclock.delete(whereclause=(gnclock.c.hostname == socket.gethostname())
                                                   and (gnclock.c.pid == os.getpid())))
        session.commit()

    session.delete_lock = delete_lock

    def create_lock():
        session.execute(gnclock.insert(values=dict(hostname=socket.gethostname(), pid=os.getpid())))
        session.commit()

    session.create_lock = create_lock


    # add logic to track if a session has been modified or not
    session._is_modified = False

    @event.listens_for(session, 'after_flush')
    def receive_after_flush(session, flush_context):
        session._is_modified = not session.is_saved

    @event.listens_for(session, 'after_commit')
    @event.listens_for(session, 'after_begin')
    @event.listens_for(session, 'after_rollback')
    def init_session_status(session, *args, **kwargs):
        session._is_modified = False

    session.__class__.is_saved = property(
        fget=lambda self: not (self._is_modified or self.dirty or self.deleted or self.new),
        doc="True if nothing has yet been changed (False otherwise)")

