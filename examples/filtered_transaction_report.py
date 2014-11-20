import datetime
import re
from piecash import Transaction, open_book


s = open_book("book.gnucash", open_if_lock=True)

regex = re.compile("^/Rental/")

# retrieve relevant transactions
transactions = [tr for tr in s.transactions  # query all transactions in the book/session and filter them on
                if (regex.search(tr.description)                            # description field matching regex
                    or any(regex.search(spl.memo) for spl in tr.splits))    # or memo field of any split of transaction
                and tr.post_date.date() >= datetime.date(2014, 11, 1)]      # and with post_date no later than begin nov.


# output report with simple 'print'
print "Here are the transactions for the search criteria '{}':".format(regex.pattern)
for tr in transactions:
    print "- {:%Y/%m/%d} : {}".format(tr.post_date, tr.description)
    for spl in tr.splits:
        print "\t{amount}  {direction}  {account} : {memo}".format(amount=abs(spl.value),
                                                                 direction="-->" if spl.value > 0 else "<--",
                                                                 account=spl.account.fullname(),
                                                                 memo=spl.memo)

# same with jinja2 templates
try:
    import jinja2
except ImportError:
    print "\n\t*** Install jinja2 ('pip install jinja2') to test the jinja2 template version ***\n"
    jinja2 = None

if jinja2:
    env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
    print env.from_string("""
    Here are the transactions for the search criteria '{{regex.pattern}}':
    {% for tr in transactions %}
    - {{ tr.post_date.strftime("%Y/%m/%d") }} : {{ tr.description }}
      {% for spl in tr.splits %}
        {{ spl.value.__abs__() }} {% if spl.value < 0 %} --> {% else %} <-- {% endif %} {{ spl.account.fullname() }} : {{ spl.memo }}
      {% endfor %}
    {% endfor %}
    """).render(transactions=transactions,
                regex=regex)
