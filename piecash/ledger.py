from __future__ import unicode_literals
from .core import Transaction, Account, Commodity, Price, Book

"""original script from https://github.com/MatzeB/pygnucash/blob/master/gnucash2ledger.py by Matthias Braun matze@braunis.de
 adapted for:
 - python 3 support
 - new string formatting
"""


# def attach_ledger(cls):
#     def _process(fct):
#         cls.__ledger__ = fct

#     return _process


# @attach_ledger(Transaction)
# def ledger(tr):
#     """Return a ledger-cli alike representation of the transaction"""
#     s = ["{:%Y/%m/%d} {}{}\n".format(tr.post_date,
#                                        "({}) ".format(tr.num.replace(")", "")) if tr.num else "",
#                                        tr.description)]
#     if tr.notes:
#         s.append("\t;{}\n".format(tr.notes))
#     for split in tr.splits:
#         if split.account.commodity.mnemonic == "template":
#             return ""
#         if split.reconcile_state in ['c', 'y']:
#             s.append("\t* {:38}  ".format(split.account.fullname))
#         else:
#             s.append("\t{:40}  ".format(split.account.fullname))
#         if split.account.commodity != tr.currency:
#             s.append("{:10.{}f} {} @@ {:.{}f} {}".format(
#                 split.quantity,
#                 split.account.commodity.precision,
#                 format_commodity(split.account.commodity),
#                 abs(split.value),
#                 tr.currency.precision,
#                 format_commodity(tr.currency)))
#         else:
#             s.append("{:10.{}f} {}".format(split.value,
#                                            tr.currency.precision,
#                                            format_commodity(tr.currency)))
#         if split.memo:
#             s.append(" ;   {:20}".format(split.memo))
#         s.append("\n")

#     return "".join(s)


# def format_commodity(commodity):
#     """ Export the namespace for non-currency commodities. """
#     if commodity.namespace == "CURRENCY":
#         symbol = commodity.mnemonic
#     else:
#         # Python 3.6 syntax
#         #symbol = f"{commodity.namespace}.{commodity.mnemonic}"
#         symbol = "{}.{}".format(commodity.namespace, commodity.mnemonic)

#     try:
#         if symbol.encode('ascii').isalpha():
#             return symbol
#     except:
#         pass
#     return "\"{}\"".format(symbol)  # TODO: escape " char in symbol


# @attach_ledger(Commodity)
# def ledger(cdty):
#     """Return a ledger-cli alike representation of the commodity"""
#     if cdty.mnemonic in ["", "template"]:
#         return ""
#     res = "commodity {}\n".format(format_commodity(cdty))
#     if cdty.fullname != "":
#         res += "\tnote {}\n".format(cdty.fullname)
#     res += "\n"
#     return res


# @attach_ledger(Account)
# def ledger(acc):
#     """Return a ledger-cli alike representation of the account"""
#     # ignore "dummy" accounts
#     if acc.type is None or acc.parent is None:
#         return ""
#     if acc.commodity.mnemonic == "template":
#         return ""
#     res = "account {}\n".format(acc.fullname, )
#     if acc.description != "":
#         res += "\tnote {}\n".format(acc.description, )

#     res += "\tcheck commodity == \"{}\"\n".format(format_commodity(acc.commodity).replace("\"", "\\\""))
#     return res


# @attach_ledger(Price)
# def ledger(price):
#     """Return a ledger-cli alike representation of the price"""
#     return "P {:%Y/%m/%d %H:%M:%S} {} {} {}\n".format(price.date,
#                                                       format_commodity(price.commodity),
#                                                       price.value,
#                                                       format_commodity(price.currency))


# @attach_ledger(Book)
# def ledger(book):
#     """Return a ledger-cli alike representation of the book"""
#     res = []

#     # Commodities
#     for commodity in book.commodities:
#         res.append(ledger(commodity))

#     # Accounts
#     for acc in book.accounts:
#         res.append(ledger(acc))
#         res.append("\n")

#     # Prices
#     for price in sorted(book.prices, key=lambda x: x.date):
#         res.append(ledger(price))
#     res.append("\n")

#     # Transactions
#     for trans in sorted(book.transactions, key=lambda x: x.post_date):
#         res.append(ledger(trans))
#         res.append("\n")

#     return "".join(res)


# def ledger(obj):
#     return obj.__ledger__()


class GnuCash2LedgerParser:
    """ Parses GnuCash entities into Ledger format """
    def __init__(self):
        self._symbol_with_exchange = False

    def parse_commodity(self, commodity):
        if commodity.mnemonic in ["", "template"]:
            return ""

        res = "commodity {}\n".format(self.format_commodity(commodity))

        if commodity.fullname != "":
            res += "\tnote {}\n".format(commodity.fullname)

        res += "\n"

        return res

    def format_commodity(self, commodity: Commodity):
        """
        Format the commodity display. Currencies use only symbol.
        Other commodities can be output with or without the namespace (exchange)
        by setting the _symbol_with_exchange to True.
        """
        if not self._symbol_with_exchange or commodity.namespace == "CURRENCY":
            symbol = commodity.mnemonic
        else:
            # Python 3.6 syntax
            #symbol = f"{commodity.namespace}.{commodity.mnemonic}"
            symbol = "{}.{}".format(commodity.namespace, commodity.mnemonic)

        try:
            if symbol.encode('ascii').isalpha():
                return symbol
        except:
            pass
        return "\"{}\"".format(symbol)  # TODO: escape " char in symbol

    def parse_transaction(self, tr):
        """Return a ledger-cli alike representation of the transaction"""
        s = ["{:%Y/%m/%d} {}{}\n".format(tr.post_date,
                                        "({}) ".format(tr.num.replace(")", "")) if tr.num else "",
                                        tr.description)]
        if tr.notes:
            s.append("\t;{}\n".format(tr.notes))
        for split in tr.splits:
            if split.account.commodity.mnemonic == "template":
                return ""
            if split.reconcile_state in ['c', 'y']:
                s.append("\t* {:38}  ".format(split.account.fullname))
            else:
                s.append("\t{:40}  ".format(split.account.fullname))
            if split.account.commodity != tr.currency:
                s.append("{:10.{}f} {} @@ {:.{}f} {}".format(
                    split.quantity,
                    split.account.commodity.precision,
                    self.format_commodity(split.account.commodity),
                    abs(split.value),
                    tr.currency.precision,
                    self.format_commodity(tr.currency)))
            else:
                s.append("{:10.{}f} {}".format(split.value,
                                            tr.currency.precision,
                                            self.format_commodity(tr.currency)))
            if split.memo:
                s.append(" ;   {:20}".format(split.memo))
            s.append("\n")

        return "".join(s)

    def parse_price(self, price):
        """Return a ledger-cli alike representation of the price"""
        return "P {:%Y/%m/%d %H:%M:%S} {} {} {}\n".format(price.date,
                                                        self.format_commodity(price.commodity),
                                                        price.value,
                                                        self.format_commodity(price.currency))

    def parse_account(self, acc):
        """Return a ledger-cli alike representation of the account"""
        # ignore "dummy" accounts
        if acc.type is None or acc.parent is None:
            return ""
        if acc.commodity.mnemonic == "template":
            return ""
        res = "account {}\n".format(acc.fullname, )
        if acc.description != "":
            res += "\tnote {}\n".format(acc.description, )

        res += "\tcheck commodity == \"{}\"\n".format(
            self.format_commodity(acc.commodity).replace("\"", "\\\""))
        return res


def get_ledger_output(book, commodities=True, accounts=True, prices=True, transactions=True,
    with_exchange=False):
    """ Returns the specified parts of the book in ledger format """
    res = []

    parser = GnuCash2LedgerParser()
    parser._symbol_with_exchange = with_exchange

    # Commodities
    if commodities:
        res.append("; Commodities\n")
        for commodity in book.commodities:
            #res.append(ledger(commodity))
            res.append(parser.parse_commodity(commodity))
        res.append("\n")

    # Accounts
    if accounts:
        res.append("; Accounts\n")
        for acc in book.accounts:
            #res.append(ledger(acc))
            res.append(parser.parse_account(acc))
            res.append("\n")

    # Prices
    if prices:
        res.append("; Prices\n")
        for price in sorted(book.prices, key=lambda x: x.date):
            #res.append(ledger(price))
            res.append(parser.parse_price(price))
        res.append("\n")

    # Transactions
    if transactions:
        res.append("; Transactions\n")
        for trans in sorted(book.transactions, key=lambda x: x.post_date):
            #res.append(ledger(trans))
            res.append(parser.parse_transaction(trans))
            res.append("\n")

    return "".join(res)    
