import datetime
import re
from piecash import Transaction, open_book


s = open_book("multiple_Accounts.gnucash", open_if_lock=True)

regex = re.compile("^/Rental/")

# retrieve relevant transactions
transactions = [tr for tr in s.transactions  # query all transactions in the book/session and filter them on
                if (regex.search(tr.description)                            # description field matching regex
                    or any(regex.search(spl.memo) for spl in tr.splits))    # or memo field of any split of transaction
                and tr.post_date.date() >= datetime.date(2014, 11, 1)]      # and with post_date no later than begin nov.

print "Here are the transactions for the search criteria '{}':".format(regex.pattern)
for tr in transactions:
    print "- {:%Y/%m/%d} : {}".format(tr.post_date, tr.description)
    for spl in tr.splits:
        print "\t{amount}  {direction}  {account} {memo}".format(amount=abs(spl.value),
                                                                 direction="-->" if spl.value > 0 else "<--",
                                                                 account=spl.account.fullname(),
                                                                 memo=spl.memo)
