from __future__ import unicode_literals

import re
from functools import singledispatch
from locale import getdefaultlocale

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


CURRENCY_RE = re.compile("^[A-Z]{3}$")
NUMBER_RE = re.compile("[0-9\., ]")


def format_commodity(mnemonic, locale):
    if CURRENCY_RE.match(mnemonic):
        # format the commodity
        s = format_currency(0, 0, mnemonic, locale)

        # remove the non currency part and real white spaces
        return NUMBER_RE.sub("", s)
    else:
        if NUMBER_RE.search(mnemonic):
            return '"{}"'.format(mnemonic)
        else:
            return mnemonic

    return NUMBER_RE.sub("", s)


def format_currency(amount, decimals, currency, locale=False):
    if locale:
        if locale is True:
            locale = getdefaultlocale()[0]
        if Money is None:
            raise ValueError(
                f"You must install Money ('pip install money') to export to ledger in your locale '{locale}'"
            )
        return Money(amount=amount, currency=currency).format(locale)
    else:
        if Money:
            try:
                # version from Money
                return str(Money(amount=amount, currency=currency))
            except ValueError:
                # local hand made version
                return "{:.{}f} {}".format(amount, decimals, format_commodity(currency, locale))
        else:
            # local hand made version
            return "{:.{}f} {}".format(amount, decimals, currency)


@ledger.register(Transaction)
def _(tr, locale=False, **kwargs):
    """Return a ledger-cli alike representation of the transaction"""
    s = [
        "{:%Y-%m-%d} {}{}\n".format(
            tr.post_date, "({}) ".format(tr.num.replace(")", "")) if tr.num else "", tr.description
        )
    ]
    if tr.notes:
        s.append("\t;{}\n".format(tr.notes))
    for split in sorted(
        tr.splits, key=lambda split: (split.value, split.transaction_guid, split.account_guid)
    ):
        if split.account.commodity.mnemonic == "template":
            return ""
        if split.reconcile_state in ["c", "y"]:
            s.append("\t* {:38}  ".format(split.account.fullname))
        else:
            s.append("\t{:40}  ".format(split.account.fullname))
        if split.account.commodity != tr.currency:
            s.append(
                "{quantity} @@ {amount}".format(
                    quantity=format_currency(
                        split.quantity,
                        split.account.commodity.precision,
                        split.account.commodity.mnemonic,
                        locale=False,
                    ),
                    amount=format_currency(
                        abs(split.value), tr.currency.precision, tr.currency.mnemonic, locale
                    ),
                )
            )
        else:
            s.append(
                format_currency(split.value, tr.currency.precision, tr.currency.mnemonic, locale)
            )

        if split.memo:
            s.append(" ;   {:20}".format(split.memo))
        s.append("\n")

    return "".join(s)


@ledger.register(Commodity)
def _(cdty, locale=False, commodity_notes=False, **kwargs):
    """Return a ledger-cli alike representation of the commodity"""
    if cdty.mnemonic in ["", "template"]:
        return ""
    res = "commodity {}\n".format(format_commodity(cdty.mnemonic, locale))
    if cdty.fullname != "" and commodity_notes:
        res += "\tnote {}\n".format(cdty.fullname, locale)
    res += "\n"
    return res


@ledger.register(Account)
def _(acc, short_account_names=False, **kwargs):
    """Return a ledger-cli alike representation of the account"""
    # ignore "dummy" accounts
    if acc.type is None or acc.parent is None:
        return ""
    if acc.commodity.mnemonic == "template":
        return ""

    if short_account_names:
        res = "account {}\n".format(acc.name)
    else:
        res = "account {}\n".format(acc.fullname)

    if acc.description != "":
        res += "\tnote {}\n".format(acc.description)

    res += '\tcheck commodity == "{}"\n'.format(acc.commodity.mnemonic)  # .replace('"', '\\"'))
    return res


@ledger.register(Price)
def _(price, locale=False, **kwargs):
    """Return a ledger-cli alike representation of the price"""
    return "P {:%Y-%m-%d %H:%M:%S} {} {}\n".format(
        price.date,
        format_commodity(price.commodity.mnemonic, locale),
        format_currency(price.value, price.currency.precision, price.currency.mnemonic, locale),
    )


@ledger.register(Book)
def _(book, **kwargs):
    """Return a ledger-cli alike representation of the book"""
    res = []

    # Commodities
    for commodity in sorted(book.commodities, key=lambda cdty: cdty.mnemonic):
        res.append(ledger(commodity, **kwargs))

    # Accounts
    if kwargs.get("short_account_names"):  # check that no ambiguity in account names
        accounts = [acc.name for acc in book.accounts]
        if len(accounts) != len(set(accounts)):
            raise ValueError(
                "You have duplicate short names in your book. "
                "You cannot use the 'short_account_names' option."
            )
    for acc in book.accounts:
        res.append(ledger(acc, **kwargs))
        res.append("\n")

    # Prices
    for price in sorted(book.prices, key=lambda x: (x.commodity_guid, x.currency_guid, x.date)):
        res.append(ledger(price, **kwargs))
    res.append("\n")

    for trans in sorted(book.transactions, key=lambda x: (x.currency_guid, x.post_date)):
        res.append(ledger(trans, **kwargs))
        res.append("\n")

    return "".join(res)
