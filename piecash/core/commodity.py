from __future__ import division
from __future__ import unicode_literals

import pytz

_type = type

import datetime
from decimal import Decimal

from sqlalchemy import Column, VARCHAR, INTEGER, ForeignKey, BIGINT, Index
from sqlalchemy.orm import relation
from sqlalchemy.orm.exc import MultipleResultsFound

from ._commodity_helper import quandl_fx
from .._common import CallableList, GncConversionError
from .._common import GnucashException, hybrid_property_gncnumeric
from .._declbase import DeclarativeBaseGuid
from ..sa_extra import _DateAsDateTime
from ..yahoo_client import get_latest_quote, download_quote


class GncCommodityError(GnucashException):
    pass


class GncPriceError(GnucashException):
    pass


class Price(DeclarativeBaseGuid):
    """
    A single Price for a commodity.

    Attributes:
        commodity (:class:`Commodity`): commodity to which the Price relates
        currency (:class:`Commodity`): currency in which the Price is expressed
        date (:class:`datetime.date`): date object representing the day at which the price is relevant
        source (str): source of the price
        type (str): last, ask, bid, unknown, nav
        value (:class:`decimal.Decimal`): the price itself
    """
    __tablename__ = 'prices'

    __table_args__ = {}

    # column definitions
    commodity_guid = Column('commodity_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    currency_guid = Column('currency_guid', VARCHAR(length=32), ForeignKey('commodities.guid'), nullable=False)
    date = Column('date', _DateAsDateTime(neutral_time=False), nullable=False)
    source = Column('source', VARCHAR(length=2048))
    type = Column('type', VARCHAR(length=2048))

    _value_num = Column('value_num', BIGINT(), nullable=False)
    _value_denom = Column('value_denom', BIGINT(), nullable=False)
    value = hybrid_property_gncnumeric(_value_num, _value_denom)

    # relation definitions
    commodity = relation('Commodity',
                         back_populates="prices",
                         foreign_keys=[commodity_guid],
                         )
    currency = relation('Commodity',
                        foreign_keys=[currency_guid],
                        )

    def __init__(self,
                 commodity,
                 currency,
                 date,
                 value,
                 type="unknown",
                 source="user:price"):
        self.commodity = commodity
        self.currency = currency
        assert _type(date) is datetime.date
        self.date = date
        self.value = value
        self.type = type
        self.source = source

    def __str__(self):
        return "Price<{:%Y-%m-%d} : {} {}/{}>".format(self.date,
                                                       self.value,
                                                       self.currency.mnemonic,
                                                       self.commodity.mnemonic)

    def object_to_validate(self, change):
        if change[-1] != "deleted":
            yield self

    def validate(self):
        # check uniqueness of namespace/mnemonic
        try:
            self.book.query(Price).filter_by(commodity=self.commodity,
                                             currency=self.currency,
                                             source=self.source,
                                             date=self.date).one()
        except MultipleResultsFound:
            raise ValueError("{} already exists in this book".format(self))


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

        accounts (list of :class:`piecash.core.account.Account`): list of accounts which have the commodity as commodity
        transactions (list of :class:`piecash.core.transaction.Transaction`): list of transactions which have the commodity as currency
        prices (iterator of :class:`Price`): iterator on prices related to the commodity (it is a sqlalchemy query underneath)

    """
    __tablename__ = 'commodities'

    __table_args__ = (Index('_unique_cdty',
                            'namespace', 'mnemonic',
                            unique=True,
                            mysql_length={'namespace': 200,
                                          'mnemonic': 10},
                            ),
                      )

    # column definitions
    namespace = Column('namespace', VARCHAR(length=2048), nullable=False)
    mnemonic = Column('mnemonic', VARCHAR(length=2048), nullable=False)
    fullname = Column('fullname', VARCHAR(length=2048))
    cusip = Column('cusip', VARCHAR(length=2048))
    fraction = Column('fraction', INTEGER(), nullable=False)
    quote_flag = Column('quote_flag', INTEGER(), nullable=False)
    quote_source = Column('quote_source', VARCHAR(length=2048))
    quote_tz = Column('quote_tz', VARCHAR(length=2048))

    @property
    def base_currency(self):
        b = self.book
        if b is None:
            raise GnucashException("The commodity should be linked to a session to have a 'base_currency'")

        if self.namespace == "CURRENCY":
            # get the base currency as first commodity in DB
            return b.default_currency
        else:
            # retrieve currency from quoted_currency kvp
            # TODO: recover from the web (as fallback)
            mnemonic = self.get("quoted_currency", None)
            if mnemonic:
                return b.currencies(mnemonic=mnemonic)
            else:
                raise GnucashException("The commodity '{}' has no information about its base currency. "
                                       "Add a kvp item named 'quoted_currency' with the mnemonic of the "
                                       "currency to have proper behavior".format(self.mnemonic))

    # relation definitions
    accounts = relation('Account',
                        back_populates='commodity',
                        cascade='all, delete-orphan',
                        collection_class=CallableList)
    transactions = relation('Transaction',
                            back_populates='currency',
                            cascade='all, delete-orphan',
                            collection_class=CallableList,
                            )
    prices = relation("Price",
                      back_populates='commodity',
                      foreign_keys=[Price.commodity_guid],
                      cascade='all, delete-orphan',
                      lazy="dynamic",
                      )

    def __init__(self,
                 namespace,
                 mnemonic,
                 fullname,
                 fraction=100,
                 cusip="",
                 quote_flag=0,
                 quote_source=None,
                 quote_tz='',
                 book=None):

        if quote_source is None:
            quote_source = "currency" if namespace == "CURRENCY" else "yahoo"

        if book is not None:
            book.add(self)

        self.namespace = namespace
        self.mnemonic = mnemonic
        self.fullname = fullname
        self.fraction = fraction
        self.cusip = cusip
        self.quote_flag = quote_flag
        self.quote_source = quote_source
        self.quote_tz = quote_tz

        if book is not None:
            book.flush()

    def __str__(self):
        return "Commodity<{}:{}>".format(self.namespace, self.mnemonic)

    @property
    def precision(self):
        return len(str(self.fraction)) - 1

    def currency_conversion(self, currency):
        """
        Return the latest conversion factor to convert self to currency

        Attributes:
            currency (:class:`piecash.core.commodity.Commodity`): the currency to which the Price need to be converted

        Returns:
            a Decimal that can be multiplied by an amount expressed in self.commodity to get an amount expressed in currency

        Raises:
            GncConversionError: not possible to convert self to the currency

        """
        # conversion is done from self.commodity to commodity (if possible)
        sc2c = self.prices.filter_by(currency=currency).order_by(Price.date.desc()).first()
        if sc2c:
            return sc2c.value

        # conversion is done directly from commodity to self.commodity (if possible)
        c2sc = currency.prices.filter_by(currency=self).order_by(Price.date.desc()).first()
        if c2sc:
            return Decimal(1) / c2sc.value

        raise GncConversionError("Cannot convert {} to {}".format(self, currency))

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
        if self.book is None:
            raise GncPriceError("Cannot update price for a commodity not attached to a book")

        # get last_price updated
        last_price = self.prices.order_by(Price.date.desc()).limit(1).first()

        if start_date is None:
            start_date = datetime.datetime.today().date() + datetime.timedelta(days=-7)

        if last_price:
            start_date = max(last_price.date + datetime.timedelta(days=1),
                             start_date)

        if self.namespace == "CURRENCY":
            # get reference currency (from book.root_account)
            default_currency = self.base_currency
            if default_currency == self:
                raise GncPriceError("Cannot update exchange rate for base currency")

            # through Quandl for exchange rates
            quotes = quandl_fx(self.mnemonic, default_currency.mnemonic, start_date)
            for q in quotes:
                p = Price(commodity=self,
                          currency=default_currency,
                          date=datetime.datetime.strptime(q.date, "%Y-%m-%d").date(),
                          value=str(q.rate))

        else:
            symbol = self.mnemonic
            share = get_latest_quote(symbol)
            currency = self.book.currencies(mnemonic=share.currency)
            tz = pytz.timezone(share.timezone)

            # get historical data
            for q in download_quote(
                    symbol,
                    start_date,
                    datetime.date.today(),
                    tz
            ):
                Price(commodity=self,
                      currency=currency,
                      date=q.date,
                      value=q.close,
                      type='last')

    def object_to_validate(self, change):
        if change[-1] != "deleted":
            yield self

    def validate(self):
        # check uniqueness of namespace/mnemonic
        try:
            self.book.query(Commodity).filter_by(namespace=self.namespace, mnemonic=self.mnemonic).one()
        except MultipleResultsFound:
            raise ValueError("{} already exists in this book".format(self))
