import warnings

from sqlalchemy import Column, VARCHAR, ForeignKey
from sqlalchemy.orm import relation
from sqlalchemy.orm.exc import NoResultFound

from .._declbase import DeclarativeBaseGuid
from .._common import CallableList
from . import factories
from .commodity import Commodity


def option(name, to_gnc, from_gnc, default=None):
    def getter(self):
        try:
            return from_gnc(self.book[name].value)
        except KeyError:
            return default

    def setter(self, value):
        if value == default:
            try:
                del self[name]
            except KeyError:
                pass
        else:
            self.book[name] = to_gnc(value)

    return property(getter, setter)


class Book(DeclarativeBaseGuid):
    """
    A Book represents a GnuCash document. It is created through one of the two factory functions
    :func:`create_book` and :func:`open_book`.

    Canonical use is as a context manager like (the book is automatically closed at the end of the with block)::

        with create_book() as book:
            ...

    .. note:: If you do not use the context manager, do not forget to close the session explicitly (``book.close()``)
       to release any lock on the file/DB.

    The book puts at disposal several attributes to access the main objects of the GnuCash document::

        # to get the book and the root_account
        ra = book.root_account

        # to get the list of accounts, commodities or transactions
        for acc in book.accounts:  # or book.commodities or book.transactions
            # do something with acc

        # to get a specific element of these lists
        EUR = book.commodities(namespace="CURRENCY", mnemonic="EUR")

        # to get a list of all objects of some class (even non core classes)
        budgets = book.get(Budget)
        # or a specific object
        budget = book.get(Budget, name="my first budget")

    You can check a session has changes (new, deleted, changed objects) by getting the ``book.is_saved`` property.
    To save or cancel changes, use ``book.save()`` or ``book.cancel()``::

        # save a session if it is no saved (saving a unchanged session is a no-op)
        if not book.is_saved:
            book.save()

    Attributes:
        root_account (:class:`piecash.core.account.Account`): the root account of the book
        root_template (:class:`piecash.core.account.Account`): the root template of the book (usage not yet clear...)
        uri (str): connection string of the book (set by the GncSession when accessing the book)
        session (:class:`sqlalchemy.orm.session.Session`): the sqlalchemy session encapsulating the book
        use_trading_accounts (bool): true if option "Use trading accounts" is enabled
        use_split_action_field (bool): true if option "Use Split Action Field for Number" is enabled
        RO_threshold_day (int): value of Day Threshold for Read-Only Transactions (red line)
        control_mode (list(str)) : list of allowed non-standard operations like : "allow-root-subaccounts"
        counter_customer (int) : counter for :class:`piecash.business.person.Customer` id (link to slot "counters/gncCustomer")
        counter_vendor (int) : counter for :class:`piecash.business.person.Vendor` id (link to slot "counters/gncVendor")
        counter_employee (int) : counter for :class:`piecash.business.person.Employee` id (link to slot "counters/gncEmployee")
        counter_invoice (int) : counter for :class:`piecash.business.invoice.Invoice` id (link to slot "counters/gncInvoice")
        counter_job (int) : counter for :class:`piecash.business.invoice.Job` id (link to slot "counters/gncJob")
        counter_bill (int) : counter for :class:`piecash.business.invoice.Bill` id (link to slot "counters/gncBill")
        counter_exp_voucher (int) : counter for :class:`piecash.business.invoice.Invoice` id (link to slot "counters/gncExpVoucher")
        counter_order (int) : counter for :class:`piecash.business.invoice.Order` id (link to slot "counters/gncOrder")
    """
    __tablename__ = 'books'

    __table_args__ = {}

    # column definitions
    root_account_guid = Column('root_account_guid', VARCHAR(length=32),
                               ForeignKey('accounts.guid'), nullable=False)
    root_template_guid = Column('root_template_guid', VARCHAR(length=32),
                                ForeignKey('accounts.guid'), nullable=False)

    # relation definitions
    root_account = relation('Account',
                            # back_populates='root_book',
                            foreign_keys=[root_account_guid],
    )
    root_template = relation('Account',
                             foreign_keys=[root_template_guid])

    uri = None
    session = None

    # link options to KVP
    use_trading_accounts = option("options/Accounts/Use Trading Accounts",
                                  from_gnc=lambda v: v == 't',
                                  to_gnc=lambda v: 't',
                                  default=False)

    use_split_action_field = option("options/Accounts/Use Split Action Field for Number",
                                    from_gnc=lambda v: v == 't',
                                    to_gnc=lambda v: 't' if v else 'f',
                                    default=False)

    RO_threshold_day = option("options/Accounts/Day Threshold for Read-Only Transactions (red line)",
                              from_gnc=lambda v: int(v),
                              to_gnc=lambda v: float(v),
                              default=0)

    counter_customer = option("counters/gncCustomer", from_gnc=lambda v: int(v), to_gnc=lambda v: int(v), default=0)
    counter_vendor = option("counters/gncVendor", from_gnc=lambda v: int(v), to_gnc=lambda v: int(v), default=0)
    counter_employee = option("counters/gncEmployee", from_gnc=lambda v: int(v), to_gnc=lambda v: int(v), default=0)
    counter_invoice = option("counters/gncInvoice", from_gnc=lambda v: int(v), to_gnc=lambda v: int(v), default=0)
    counter_job = option("counters/gncJob", from_gnc=lambda v: int(v), to_gnc=lambda v: int(v), default=0)
    counter_bill = option("counters/gncBill", from_gnc=lambda v: int(v), to_gnc=lambda v: int(v), default=0)
    counter_exp_voucher = option("counters/gncExpVoucher", from_gnc=lambda v: int(v), to_gnc=lambda v: int(v), default=0)
    counter_order = option("counters/gncOrder", from_gnc=lambda v: int(v), to_gnc=lambda v: int(v), default=0)


    def __init__(self, root_account=None, root_template=None):
        self.root_account = root_account
        self.root_template = root_template

    def __unirepr__(self):
        return u"Book<{}>".format(self.uri)


    _control_mode = None

    @property
    def control_mode(self):
        if self._control_mode is None:
            self._control_mode = []
        return self._control_mode

    @property
    def default_currency(self):
        return self.session.query(Commodity).first()

    @property
    def book(self):
        warnings.warn("deprecated", DeprecationWarning)
        return self

    _trading_accounts = None

    def trading_account(self, cdty):
        """Return the trading account related to the commodity. If it does not exist and the option
        "Use Trading Accounts" is enabled, create it on the fly"""
        key = namespace, mnemonic = cdty.namespace, cdty.mnemonic
        if self._trading_accounts is None:
            self._trading_accounts = {}

        tacc = self._trading_accounts.get(key, None)
        if tacc: return tacc

        from .account import Account

        try:
            trading = self.root_account.children(name="Trading")
        except KeyError:
            trading = Account(name="Trading",
                              type="TRADING",
                              placeholder=1,
                              commodity=self.default_currency,
                              parent=self.root_account)
        try:
            nspc = trading.children(name=cdty.namespace)
        except KeyError:
            nspc = Account(name=namespace,
                           type="TRADING",
                           placeholder=1,
                           commodity=self.default_currency,
                           parent=trading)
        try:
            tacc = nspc.children(name=cdty.mnemonic)
        except KeyError:
            tacc = Account(name=mnemonic,
                           type="TRADING",
                           placeholder=0,
                           commodity=cdty,
                           parent=nspc)
        # self.flush()
        return tacc


    # add session alike functions
    def add(self, obj):
        """Add an object to the book (to be used if object not linked in any way to the book)"""
        self.session.add(obj)

    def delete(self, obj):
        """Delete an object from the book (to remove permanently an object)"""
        self.session.delete(obj)

    def save(self):
        """Save the changes to the file/DB (=commit transaction)
        """
        self.session.commit()

    def flush(self):
        """Flush the book"""
        self.session.flush()

    def cancel(self):
        """Cancel all the changes that have not been saved (=rollback transaction)
        """
        self.session.rollback()

    @property
    def is_saved(self):
        """Save the changes to the file/DB (=commit transaction)
        """
        return self.session.is_saved


    # add context manager that close the session when leaving
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close a session. Any changes not yet saved are rolled back. Any lock on the file/DB is released.
        """
        session = self.session
        # cancel pending changes
        session.rollback()
        # if self._acquire_lock:
        # # remove the lock
        # session.delete_lock()
        session.close()

    # add general getters for gnucash classes
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
            try:
                return self.session.query(cls).filter_by(**kwargs).one()
            except NoResultFound:
                raise ValueError("Could not find a {}({})".format(cls.__name__,
                                                                  kwargs))
        else:
            return self.session.query(cls)

    @property
    def transactions(self):
        """
        gives easy access to all transactions in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.core.transaction.Transaction`
        """
        from .transaction import Transaction

        return CallableList(self.session.query(Transaction))

    @property
    def accounts(self):
        """
        gives easy access to all accounts in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.core.account.Account`
        """
        from .account import Account

        return CallableList(self.session.query(Account).filter(Account.parent != None))

    @property
    def commodities(self):
        """
        gives easy access to all commodities in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.core.commodity.Commodity`
        """
        from .commodity import Commodity

        return CallableList(self.session.query(Commodity))

    @property
    def currencies(self):
        """
        gives easy access to all currencies in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.core.commodity.Commodity`
        """
        from .commodity import Commodity

        def fallback(mnemonic):
            cur = factories.create_currency_from_ISO(isocode=mnemonic)
            self.add(cur)
            # self.flush()
            return cur

        cl = CallableList(self.session.query(Commodity).filter_by(namespace="CURRENCY"))
        cl.fallback = fallback
        return cl

    @property
    def prices(self):
        """
        gives easy access to all prices in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.core.commodity.Price`
        """
        from .commodity import Price

        return CallableList(self.session.query(Price))

    @property
    def customers(self):
        """
        gives easy access to all commodities in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.business.people.Customer`
        """
        from ..business import Customer

        return CallableList(self.session.query(Customer))

    @property
    def vendors(self):
        """
        gives easy access to all commodities in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.business.people.Vendor`
        """
        from ..business import Vendor

        return CallableList(self.session.query(Vendor))

    @property
    def employees(self):
        """
        gives easy access to all commodities in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.business.people.Employee`
        """
        from ..business import Employee

        return CallableList(self.session.query(Employee))

    @property
    def taxtables(self):
        """
        gives easy access to all commodities in the book through a :class:`piecash.model_common.CallableList`
        of :class:`piecash.business.tax.Taxtable`
        """
        from ..business import Taxtable

        return CallableList(self.session.query(Taxtable))

    @property
    def query(self):
        """
        proxy for the query function of the underlying sqlalchemy session
        """
        return self.session.query
