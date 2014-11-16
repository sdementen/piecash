# -*- coding: utf-8 -*-
"""Python GnuCash SQL interface"""

# import metadata

# from .model_core import (
#     Book, Account,
#     Commodity,
#     Transaction, Split,
# )
#
# __version__ = metadata.version
# __author__ = metadata.authors[0]
# __license__ = metadata.license
# __copyright__ = metadata.copyright
#
# __all__ = [Book, Account, Commodity, Transaction, Split]
from .model_common import get_active_session
from .model_core import (connect_to_gnucash_book,
                         Book, Account, Transaction, Split,
                         Commodity, Price,
)

