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
@click.option('--output', type=click.File('w'), default="-",
              help="File to which to export the data (default=stdout)")
def ledger(book, output):
    """Export to ledger-cli format.

    This scripts export a GnuCash BOOK to the ledget-cli format.
    """
    with piecash.open_book(book, open_if_lock=True) as data:
        output.write(piecash.ledger(data))
