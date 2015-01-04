import os
import socket

from sqlalchemy import event, create_engine, Column, VARCHAR, INTEGER, Table
from sqlalchemy.sql.ddl import DropConstraint
from sqlalchemy_utils import database_exists

from .book import Book
from .commodity import Commodity
from .._common import CallableList
from ..sa_extra import DeclarativeBase, get_foreign_keys, Session
from .._common import GnucashException


version_supported = {u'Gnucash-Resave': 19920, u'invoices': 3, u'books': 1, u'accounts': 1, u'slots': 3,
                     u'taxtables': 2, u'lots': 2, u'orders': 1, u'vendors': 1, u'customers': 2, u'jobs': 1,
                     u'transactions': 3, u'Gnucash': 2060400, u'budget_amounts': 1, u'billterms': 2, u'recurrences': 2,
                     u'entries': 3, u'prices': 2, u'schedxactions': 1, u'splits': 4, u'taxtable_entries': 3,
                     u'employees': 2, u'commodities': 1, u'budgets': 1}

# this is not a declarative as it is used before binding the session to an engine.
gnclock = Table(u'gnclock', DeclarativeBase.metadata,
                Column('Hostname', VARCHAR(length=255)),
                Column('PID', INTEGER()),
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

    def __repr__(self):
        return "Version<{}={}>".format(self.table_name, self.table_version)


class GncSession(object):
    """
    The GncSession represents a session to a GnuCash document. It is created through one of the two factory functions
    :func:`create_book` and :func:`open_book`.

    Canonical use is as a context manager like (the session is automatically closed at the end of the with block)::

        with create_book() as s:
            ...

    .. note:: If you do not use the context manager, do not forget to close the session explicitly (``s.close()``)
       to release any lock on the file/DB.

    The session puts at disposal several attributes to access the main objects of the GnuCash document::

        # to get the book and the root_account
        ra = s.book.root_account

        # to get the list of accounts, commodities or transactions
        for acc in s.accounts:  # or s.commodities or s.transactions
            # do something with acc

        # to get a specific element of these lists
        EUR = s.commodities(namespace="CURRENCY", mnemonic="EUR")

        # to get a list of all objects of some class (even non core classes)
        budgets = s.get(Budget)
        # or a specific object
        budget = s.get(Budget, name="my first budget")

    You can check a session has changes (new, deleted, changed objects) by getting the ``s.is_saved`` property.
    To save or cancel changes, use ``s.save()`` or ``s.cancel()``::

        # save a session if it is no saved (saving a unchanged session is a no-op)
        if not s.is_saved:
            s.save()


    .. attribute:: sa_session

        the underlying sqlalchemy session
    """
    def __init__(self, session, acquire_lock=False):
        self.sa_session = session
        self._acquire_lock = acquire_lock

        if acquire_lock:
            # set a lock
            session.execute(gnclock.insert(values=dict(Hostname=socket.gethostname(), PID=os.getpid())))
            session.commit()

        # setup tracking of session changes (see https://www.mail-archive.com/sqlalchemy@googlegroups.com/msg34201.html)
        self._is_modified = False

        @event.listens_for(session, 'after_flush')
        def receive_after_flush(session, flush_context):
            self._is_modified = not self.is_saved

        @event.listens_for(session, 'after_commit')
        @event.listens_for(session, 'after_begin')
        @event.listens_for(session, 'after_rollback')
        def init_session_status(session, *args, **kwargs):
            self._is_modified = False


    def save(self):
        """Save the changes to the file/DB (=commit transaction)
        """
        self.sa_session.commit()

    def cancel(self):
        """Cancel all the changes that have not been saved (=rollback transaction)
        """
        self.sa_session.rollback()

    def close(self):
        """Close a session. Any changes not yet saved are rolled back. Any lock on the file/DB is released.
        """
        session = self.sa_session
        # cancel pending changes
        session.rollback()

        if self._acquire_lock:
            # remove the lock
            session.execute(gnclock.delete(whereclause=(gnclock.c.Hostname == socket.gethostname())
                                                       and (gnclock.c.PID == os.getpid())))
            session.commit()

        session.close()


    @property
    def is_saved(self):
        """
        True if nothing has yet been changed (False otherwise)
        """
        s = self.sa_session
        return not (self._is_modified or s.dirty or s.deleted or s.new)

    @property
    def book(self):
        """
        the single :class:`piecash.core.book.Book` within the GnuCash session.
        """
        b = self.sa_session.query(Book).one()
        b.uri = self.sa_session.connection().engine.url
        return b

    @property
    def transactions(self):
        """
        gives easy access to all transactions (including transactions used in :class:`piecash.core.transaction.ScheduledTransaction`
        in the document through a :class:`piecash._common.CallableList` of :class:`piecash.core.transaction.Transaction`
        """
        from .transaction import Transaction
        return CallableList(self.sa_session.query(Transaction))

    @property
    def accounts(self):
        """
        gives easy access to all accounts (except root accounts) in the document through a :class:`piecash._common.CallableList`
        of :class:`piecash.core.account.Account`
        """
        from .account import Account

        return CallableList(self.sa_session.query(Account).filter(Account.type!='ROOT'))

    @property
    def commodities(self):
        """
        gives easy access to all commodities in the document through a :class:`piecash._common.CallableList`
        of :class:`piecash.core.commodity.Commodity`
        """
        from .commodity import Commodity

        return CallableList(self.sa_session.query(Commodity))

    @property
    def prices(self):
        """
        gives easy access to all commodities in the document through a :class:`piecash._common.CallableList`
        of :class:`piecash.core.commodity.Commodity`
        """
        from .commodity import Price

        return CallableList(self.sa_session.query(Price))

    @property
    def query(self):
        """
        proxy for the query function of the underlying sqlalchemy session
        """
        return self.sa_session.query

    @property
    def add(self):
        """
        proxy for the add function of the underlying sqlalchemy session
        """
        return self.sa_session.add

    def get(self, cls, **kwargs):
        """
        Generic getter for a GnuCash object in the `GncSession`. If no kwargs is given, it returns the list of all
        objects of type cls (uses the sqlalchemy session.query(cls).all()).
        Otherwise, it gets the unique object which attributes match the kwargs
        (uses the sqlalchemy session.query(cls).filter_by(\*\*kwargs).one() underneath)::

            # to get the first account with name="Income"
            inc_account = session.get(Account, name="Income")

            # to get all accounts
            accs = session.get(Account)

        Args:
            cls (class): the class of the object to retrieve (Account, Price, Budget,...)
            kwargs (dict): the attributes to filter on

        Returns:
            object: the unique object if it exists, raises exceptions otherwise
        """
        if kwargs:
            return self.sa_session.query(cls).filter_by(**kwargs).one()
        else:
            return self.sa_session.query(cls)


    def update_prices(self, start_date=None):
        """
        .. py:currentmodule:: piecash.core.commodity

        Update prices for all commodities in the book which quote_flag is True (this just calls the
        :func:`Commodity.update_prices` method of the commodities).

        """
        for c in self.commodities:
            if c.quote_flag:
                c.update_prices(start_date)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


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
                                  commodity=Commodity.create_currency_from_ISO(currency)),
             root_template=Account(name="Template Root", type="ROOT", commodity=None),
    )
    s.add(b)
    s.commit()
    return GncSession(s)


def open_book(sqlite_file=None, uri_conn=None, acquire_lock=False, readonly=True, open_if_lock=False, **kwargs):
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


    # flush is a "no op" if readonly
    if readonly:
        def new_flush(*args, **kwargs):
            if s.dirty or s.new or s.deleted:
                s.rollback()
                raise GnucashException("You cannot change the DB, it is locked !")

        def new_commit(*args, **kwargs):
            s.rollback()
            raise GnucashException("You cannot change the DB, it is locked !")

        s.commit = new_commit
        # s.flush = new_flush

    return GncSession(s, acquire_lock and not readonly)



