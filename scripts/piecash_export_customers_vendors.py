import argparse
import codecs

import sys

from piecash import open_book


def export_customer_vendor(book, entity, include_inactive=False):
    assert entity in ["customers", "vendors"]
    columns = "id, name, addr_name, addr_addr1, addr_addr2, addr_addr3, addr_addr4, " \
              "addr_phone, addr_fax, addr_email, notes, shipaddr_name, " \
              "shipaddr_addr1, shipaddr_addr2, shipaddr_addr3, shipaddr_addr4, " \
              "shipaddr_phone, shipaddr_fax, shipaddr_email".split(", ")
    separator = ";"
    filter_entity = (lambda e: True) if include_inactive else (lambda e:e.active)

    # open a book
    with open_book(book, open_if_lock=True) as mybook:
        return "\n".join([separator.join(getattr(v, fld,"")
                                         for fld in columns)
                          for v in getattr(mybook, entity)
                          if filter_entity(v)
                          ])

if sys.version_info.major == 2:
    out = codecs.getwriter('UTF-8')(sys.stdout)
else:
    out = sys.stdout

parser = argparse.ArgumentParser(description="""
Export customers or vendors from a GnuCash book in a format suitable for import in GnuCash.
""", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("entity",
                    help="customers or vendors")
parser.add_argument("gnucash_filename",
                    help="the name of the gnucash file")
parser.add_argument("--inactive", const=True, action="store_const",
                    help="to include inactive customer or vendors")
parser.add_argument("--out", dest="output",
                    help="filename for the output")
args = parser.parse_args()

res = export_customer_vendor(args.gnucash_filename,args.entity, args.inactive)
if args.output:
    with open(args.output, "w") as f:
        f.write(res)
else:
    print(res)
