#!/usr/bin/env python

import click

from piecash.scripts.cli import cli


@cli.command()
@click.argument('book', type=click.Path(exists=True))
@click.argument('entities', type=click.Choice(['customers', 'vendors', 'prices']))
@click.option('--output', type=click.File('w'), default="-",
              help="File to which to export the data (default=stdout)")
@click.option('--inactive', is_flag=True, default=False,
              help="Include inactive entities (for vendors and customers)")
def export(book, entities, output, inactive):
    """Exports GnuCash ENTITIES.

    This scripts export ENTITIES from the BOOK in a CSV format.
    When possible, it exports in a format that can be used to import the data into GnuCash.

    \b
    Remarks:
    - for customers and vendors, the format does not include an header
    - for prices, the format can be used with the `piecash import` command.
    """
    from piecash import open_book

    with open_book(book, open_if_lock=True) as book:
        if entities == "prices":
            output.write("date,type,value,value_num, value_denom, currency,commodity,source\n")
            output.writelines(
                "{p.date:%Y-%m-%d},{p.type},{p.value},{p._value_num},{p._value_denom},{p.currency.mnemonic},{p.commodity.mnemonic},{p.source}\n".format(
                    p=p) for p in book.prices)

        elif entities in ["customers", "vendors"]:
            columns = "id, name, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4, " \
                      "addr_phone, addr_fax, addr_email, notes, shipaddr_name, " \
                      "shipaddr_addr1, shipaddr_addr2, shipaddr_addr3, shipaddr_addr4, " \
                      "shipaddr_phone, shipaddr_fax, shipaddr_email".split(", ")
            separator = ";"

            filter_entity = (lambda e: True) if inactive else (lambda e: e.active)

            # open the book
            res = "\n".join([separator.join(getattr(v, fld, "")
                                            for fld in columns)
                             for v in getattr(book, entities)
                             if filter_entity(v)
                             ])

            output.write(res)
