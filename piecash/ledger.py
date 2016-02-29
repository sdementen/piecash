from __future__ import unicode_literals
from .core import Transaction, Account, Commodity, Price, Book

def attach_ledger(cls):
    def _process(fct):
        cls.__ledger__ = fct
    return _process

@attach_ledger(Transaction)
def ledger(tr):
    """Return a ledger-cli alike representation of the transaction"""
    s = ["{:%Y/%m/%d} * {}\n".format(tr.post_date, tr.description)]
    if tr.notes:
        s.append("\t;{}\n".format(tr.notes))
    for split in tr.splits:
        s.append("\t{:40} ".format(split.account.fullname))
        if split.account.commodity != tr.currency:
            s.append("{:10.2f} {} @@ {:.2f} {}".format(
                split.quantity, split.account.commodity.mnemonic, abs(split.value),
                tr.currency.mnemonic))
        else:
            s.append("{:10.2f} {}".format(split.value, tr.currency.mnemonic))
        if split.memo:
            s.append(" ;   {:20}".format(split.memo))
        s.append("\n")
    return "".join(s)


def format_commodity(commodity):
    mnemonic = commodity.mnemonic
    try:
        if mnemonic.encode('ascii').isalpha():
            return mnemonic
    except:
        pass
    return "\"{}\"" .format(mnemonic)  # TODO: escape " char in mnemonic


@attach_ledger(Commodity)
def ledger(cdty):
    """Return a ledger-cli alike representation of the commodity"""
    if cdty.mnemonic == "":
        return
    res = "commodity {}\n" .format(format_commodity(cdty))
    if cdty.fullname != "":
        res += "\tnote {}\n" .format(cdty.fullname)
    res += "\n"
    return res

@attach_ledger(Account)
def ledger(acc):
    """Return a ledger-cli alike representation of the account"""
    # ignore "dummy" accounts
    if acc.type is None or acc.parent is None:
        return
    if str(acc.commodity) == "template":
        return
    res = "account {}\n" .format(acc.fullname, )
    if acc.description != "":
        res += "\tnote {}\n" .format(acc.description,)

    res += "\tcheck commodity == \"{}\"\n" .format(acc.commodity.mnemonic)
    return res

@attach_ledger(Price)
def ledger(price):
    """Return a ledger-cli alike representation of the price"""
    return "P {:%Y/%m/%d %H:%M:%S} {} {} {}\n" .format(price.date, format_commodity(price.commodity), price.value, format_commodity(price.currency))

@attach_ledger(Book)
def ledger(book):
    """Return a ledger-cli alike representation of the book"""
    res = []

    # Commodities
    for commodity in book.commodities:
        res.append(ledger(commodity))

    # Accounts
    for acc in book.accounts:
        res.append(ledger(acc))
        res.append("\n")

    # Prices
    for price in sorted(book.prices, key=lambda x:x.date):
        res.append(ledger(price))
    res.append("\n")

    for trans in sorted(book.transactions,key=lambda x: x.post_date):
        res.append(ledger(trans))
        res.append("\n")

    return "".join(res)

def ledger(obj):
    return obj.__ledger__()
