#!/usr/local/bin/python
"""original script from https://github.com/MatzeB/pygnucash/blob/master/gnucash2ledger.py by Matthias Braun matze@braunis.de
 adapted for:
 - python 3 support
 - new string formatting
"""

import click

import piecash
from piecash.scripts.cli import cli


@cli.command()
@click.argument("book", type=click.Path(exists=True))
@click.option("--locale/--no-locale", default=False, help="Export currency amounts using locale for currencies format")
@click.option(
    "--commodity-notes/--no-commodity-notes",
    default=True,
    help="Include the commodity_notes for the commodity (hledger does not support commodity commodity_notes",
)
@click.option(
    "--short-account-names/--no-short-account-names",
    default=False,
    help="Use the short name for the accounts instead of the full hierarchical name.",
)
@click.option(
    "--output",
    type=click.File("w", encoding="UTF-8"),
    default="-",
    help="File to which to export the data (default=stdout)",
)
def ledger(book, output, locale, commodity_notes, short_account_names):
    """Export to ledger-cli format.

    This scripts export a GnuCash BOOK to the ledget-cli format.
    """
    with piecash.open_book(book, open_if_lock=True) as data:
        output.write(piecash.ledger(data, locale=locale, commodity_notes=commodity_notes,short_account_names=short_account_names))
