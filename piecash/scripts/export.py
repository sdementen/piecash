#!/usr/bin/env python

import click

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('book', type=click.Path(exists=True))
@click.argument('entities', type=click.Choice(['customers', 'vendors']))
@click.option('--output', type=click.File('w'), default="-",
              help="File to which to export the data (default=stdout)")
@click.option('--inactive', is_flag=True, default=False,
              help="Include inactive entities")
@click.option('--separator', is_flag=True, default=False,
              help="Include inactive entities")
def cli(book, entities, output, inactive):
    """This script exports all ENTITIES from the BOOK in a CSV format that can be used to import in GnuCash.

    remark: this format does not include the header"""
    from piecash import open_book


    columns = "id, name, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4, " \
              "addr_phone, addr_fax, addr_email, notes, shipaddr_name, " \
              "shipaddr_addr1, shipaddr_addr2, shipaddr_addr3, shipaddr_addr4, " \
              "shipaddr_phone, shipaddr_fax, shipaddr_email".split(", ")
    separator = ";"

    filter_entity = (lambda e: True) if inactive else (lambda e: e.active)

    # open the book
    with open_book(book, open_if_lock=True) as mybook:
        res = "\n".join([separator.join(getattr(v, fld, "")
                                        for fld in columns)
                         for v in getattr(mybook, entities)
                         if filter_entity(v)
                         ])

    output.write(res)


if __name__ == '__main__':
    cli()
