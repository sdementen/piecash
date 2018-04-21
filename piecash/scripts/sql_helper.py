#!/usr/bin/env python
import sqlite3

import click

import piecash
from piecash.scripts.cli import cli


@cli.command()
@click.argument('book', type=click.Path(exists=True))
@click.option('--output', type=click.File('w'), default=None,
              help="File to which to dump the sql schema (default=stdout)")
def sql_dump(book, output):
    """Dump SQL schema of the gnucash sqlite book

    """

    if output is None:
        output = open(book + ".sql", "w", encoding="UTF-8")

    con = sqlite3.connect(book)
    for line in con.iterdump():
        output.write('%s\n' % line.replace("VARCHAR(", "TEXT("))

    output.close()


@cli.command()
@click.argument('book', type=click.Path(exists=False))
def sql_create(book):
    """Create an empty book with gnucash

    """
    with piecash.create_book(book, overwrite=True,keep_foreign_keys=False) as b:
        b.save()
