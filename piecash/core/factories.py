# coding=utf-8
from __future__ import unicode_literals

from .._common import GnucashException
from ..yahoo_client import get_latest_quote


def create_stock_accounts(cdty, broker_account, income_account=None, income_account_types="D/CL/I"):
    """Create the multiple accounts used to track a single stock, ie:

    - broker_account/stock.mnemonic

    and the following accounts depending on the income_account_types argument

    - D = Income/Dividend Income/stock.mnemonic
    - CL = Income/Cap Gain (Long)/stock.mnemonic
    - CS = Income/Cap Gain (Short)/stock.mnemonic
    - I = Income/Interest Income/stock.mnemonic

    Args:
        broker_account (:class:`piecash.core.account.Account`): the broker account where the account holding
        the stock is to be created
        income_account (:class:`piecash.core.account.Account`): the income account where the accounts holding
        the income related to the stock are to be created
        income_account_types (str): "/" separated codes to drive the creation of income accounts

    Returns:
        :class:`piecash.core.account.Account`: a tuple with the account under the broker_account where the stock is held
        and the list of income accounts.
    """
    if cdty.namespace == "CURRENCY":
        raise GnucashException("{} is a currency ! You can't create stock_accounts for currencies".format(cdty))

    from .account import Account

    symbol = cdty.mnemonic
    try:
        acc = broker_account.children(name=symbol)
    except KeyError:
        acc = Account(symbol, "STOCK", cdty, broker_account)

    inc_accounts = []
    if income_account:
        cur = cdty.base_currency

        for inc_acc in income_account_types.split("/"):
            sub_account_name = {
                "D": "Dividend Income",
                "CL": "Cap Gain (Long)",
                "CS": "Cap Gain (Short)",
                "I": "Interest Income",
            }[inc_acc]
            try:
                sub_acc = income_account.children(name=sub_account_name)
            except KeyError:
                sub_acc = Account(sub_account_name, "INCOME", cur.base_currency, income_account)
            try:
                cdty_acc = sub_acc.children(name=symbol)
            except KeyError:
                cdty_acc = Account(symbol, "INCOME", cur, sub_acc)
            inc_accounts.append(cdty_acc)

    return acc, inc_accounts


def create_currency_from_ISO(isocode):
    """
    Factory function to create a new currency from its ISO code

    Args:
        isocode (str): the ISO code of the currency (e.g. EUR for the euro)

    Returns:
        :class:`Commodity`: the currency as a commodity object
    """
    from .commodity import Commodity

    # if self.get_session().query(Commodity).filter_by(isocode=isocode).first():
    #     raise GncCommodityError("Currency '{}' already exists".format(isocode))

    from .currency_ISO import ISO_currencies

    cur = ISO_currencies.get(isocode)

    if cur is None:
        raise ValueError("Could not find the ISO code '{}' in the ISO table".format(isocode))

    # create the currency
    cdty = Commodity(mnemonic=cur.mnemonic,
                     fullname=cur.currency,
                     fraction=10 ** int(cur.fraction),
                     cusip=cur.cusip,
                     namespace="CURRENCY",
                     quote_flag=1,
                     )

    # self.gnc_session.add(cdty)
    return cdty


def create_stock_from_symbol(symbol, book=None):
    """
    Factory function to create a new stock from its symbol. The ISO code of the quoted currency of the stock is
    stored in the slot "quoted_currency".

    Args:
        symbol (str): the symbol for the stock (e.g. YHOO for the Yahoo! stock)

    Returns:
        :class:`Commodity`: the stock as a commodity object

    .. note::
       The information is gathered from the yahoo-finance package
       The default currency in which the quote is traded is stored in a slot 'quoted_currency'

    .. todo::
       use 'select * from yahoo.finance.sectors' and 'select * from yahoo.finance.industry where id ="sector_id"'
       to retrieve name of stocks and allow therefore the creation of a stock by giving its "stock name" (or part of it).
       This could also be used to retrieve all symbols related to the same company
    """
    from .commodity import Commodity

    share = get_latest_quote(symbol)

    stock = Commodity(mnemonic=symbol,
                      fullname=share.name,
                      fraction=10000,
                      namespace=share.exchange,
                      quote_flag=1,
                      quote_source="yahoo",
                      quote_tz=share.timezone,
                      )

    if book:
        book.add(stock)
        book.flush()

    return stock


def single_transaction(post_date,
                       enter_date,
                       description,
                       value,
                       from_account,
                       to_account):
    from . import Transaction, Split
    # currency is derived from "from_account" (as in GUI)
    currency = from_account.commodity
    # currency of other destination account should be identical (as only one value given)
    assert currency == to_account.commodity, "Commodities of accounts should be the same"
    tx = Transaction(
        currency=currency,
        post_date=post_date,
        enter_date=enter_date,
        description=description,
        splits=[
            Split(account=from_account, value=-value),
            Split(account=to_account, value=value),
        ])
    return tx
