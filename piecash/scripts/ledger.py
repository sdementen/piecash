#!/usr/local/bin/python
"""original script from https://github.com/MatzeB/pygnucash/blob/master/gnucash2ledger.py by Matthias Braun matze@braunis.de
 adapted for:
 - python 3 support
 - new string formatting
"""
import argparse
import sys
import codecs

import piecash


import click

from piecash.scripts.cli import cli


@cli.command()
@click.argument('book', type=click.Path(exists=True))
@click.option('--output', type=click.File('w', encoding="utf-8"), default="-",
              help="File to which to export the data (default=stdout)")
@click.option('--commodities', default=False, is_flag=True)
@click.option('--accounts', default=False, is_flag=True)
@click.option('--prices', default=False, is_flag=True)
@click.option('--transactions', default=False, is_flag=True)
def ledger(book, output, commodities, accounts, prices, transactions):
    """
    Export to ledger-cli format.
    This scripts export a GnuCash BOOK to the ledget-cli format.
    """
    # If none of the parts are specified, return all. 
    if (commodities or accounts or prices or transactions) == False:
        commodities = True
        accounts = True
        prices = True
        transactions = True

    with piecash.open_book(book, open_if_lock=True) as data:
        #output.write(piecash.ledger(data, commodities))
        result = piecash.get_ledger_output(data, commodities, accounts, prices, transactions)
        output.write(result)
