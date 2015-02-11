from sqlalchemy import Column, VARCHAR, ForeignKey
from sqlalchemy.orm import relation

from .._declbase import DeclarativeBaseGuid
from piecash.core._commodity_helper import run_yql
from piecash.core.commodity import GncCommodityError


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

    def __init__(self, root_account, root_template):
        self.root_account = root_account
        self.root_template = root_template

    def __repr__(self):
        return "<Book {}>".format(self.uri)

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

    def create_currency_from_ISO(self, iso_code, from_web=False):
        """
        Factory function to create a new currency from its ISO code

        Args:
            iso_code (str): the ISO code of the currency (e.g. EUR for the euro)
            from_web (bool): True to get the info from the website, False to get it from the hardcoded currency_ISO module

        Returns:
            :class:`Commodity`: the currency as a commodity object
        """
        from .commodity import Commodity

        if self.get_session().query(Commodity).filter_by(mnemonic=iso_code).first():
            raise GncCommodityError("Currency '{}' already exists".format(iso_code))

        if not from_web:
            from .currency_ISO import ISO_currencies

            for cur in ISO_currencies:
                if cur.mnemonic == iso_code:
                    # create the currency
                    cdty = Commodity(mnemonic=cur.mnemonic,
                                     fullname=cur.currency,
                                     fraction=10 ** int(cur.fraction),
                                     cusip=cur.cusip,
                                     namespace="CURRENCY",
                                     quote_flag=1,
                    )
                    break
            else:
                raise ValueError("Could not find the ISO code '{}' in the ISO table".format(iso_code))

        else:
            # retrieve XML table with currency information
            import requests
            from xml.etree import ElementTree

            url = "http://www.currency-iso.org/dam/downloads/table_a1.xml"
            table = requests.get(url)

            # parse it with elementree
            root = ElementTree.fromstring(table.content)
            # and look for each currency item
            for i in root.findall(".//CcyNtry"):
                # if there is no iso_code, skip it
                mnemonic_node = i.find("Ccy")
                if mnemonic_node is None:
                    continue
                # if the iso_code is not the one expected, skip it
                if mnemonic_node.text != iso_code:
                    continue
                # retreive currency info from xml
                cusip = i.find("CcyNbr").text
                fraction = 10 ** int(i.find("CcyMnrUnts").text)
                fullname = i.find("CcyNm").text
                break
            else:
                # raise error if iso_code has not been found
                raise ValueError("Could not find the iso_code '{}' in the table at {}".format(iso_code, url))

            # create the currency
            cdty = Commodity(mnemonic=iso_code,
                             fullname=fullname,
                             fraction=fraction,
                             cusip=cusip,
                             namespace="CURRENCY",
                             quote_flag=1,
            )
        self.gnc_session.add(cdty)
        return cdty

    def create_stock_from_symbol(self, symbol):
        """
        Factory function to create a new stock from its symbol. The ISO code of the quoted currency of the stock is
        stored in the slot "quoted_currency".

        Args:
            symbol (str): the symbol for the stock (e.g. YHOO for the Yahoo! stock)

        Returns:
            :class:`Commodity`: the stock as a commodity object

        .. note::
           The information is gathered from a yql query to the yahoo.finance.quotes
           The default currency in which the quote is traded is stored as a slot

        .. todo::
           use 'select * from yahoo.finance.sectors' and 'select * from yahoo.finance.industry where id ="sector_id"'
           to retrieve name of stocks and allow therefore the creation of a stock by giving its "stock name" (or part of it).
           This could also be used to retrieve all symbols related to the same company
        """
        from .commodity import Commodity
        yql = 'select Name, StockExchange, Symbol,Currency from yahoo.finance.quotes where symbol = "{}"'.format(symbol)
        symbol_info = run_yql(yql, scalar=True)
        if symbol_info and symbol_info.StockExchange:
            stock = Commodity(mnemonic=symbol_info.Symbol,
                              fullname=symbol_info.Name,
                              fraction=10000,
                              namespace=symbol_info.StockExchange.upper(),
                              quote_flag=1,
            )
            stock["quoted_currency"] = symbol_info.Currency
            return stock
        else:
            raise GncCommodityError("Can't find information on symbol '{}'".format(symbol))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
