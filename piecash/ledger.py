from __future__ import unicode_literals

import locale
from functools import singledispatch

from .core import Transaction, Account, Commodity, Price, Book

"""original script from https://github.com/MatzeB/pygnucash/blob/master/gnucash2ledger.py by Matthias Braun matze@braunis.de
 adapted for:
 - python 3 support
 - new string formatting
"""

try:
    from money import Money
except ImportError:
    Money = None


@singledispatch
def ledger(obj, **kwargs):
    raise NotImplemented


@ledger.register(Transaction)
def _(tr, **kwargs):
    """Return a ledger-cli alike representation of the transaction"""
    s = [
        "{:%Y-%m-%d} {}{}\n".format(
            tr.post_date, "({}) ".format(tr.num.replace(")", "")) if tr.num else "", tr.description
        )
    ]
    if tr.notes:
        s.append("\t;{}\n".format(tr.notes))
    for split in tr.splits:
        if split.account.commodity.mnemonic == "template":
            return ""
        if split.reconcile_state in ["c", "y"]:
            s.append("\t* {:38}  ".format(split.account.fullname))
        else:
            s.append("\t{:40}  ".format(split.account.fullname))
        if split.account.commodity != tr.currency:
            s.append(
                "{:10.{}f} {} @@ {:.{}f} {}".format(
                    split.quantity,
                    split.account.commodity.precision,
                    format_commodity(split.account.commodity),
                    abs(split.value),
                    tr.currency.precision,
                    format_commodity(tr.currency),
                )
            )
        else:
            if kwargs.get("locale"):
                _locale = locale.getdefaultlocale()[0]
                if Money is None:
                    raise ValueError("You must install Money ('pip install money') to export to ledger in your locale '{_locale}".format(_locale=_locale))
                s.append(Money(amount=split.value, currency=format_commodity(tr.currency)).format(_locale))
            else:
                if Money:
                    # vesion from Money
                    s.append(str(Money(amount=split.value, currency=format_commodity(tr.currency))))
                else:
                    # local hand made version
                    s.append("{:10.{}f} {}".format(split.value, tr.currency.precision, format_commodity(tr.currency)))
        if split.memo:
            s.append(" ;   {:20}".format(split.memo))
        s.append("\n")

    return "".join(s)


def format_commodity(commodity):
    mnemonic = commodity.mnemonic
    try:
        if mnemonic.encode("ascii").isalpha():
            return mnemonic
    except:
        pass
    return '"{}"'.format(mnemonic)  # TODO: escape " char in mnemonic


@ledger.register(Commodity)
def _(cdty, **kwargs):
    """Return a ledger-cli alike representation of the commodity"""
    if cdty.mnemonic in ["", "template"]:
        return ""
    res = "commodity {}\n".format(format_commodity(cdty))
    if cdty.fullname != "":
        res += "\tnote {}\n".format(cdty.fullname)
    res += "\n"
    return res


@ledger.register(Account)
def _(acc, **kwargs):
    """Return a ledger-cli alike representation of the account"""
    # ignore "dummy" accounts
    if acc.type is None or acc.parent is None:
        return ""
    if acc.commodity.mnemonic == "template":
        return ""
    res = "account {}\n".format(acc.fullname)
    if acc.description != "":
        res += "\tnote {}\n".format(acc.description)

    res += '\tcheck commodity == "{}"\n'.format(format_commodity(acc.commodity).replace('"', '\\"'))
    return res


@ledger.register(Price)
def _(price, **kwargs):
    """Return a ledger-cli alike representation of the price"""
    return "P {:%Y-%m-%d %H:%M:%S} {} {} {}\n".format(
        price.date, format_commodity(price.commodity), price.value, format_commodity(price.currency)
    )


@ledger.register(Book)
def _(book, **kwargs):
    """Return a ledger-cli alike representation of the book"""
    res = []

    # Commodities
    for commodity in book.commodities:
        res.append(ledger(commodity, **kwargs))

    # Accounts
    for acc in book.accounts:
        res.append(ledger(acc, **kwargs))
        res.append("\n")

    # Prices
    for price in sorted(book.prices, key=lambda x: x.date):
        res.append(ledger(price, **kwargs))
    res.append("\n")

    for trans in sorted(book.transactions, key=lambda x: x.post_date):
        res.append(ledger(trans, **kwargs))
        res.append("\n")

    return "".join(res)
