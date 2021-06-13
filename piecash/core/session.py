import datetime
import locale
import os
import shutil
import socket
from collections import defaultdict

from sqlalchemy import event, Column, VARCHAR, INTEGER, Table, PrimaryKeyConstraint
from sqlalchemy.sql.ddl import DropConstraint, DropIndex
from sqlalchemy_utils import database_exists

from piecash.core import factories
from .book import Book
from .._common import GnucashException
from ..sa_extra import create_piecash_engine, DeclarativeBase, Session

# version of tables changed between 2.6 and 3.0
#   ('invoices', 4)
#   ('prices', 3)
#   ('slots', 4)
#   ('transactions', 4)
#   ('entries', 4)

version_supported = {
    "2.6": {
        "Gnucash": 2062100,
        "Gnucash-Resave": 19920,
        "accounts": 1,
        "billterms": 2,
        "books": 1,
        "budget_amounts": 1,
        "budgets": 1,
        "commodities": 1,
        "customers": 2,
        "employees": 2,
        "entries": 3,
        "invoices": 3,
        "jobs": 1,
        "lots": 2,
        "orders": 1,
        "prices": 2,
        "recurrences": 2,
        "schedxactions": 1,
        "slots": 3,
        "splits": 4,
        "taxtable_entries": 3,
        "taxtables": 2,
        "transactions": 3,
        "vendors": 1,
    },
    "3.0": {
        "Gnucash": 3000000,
        "Gnucash-Resave": 19920,
        "accounts": 1,
        "billterms": 2,
        "books": 1,
        "budget_amounts": 1,
        "budgets": 1,
        "commodities": 1,
        "customers": 2,
        "employees": 2,
        "entries": 4,
        "invoices": 4,
        "jobs": 1,
        "lots": 2,
        "orders": 1,
        "prices": 3,
        "recurrences": 2,
        "schedxactions": 1,
        "slots": 4,
        "splits": 4,
        "taxtable_entries": 3,
        "taxtables": 2,
        "transactions": 4,
        "vendors": 1,
    },
    "3.7": {
        "Gnucash": 3000001,
        "Gnucash-Resave": 19920,
        "accounts": 1,
        "billterms": 2,
        "books": 1,
        "budget_amounts": 1,
        "budgets": 1,
        "commodities": 1,
        "customers": 2,
        "employees": 2,
        "entries": 4,
        "invoices": 4,
        "jobs": 1,
        "lots": 2,
        "orders": 1,
        "prices": 3,
        "recurrences": 2,
        "schedxactions": 1,
        "slots": 4,
        "splits": 5,
        "taxtable_entries": 3,
        "taxtables": 2,
        "transactions": 4,
        "vendors": 1,
    },
    "4.1": {
        "Gnucash": 4000001,
        "Gnucash-Resave": 19920,
        "accounts": 1,
        "billterms": 2,
        "books": 1,
        "budget_amounts": 1,
        "budgets": 1,
        "commodities": 1,
        "customers": 2,
        "employees": 2,
        "entries": 4,
        "invoices": 4,
        "jobs": 1,
        "lots": 2,
        "orders": 1,
        "prices": 3,
        "recurrences": 2,
        "schedxactions": 1,
        "slots": 4,
        "splits": 5,
        "taxtable_entries": 3,
        "taxtables": 2,
        "transactions": 4,
        "vendors": 1,
    },
}

# this is not a declarative as it is used before binding the session to an engine.
gnclock = Table(
    u"gnclock",
    DeclarativeBase.metadata,
    Column("hostname", VARCHAR(length=255)),
    Column("pid", INTEGER()),
)


class Version(DeclarativeBase):
    """The declarative class for the 'versions' table."""

    __tablename__ = "versions"

    __table_args__ = {}

    # column definitions
    # : The name of the table
    table_name = Column(
        "table_name", VARCHAR(length=50), primary_key=True, nullable=False
    )
    #: The version for the table
    table_version = Column("table_version", INTEGER(), nullable=False)

    def __init__(self, table_name, table_version):
        self.table_name = table_name
        self.table_version = table_version

    def __str__(self):
        return "Version<{}={}>".format(self.table_name, self.table_version)


def build_uri(
    sqlite_file=None,
    uri_conn=None,
    db_type=None,
    db_user=None,
    db_password=None,
    db_name=None,
    db_host=None,
    db_port=None,
    check_same_thread=True,
):
    """Create the connection string in function of some choices.

    :param str sqlite_file: a path to an sqlite3 file (only used if uri_conn is None)
    :param str uri_conn: a sqlalchemy connection string
    :param str db_type: type of database in ["postgres","mysql"]
    :param str db_user: username of database
    :param str db_password: password for the use of database
    :param str db_name: name of database
    :param str db_host: host of database
    :param int db_port: port of database
    :param bool check_same_thread: sqlite flag that restricts connection use to the thread that created (see False for use in ipython/flask/... but read first https://docs.python.org/3/library/sqlite3.html)

    :return: the connection string
    :rtype: str
    """
    db_config = (db_type, db_host, db_port, db_name, db_user, db_password)
    db_config_isdefined = map(lambda x: x is not None, db_config[:-1])
    if any(db_config_isdefined):
        if not all(db_config_isdefined):
            raise ValueError(
                "When using db_* arguments, all must be specified : {}".format(
                    db_config
                )
            )

        uri_conn = {
            "postgres": "postgresql://{username}:{password}@{host}:{port}/{name}",
            "mysql": "mysql+pymysql://{username}:{password}@{host}:{port}/{name}?charset=utf8",
        }[db_type].format(
            username=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            name=db_name,
        )

    # db_postgres_uri = "postgresql://postgres:{pwd}@localhost:5432/foo".format(pwd=pg_password)
    # db_mysql_uri = "mysql+pymysql://travis:@localhost/foo?charset=utf8"
    # db_sqlite_uri = "sqlite:///{}".format(db_sqlite)

    if sqlite_file and uri_conn:
        raise ValueError(
            "Only one of 'sqlite_file' or 'uri_conn' argument can be defined"
        )

    if uri_conn is None:
        # fallback on sqlite
        if sqlite_file:
            if isinstance(sqlite_file, str) and sqlite_file.startswith("sqlite:///"):
                # already have the protocol specified.
                uri_conn = sqlite_file
            else:
                uri_conn = "sqlite:///{}".format(sqlite_file)
        else:
            uri_conn = "sqlite:///:memory:"
        if check_same_thread is False:
            uri_conn = uri_conn + "?check_same_thread=False"

    return uri_conn


def create_book(
    sqlite_file=None,
    uri_conn=None,
    currency="locale",
    overwrite=False,
    keep_foreign_keys=False,
    db_type=None,
    db_user=None,
    db_password=None,
    db_name=None,
    db_host=None,
    db_port=None,
    check_same_thread=True,
    pg_template="template0",
    **kwargs
):
    """Create a new empty GnuCash book. If both sqlite_file and uri_conn are None, then an "in memory" sqlite book is created.

    :param str sqlite_file: a path to an sqlite3 file (only used if uri_conn is None)
    :param str uri_conn: a sqlalchemy connection string
    :param str currency: the ISO symbol of the default currency of the book, "locale" returns local international currency symbol
    :param bool overwrite: True if book should be deleted and recreated if it exists already
    :param bool keep_foreign_keys: True if the foreign keys should be kept (may not work at all with GnuCash)
    :param str db_type: type of database in ["postgres","mysql"]
    :param str db_user: username of database
    :param str db_password: password for the use of database
    :param str db_name: name of database
    :param str db_host: host of database
    :param int db_port: port of database
    :param bool check_same_thread: sqlite flag that restricts connection use to the thread that created (see False for use in ipython/flask/... but read first https://docs.python.org/3/library/sqlite3.html)
    :param str pg_template: the postgres template to use when creating the database. One of template1 or template0 (default template0). Irrelevant for other databases than postgres.
    :return: the document as a gnucash session
    :rtype: :class:`GncSession`

    :raises GnucashException: if document already exists and overwrite is False
    """
    from sqlalchemy_utils.functions import (
        database_exists,
        create_database,
        drop_database,
    )

    VERSION_FORMAT = "3.0"

    uri_conn = build_uri(
        sqlite_file,
        uri_conn,
        db_type,
        db_user,
        db_password,
        db_name,
        db_host,
        db_port,
        check_same_thread,
    )

    # create database (if DB is not a sqlite in memory)
    if uri_conn != "sqlite:///:memory:":
        if database_exists(uri_conn):
            if overwrite:
                drop_database(uri_conn)
            else:
                raise GnucashException("'{}' db already exists".format(uri_conn))
        create_database(uri_conn, template=pg_template)

    engine = create_piecash_engine(uri_conn, **kwargs)

    # drop constraints if we de not want to keep them (keep_foreign_keys=False), the default
    if not keep_foreign_keys:
        for n, tbl in DeclarativeBase.metadata.tables.items():
            # drop index constraints
            for idx in tbl.indexes:
                if idx.name.startswith("ix_") or idx.name.startswith("_"):
                    event.listen(tbl, "after_create", DropIndex(idx), once=True)
            # drop FK constraints
            for cstr in tbl.constraints:
                if isinstance(cstr, PrimaryKeyConstraint):
                    continue
                else:
                    event.listen(tbl, "before_drop", DropConstraint(cstr), once=True)
    #
    # create all (tables, fk, ...)
    DeclarativeBase.metadata.create_all(engine)

    s = Session(bind=engine)

    # create all rows in version table
    assert (
        VERSION_FORMAT in version_supported
    ), "The 'version_format'={} is not supported. " "Choose one of {}".format(
        VERSION_FORMAT, list(version_supported.keys())
    )
    for table_name, table_version in version_supported[VERSION_FORMAT].items():
        s.add(Version(table_name=table_name, table_version=table_version))

    # create book and merge with session

    b = Book()
    s.add(b)
    adapt_session(s, book=b, readonly=False)

    # create commodities and initial accounts
    from .account import Account
    
    if currency == "locale":
        locale.setlocale(locale.LC_ALL, '')
        currency = locale.localeconv()['int_curr_symbol']

    b.root_account = Account(
        name="Root Account",
        type="ROOT",
        commodity=factories.create_currency_from_ISO(currency),
        book=b,
    )
    b.root_template = Account(name="Template Root", type="ROOT", commodity=None, book=b)
    b.save()

    return b


def open_book(
    sqlite_file=None,
    uri_conn=None,
    readonly=True,
    open_if_lock=False,
    do_backup=True,
    db_type=None,
    db_user=None,
    db_password=None,
    db_name=None,
    db_host=None,
    db_port=None,
    check_same_thread=True,
    check_exists=True,
    **kwargs
):
    """Open an existing GnuCash book

    :param str sqlite_file: a path to an sqlite3 file (only used if uri_conn is None)
    :param str uri_conn: a sqlalchemy connection string
    :param bool readonly: open the file as readonly (useful to play with and avoid any unwanted save)
    :param bool open_if_lock: open the file even if it is locked by another user
        (using open_if_lock=True with readonly=False is not recommended)
    :param bool do_backup: do a backup if the file written in RW (i.e. readonly=False)
        (this only works with the sqlite backend and copy the file with .{:%Y%m%d%H%M%S}.gnucash appended to it)
    :param str db_type: type of database in ["postgres","mysql"]
    :param str db_user: username of database
    :param str db_password: password for the use of database
    :param str db_name: name of database
    :param str db_host: host of database
    :param str db_port: port of database
    :param bool check_same_thread: sqlite flag that restricts connection use to the thread that created (see False for use in ipython/flask/... but read first https://docs.python.org/3/library/sqlite3.html)
    :param bool check_exists: check if the database exists before connecting

    :return: the document as a gnucash session
    :rtype: :class:`GncSession`
    :raises GnucashException: if the document does not exist
    :raises GnucashException: if there is a lock on the file and open_if_lock is False

    """
    uri_conn = build_uri(
        sqlite_file,
        uri_conn,
        db_type,
        db_user,
        db_password,
        db_name,
        db_host,
        db_port,
        check_same_thread,
    )

    if uri_conn == "sqlite:///:memory:":
        raise ValueError(
            "An in memory sqlite gnucash databook cannot be opened, it should be created"
        )

    # check if the database exists
    if check_exists and not database_exists(uri_conn):
        raise GnucashException(
            "Database '{}' does not exist (please use create_book to create "
            "GnuCash books from scratch). If you want to bypass this existence check, "
            "use the argument check_exists=False.".format(uri_conn)
        )

    engine = create_piecash_engine(uri_conn, **kwargs)

    # backup database if readonly=False and do_backup=True
    if not readonly and do_backup:
        if engine.name != "sqlite":
            raise GnucashException(
                "Cannot do a backup for engine '{}'. Do yourself a backup and then specify do_backup=False".format(
                    engine.name
                )
            )

        url = uri_conn[len("sqlite:///") :].replace("?check_same_thread=False", "")
        url_backup = url + ".{:%Y%m%d%H%M%S}.gnucash".format(datetime.datetime.now())

        shutil.copyfile(url, url_backup)

    locks = list(engine.execute(gnclock.select()))

    # ensure the file is not locked by GnuCash itself
    if locks and not open_if_lock:
        raise GnucashException("Lock on the file")

    s = Session(bind=engine)

    # check the versions in the table versions is consistent with the API
    version_book = {
        v.table_name: v.table_version
        for v in s.query(Version).all()
        if "Gnucash" not in v.table_name
    }
    for version, vt in version_supported.items():
        if version_book == {k: v for k, v in vt.items() if "Gnucash" not in k}:
            break
    else:
        raise ValueError("Unsupported table versions")
    assert version == "3.0" or version == "3.7" or version == "4.1", (
        "This version of piecash only support books from gnucash (3.0|3.7|4.1) "
        "which is not the case for {}".format(uri_conn)
    )

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
    book.uri = session.bind.url

    # def new_flush(*args, **kwargs):
    # if session.dirty or session.new or session.deleted:
    # session.rollback()
    # raise GnucashException("You cannot change the DB, it is locked !")

    # add logic to make session readonly
    def readonly_commit(*args, **kwargs):
        # session.rollback()
        raise GnucashException("You cannot change the DB, it was opened as readonly!")

    if readonly:
        session.commit = readonly_commit

    # add logic to create/delete GnuCash locks
    def delete_lock():
        session.execute(
            gnclock.delete(
                whereclause=(gnclock.c.hostname == socket.gethostname())
                and (gnclock.c.pid == os.getpid())
            )
        )
        session.commit()

    session.delete_lock = delete_lock

    def create_lock():
        session.execute(
            gnclock.insert(values=dict(hostname=socket.gethostname(), pid=os.getpid()))
        )
        session.commit()

    session.create_lock = create_lock

    # add logic to track if a session has been modified or not
    session._is_modified = False
    session._all_changes = {}

    @event.listens_for(session, "after_flush")
    def receive_after_flush(session, flush_context):
        session._is_modified = not session.is_saved

    @event.listens_for(session, "after_commit")
    @event.listens_for(session, "after_rollback")
    def init_session_status(session, *args, **kwargs):
        session._is_modified = False
        session._all_changes.clear()

    session.book.session_changes = defaultdict(list)

    session.__class__.is_saved = property(
        fget=lambda self: not (
            self._is_modified or self.dirty or self.deleted or self.new
        ),
        doc="True if nothing has yet been changed (False otherwise)",
    )


event.listen(Session, "before_commit", Book.validate_book)
event.listen(Session, "before_flush", Book.track_dirty)
