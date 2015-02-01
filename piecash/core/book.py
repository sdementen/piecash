from sqlalchemy import Column, VARCHAR, ForeignKey
from sqlalchemy.orm import relation

from .._declbase import DeclarativeBaseGuid


def option(name, to_gnc, from_gnc, default=None):
    def getter(self):
        """Return True if the book has 'Use Trading Accounts' enabled"""
        try:
            return from_gnc(self.book[name].value)
        except KeyError:
            return default

    def setter(self, value):
        if value == default:
            del self.book[name]
        else:
            self.book[name] = to_gnc(value)

    return property(getter, setter)


class Book(DeclarativeBaseGuid):
    """
    A Book represents an accounting book. A new GnuCash document contains only a single Book .

    Attributes:
        root_account (:class:`piecash.core.account.Account`): the root account of the book
        root_template (:class:`piecash.core.account.Account`): the root template of the book (usage not yet clear...)
        uri (str): connection string of the book (set by the GncSession when accessing the book)
        gnc_session (:class:`piecash.core.session.GncSession`): the GncSession encapsulating the book
        use_trading_accounts (bool): true if option "Use trading accounts" is enabled
        use_split_action_field (bool): true if option "Use Split Action Field for Number" is enabled
        RO_threshold_day (int): value of Day Threshold for Read-Only Transactions (red line)

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
                            back_populates='book',
                            foreign_keys=[root_account_guid],
    )
    root_template = relation('Account',
                             foreign_keys=[root_template_guid])

    uri = None
    gnc_session = None

    use_trading_accounts = option("options/Accounts/Use Trading Accounts",
                                  from_gnc=lambda v: v == 't',
                                  to_gnc=lambda v: 't',
                                  default=False)

    use_split_action_field = option("options/Accounts/Use Split Action Field for Number",
                                    from_gnc=lambda v: v == 't',
                                    to_gnc=lambda v: 't',
                                    default=False)

    RO_threshold_day = option("options/Accounts/Day Threshold for Read-Only Transactions (red line)",
                              from_gnc=lambda v: int(v),
                              to_gnc=lambda v: float(v),
                              default=0)

    @property
    def default_currency(self):
        return self.gnc_session.commodities[0]

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
                              placeholder=True,
                              commodity=self.default_currency,
                              parent=self.root_account)
        try:
            nspc = trading.children(name=cdty.namespace)
        except KeyError:
            nspc = Account(name=namespace,
                           type="TRADING",
                           placeholder=True,
                           commodity=self.default_currency,
                           parent=trading)
        try:
            tacc = nspc.children(name=cdty.mnemonic)
        except KeyError:
            tacc = Account(name=mnemonic,
                           type="TRADING",
                           placeholder=False,
                           commodity=cdty,
                           parent=nspc)
        return tacc


    def __init__(self, root_account, root_template):
        self.root_account = root_account
        self.root_template = root_template

    def __repr__(self):
        return "<Book {}>".format(self.uri)