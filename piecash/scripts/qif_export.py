#!/usr/local/bin/python
"""Basic script to export QIF. Heavily untested ..."""
import sys

# https://github.com/jemmyw/Qif/blob/master/QIF_references

import click

from piecash.scripts.cli import cli


@cli.command()
@click.argument('book', type=click.Path(exists=True))
@click.option('--output', type=click.File('w'), default="-",
              help="File to which to export the data (default=stdout)")
def qif(book, output):
    """Export to QIF format.

    This scripts export a GnuCash BOOK to the QIF format.
    """
    try:
        import qifparse.qif as _qif
    except ImportError:
        _qif = None
        print("You need to install the qifparse module ('pip install qifparse')")
        sys.exit()

    import piecash

    map_gnc2qif = {
        "CASH": 'Cash',
        "BANK": 'Bank',
        "RECEIVABLE": 'Bank',
        "PAYABLE": 'Ccard',
        "MUTUAL": 'Bank',
        "CREDIT": 'Ccard',
        "ASSET": 'Oth A',
        "LIABILITY": 'Oth L',
        "TRADING": 'Oth L',
        # 'Invoice',  # Quicken for business only
        "STOCK": 'Invst',
    }

    with piecash.open_book(book, open_if_lock=True) as s:
        b = _qif.Qif()
        map = {}
        for acc in s.accounts:
            if acc.parent == s.book.root_template: continue
            elif acc.type in ["INCOME", "EXPENSE", "EQUITY"]:
                item = _qif.Category(name=acc.fullname,
                                     description=acc.description,
                                     expense=acc.type == "EXPENSE",
                                     income=acc.type == "INCOME" or acc.type == "EQUITY",
                                     )
                b.add_category(item)
            elif acc.type in map_gnc2qif:
                actype = map_gnc2qif[acc.type]
                if actype=="Invst":
                    # take parent account
                    item = _qif.Account(name=acc.fullname, account_type=actype)
                else:
                    item = _qif.Account(name=acc.fullname, account_type=actype)
                b.add_account(item)
            else:
                print("unknow {} for {}".format(acc.type, acc.fullname))

            map[acc.fullname] = item

        # print(str(b))
        def split_type(sp):
            qif_obj = map[sp.account.fullname]
            if isinstance(qif_obj, _qif.Account):
                return qif_obj.account_type
            else:
                return "Expense" if qif_obj.expense else "Income"

        def sort_split(sp):
            type = split_type(sp)
            if type=="Invst":
                return 1
            elif type in ["Expense","Income"]:
                return 2
            else:
                return 0

        tpl = s.book.root_template

        for tr in s.transactions:
            if not tr.splits or len(tr.splits)<2: continue # split empty transactions
            if tr.splits[0].account.parent==tpl: continue # skip template transactions

            splits = sorted(tr.splits, key=sort_split)
            if all(sp.account.commodity.namespace == "CURRENCY" for sp in splits):

                sp1, sp2 = splits[:2]
                item = _qif.Transaction(date=tr.post_date,
                                        num=tr.num,
                                        payee=tr.description,
                                        amount=sp1.value,
                                        memo=sp1.memo,
                                        )
                if isinstance(map[sp2.account.fullname], _qif.Account):
                    item.to_account = sp2.account.fullname
                else:
                    item.category = sp2.account.fullname

                if len(splits) > 2:
                    for sp in splits[1:]:
                        if isinstance(map[sp.account.fullname], _qif.Account):
                            asp = _qif.AmountSplit(amount=-sp.value,
                                                   memo=sp.memo,
                                                   to_account=sp.account.fullname,
                                                   )
                        else:
                            asp = _qif.AmountSplit(amount=-sp.value,
                                                   memo=sp.memo,
                                                   category=sp.account.fullname,
                                                   )
                        item.splits.append(asp)
                map[sp1.account.fullname].add_transaction(item,
                                                          header="!Type:{}".format(map[sp1.account.fullname].account_type))
            else:
                # match pattern of splits for an investment

                sp_account, sp_security, sp_others = splits[0], splits[1], splits[2:]

                assert split_type(sp_account) in ["Bank", "Cash"]
                assert split_type(sp_security) in ["Invst"]
                assert all(split_type(sp)=="Expense" for sp in sp_others)
                assert sp_security.account.parent.type=="BANK", "Security account has no parent STOCK account (aka a Brokerage account)"
                item = _qif.Investment(date=tr.post_date,
                                       action="Buy" if sp_security.quantity>0 else "Sell",
                                       security=sp_security.account.commodity.mnemonic,
                                       price=sp_security.value / sp_security.quantity,
                                       quantity=sp_security.quantity,
                                       amount=sp_security.value,
                                       commission=sum(sp.value for sp in sp_others),
                                       first_line=tr.description,
                                       to_account=sp_account.account.fullname,
                                       amount_transfer=abs(sp_account.value),
                                       )
                map[sp_security.account.fullname]\
                    .add_transaction(item, header="!Type:{}".format(split_type(sp_security)))

    output.write(str(b))
