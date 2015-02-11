from piecash import GnucashException
from piecash.core._commodity_helper import run_yql
from piecash.core.commodity import GncCommodityError


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
    acc = Account(symbol, "STOCK", cdty, broker_account)
    inc_accounts = []
    if income_account:
        s = cdty.get_session()
        cur = cdty.base_currency

        for inc_acc in income_account_types.split("/"):
            sub_account_name = {
                "D": "Dividend Income",
                "CL": "Cap Gain (Long)",
                "CS": "Cap Gain (Short)",
                "I": "Interest Income",
            }[inc_acc]
            try:
                div = income_account.children.get(name=sub_account_name)
            except KeyError:
                div = Account(sub_account_name, "INCOME", cur.base_currency, income_account)
            inc_accounts.append(Account(symbol, "INCOME", cur, div))

    return acc, inc_accounts


def create_currency_from_ISO(iso_code, from_web=False):
    """
    Factory function to create a new currency from its ISO code

    Args:
        iso_code (str): the ISO code of the currency (e.g. EUR for the euro)
        from_web (bool): True to get the info from the website, False to get it from the hardcoded currency_ISO module

    Returns:
        :class:`Commodity`: the currency as a commodity object
    """
    from .commodity import Commodity

    # if self.get_session().query(Commodity).filter_by(mnemonic=iso_code).first():
    #     raise GncCommodityError("Currency '{}' already exists".format(iso_code))

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
    # self.gnc_session.add(cdty)
    return cdty

def create_stock_from_symbol(symbol):
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
