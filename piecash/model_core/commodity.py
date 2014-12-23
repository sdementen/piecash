from __future__ import division
from collections import namedtuple
import json
from xml.etree import ElementTree
import datetime

from sqlalchemy import Column, VARCHAR, INTEGER, ForeignKey, BIGINT
from sqlalchemy.orm import relation, backref

from ..model_common import GnucashException,hybrid_property_gncnumeric
from ..model_declbase import DeclarativeBaseGuid
from ..model_common import CallableList
from ..sa_extra import _DateTime


class GncCommodityError(GnucashException):
    pass


class GncPriceError(GnucashException):
    pass


def run_yql(yql, scalar=False):
    # run a yql query and return results as list or scalar
    import requests

    DATATABLES_URL = 'store://datatables.org/alltableswithkeys'
    PUBLIC_API_URL = 'http://query.yahooapis.com/v1/public/yql'
    text_result = requests.get(PUBLIC_API_URL, params={'q': yql, 'format': 'json', 'env': DATATABLES_URL}).text
    query_result = json.loads(text_result)["query"]

    if query_result["count"] == 0:
        # no results
        return None if scalar else []

    quotes = query_result["results"]["quote"]
    fields = (quotes if scalar else quotes[0]).keys()
    yql_result = namedtuple("YQL", fields)

    if scalar:
        return yql_result(**quotes)
    else:
        return [yql_result(**v) for v in quotes]


def quandl_fx(fx_mnemonic, base_mnemonic, start_date):
    """Retrieve exchange rate of commodity fx in function of base
    """
    import requests

    PUBLIC_API_URL = 'http://www.quandl.com/api/v1/datasets/CURRFX/{}{}.json'.format(fx_mnemonic, base_mnemonic)
    text_result = requests.get(PUBLIC_API_URL, params={'request_source': 'python', 'request_version': 2,
                                                       'trim_start': "{:%Y-%m-%d}".format(start_date)}).text
    query_result = json.loads(text_result)
    rows = query_result["data"]

    qdl_result = namedtuple("QUANDL", ["date", "rate", "high", "low"])

    return [qdl_result(*v) for v in rows]


class Commodity(DeclarativeBaseGuid):
    """
    A GnuCash Commodity.

    Attributes:
        cusip (str): cusip code
        fraction (int): minimal unit of the commodity (e.g. 100 for 1/100)
        namespace (str): CURRENCY for currencies, otherwise any string to group multiple commodities together
        mnemonic (str): the ISO symbol for a currency or the stock symbol for stocks (used for online quotes)
        quote_flag (int): 1 if piecash/GnuCash quotes will retrieve online quotes for the commodity
        quote_source (str): the quote source for GnuCash (piecash always use yahoo for stock and quandl for currencies
        quote_tz (str): the timezone to assign on the online quotes

        base_currency (:class:`Commodity`): The base_currency for a commodity:

          - if the commodity is a currency, returns the "default currency" of the book (ie the one of the root_account)
          - if the commodity is not a currency, returns the currency encoded in the quoted_currency slot



    """
    __tablename__ = 'commodities'

    __table_args__ = {}

    # column definitions
    cusip = Column('cusip', VARCHAR(length=2048))
    fraction = Column('fraction', INTEGER(), nullable=False, default=100)
    fullname = Column('fullname', VARCHAR(length=2048))
    mnemonic = Column('mnemonic', VARCHAR(length=2048), nullable=False)
    namespace = Column('namespace', VARCHAR(length=2048), nullable=False)
    quote_flag = Column('quote_flag', INTEGER(), nullable=False)
    quote_source = Column('quote_source', VARCHAR(length=2048))
    quote_tz = Column('quote_tz', VARCHAR(length=2048))

    @property
    def base_currency(self):
        from .book import Book

        s = self.get_session()
        if s is None:
            raise GnucashException("The commodity should be link to a session to have a 'base_currency'")

        if self.namespace == "CURRENCY":
            return s.query(Book).one().root_account.commodity
        else:
            # retrieve currency from cusip field or from the web (as fallback)
            mnemonic = self.get("quoted_currency", None)
            if mnemonic:
                currency = s.query(Commodity).filter_by(namespace="CURRENCY", mnemonic=mnemonic).first()
                if not currency:
                    currency = Commodity.create_currency_from_ISO(mnemonic)
                    s.add(currency)
                return currency
            else:
                raise GnucashException("The commodity has no information about its base currency. "
                                       "Update the cusip field to a string with 'currency=MNEMONIC' to have proper behavior")


    # relation definitions

    def __repr__(self):
        return "Commodity<{}:{}>".format(self.namespace, self.mnemonic)

    @classmethod
    def create_currency_from_ISO(cls, iso_code, from_web=False):
        """
        Factory function to create a new currency from its ISO code

        Args:
            iso_code (str): the ISO code of the currency (e.g. EUR for the euro)
            from_web (bool): True to get the info from the website, False to get it from the hardcoded currency_ISO module

        Returns:
            :class:`Commodity`: the currency as a commodity object
        """
        if not from_web:
            from .currency_ISO import ISO_currencies

            for cur in ISO_currencies:
                if cur.mnemonic == iso_code:
                    # create the currency
                    return cls(mnemonic=cur.mnemonic,
                               fullname=cur.currency,
                               fraction=10 ** int(cur.fraction),
                               cusip=cur.cusip,
                               namespace="CURRENCY",
                               quote_flag=1,
                               quote_source="currency"
                    )
            else:
                raise ValueError("Could not find the ISO code '{}' in the ISO table".format(iso_code))

        else:
            # retrieve XML table with currency information
            import requests

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
            return cls(mnemonic=iso_code,
                       fullname=fullname,
                       fraction=fraction,
                       cusip=cusip,
                       namespace="CURRENCY",
                       quote_flag=1,
                       quote_source="currency"
            )

    @classmethod
    def create_stock_from_symbol(cls, symbol):
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
        yql = 'select Name, StockExchange, Symbol,Currency from yahoo.finance.quotes where symbol = "{}"'.format(symbol)
        symbol_info = run_yql(yql, scalar=True)
        if symbol_info.StockExchange:
            stock = Commodity(mnemonic=symbol_info.Symbol,
                             fullname=symbol_info.Name,
                             fraction=10000,
                             namespace=symbol_info.StockExchange.upper(),
                             quote_flag=1,
                             quote_source="yahoo"
            )
            stock["quoted_currency"] = symbol_info.Currency
            return stock
        else:
            raise GncCommodityError("Can't find information on symbol '{}'".format(symbol))



    def update_prices(self, start_date=None):
        """
        Retrieve online prices for the commodity:

        - for currencies, it will get from quandl the exchange rates between the currency and its base_currency
        - for stocks, it will get from yahoo the daily closing prices expressed in its base_currency

        Args:
            start_date (:class:`datetime.date`): prices will be updated as of the start_date. If None, start_date is today
            - 7 days.

        .. note:: if prices are already available in the GnuCash file, the function will only retrieve prices as of the
           max(start_date, last quoted price date)

        .. todo:: add some frequency to retrieve prices only every X (week, month, ...)
        """

        last_price = self.prices.order_by(-Price.date).limit(1).first()

        if start_date is None:
            start_date = datetime.datetime.today().date() + datetime.timedelta(days=-7)

        if last_price:
            start_date = max(last_price.date.date() + datetime.timedelta(days=1),
                             start_date)

        if self.namespace == "CURRENCY":
            # get reference currency (from book.root_account)
            default_currency = self.base_currency
            if default_currency == self:
                raise GncPriceError("Cannot update exchange rate for base currency")

            # through Quandl for exchange rates
            quotes = quandl_fx(self.mnemonic, default_currency.mnemonic, start_date)

            for q in quotes:
                Price(commodity=self,
                      currency=default_currency,
                      date=datetime.datetime.strptime(q.date, "%Y-%m-%d"),
                      value=str(q.rate))
        else:
            symbol = self.mnemonic
            default_currency = self.base_currency

            # get historical data
            yql = 'select Date, Close from yahoo.finance.historicaldata where ' \
                  'symbol = "{}" ' \
                  'and startDate = "{:%Y-%m-%d}" ' \
                  'and endDate = "{:%Y-%m-%d}"'.format(symbol,
                                                       start_date,
                                                       datetime.date.today())
            for q in run_yql(yql):
                day, close = q.Date, q.Close
                Price(commodity=self,
                      currency=default_currency,
                      date=datetime.datetime.strptime(day, "%Y-%m-%d"),
                      value=close,
                      type='last')


    def create_stock_accounts(self, broker_account, income_account=None, income_account_types="D/CL/I"):
        """Create the multiple accounts used to track a single stock, ie:

        - broker_account/stock.mnemonic

        and the following accounts depending on the income_account_types argument

        - D = Income/Dividends/stock.mnemonic
        - CL = Income/Cap Gain (Long)/stock.mnemonic
        - CS = Income/Cap Gain (Short)/stock.mnemonic
        - I = Income/Interest/stock.mnemonic

        Args:
            broker_account (:class:`piecash.model_core.account.Account`): the broker account where the account holding
            the stock is to be created
            income_account (:class:`piecash.model_core.account.Account`): the income account where the accounts holding
            the income related to the stock are to be created
            income_account_types (str): "/" separated codes to drive the creation of income accounts

        Returns:
            :class:`piecash.model_core.account.Account`: the account under the broker_account where the stock is held.
        """
        if self.namespace == "CURRENCY":
            raise GnucashException("{} is a currency ! You can't create stock_accounts for currencies".format(self))

        from .account import Account

        symbol = self.mnemonic
        acc = Account(symbol, "STOCK", self, broker_account)
        if income_account:
            s = self.get_session()
            cur = self.base_currency

            for inc_acc in income_account_types.split("/"):
                sub_account_name = {
                    "D": "Dividends",
                    "CL": "Cap Gain (Long)",
                    "CS": "Cap Gain (Short)",
                    "I": "Interest",
                }[inc_acc]
                try:
                    div = income_account.children.get(name=sub_account_name)
                except KeyError:
                    div = Account(sub_account_name, "INCOME", cur.base_currency, income_account)
                Account(symbol, "INCOME", cur, div)


class Price(DeclarativeBaseGuid):
    __tablename__ = 'prices'

    __table_args__ = {}

    # column definitions
    commodity_guid = Column('commodity_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    currency_guid = Column('currency_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    date = Column('date', _DateTime, nullable=False)
    source = Column('source', VARCHAR(length=2048))
    type = Column('type', VARCHAR(length=2048))

    _value_denom = Column('value_denom', BIGINT(), nullable=False)
    _value_num = Column('value_num', BIGINT(), nullable=False)
    value = hybrid_property_gncnumeric(_value_num, _value_denom)

    # relation definitions

    commodity = relation('Commodity', foreign_keys=[commodity_guid], backref=backref("prices",
                                                                                     cascade='all, delete-orphan',
                                                                                     collection_class=CallableList,
                                                                                     lazy="dynamic"))
    currency = relation('Commodity', foreign_keys=[currency_guid])

    def __init__(self,
                 commodity,
                 currency,
                 date,
                 value,
                 type=None,
                 source="piecash"):
        self.commodity = commodity
        self.currency = currency
        assert isinstance(date, datetime.datetime)
        self.date = date
        self.value = value
        self.type = type
        self.source = source

    def __repr__(self):
        return "<Price {:%Y-%m-%d} : {} {}/{}>".format(self.date,
                                                      self.value,
                                                      self.currency.mnemonic,
                                                      self.commodity.mnemonic)