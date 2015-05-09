Creating new Business objects
-----------------------------

piecash can create new 'business' objects (this is a work in progress).

To create a new customer (a :class:`piecash.business.person.Customer`):

.. ipython:: python

    from piecash import create_book, Customer, Address

    # create a book (in memory)
    b = create_book(currency="EUR")
    # get the currency
    eur = b.default_currency

    # create a customer
    c1 = Customer(name="Mickey", currency=eur, address=Address(addr1="Sesame street 1", email="mickey@example.com"))
    # the customer has not yet an ID
    c1

    # we add it to the book
    b.add(c1)

    # flush the book
    b.flush()

    # the customer gets its ID
    print(c1)

    # or create a customer directly in a book (by specifying the book argument)
    c2 = Customer(name="Mickey", currency=eur, address=Address(addr1="Sesame street 1", email="mickey@example.com"),
                  book=b)

    # the customer gets immediately its ID
    c2

    # the counter of the ID is accessible as
    b.counter_customer

    b.save()

Similar functions are available to create new vendors (:class:`piecash.business.person.Vendor`) or employees (:class:`piecash.business.person.Employee`).

There is also the possibility to set taxtables for customers or vendors as:

.. ipython:: python

    from piecash import Taxtable, TaxtableEntry
    from decimal import Decimal

    # let us first create an account to which link a tax table entry
    acc = Account(name="MyTaxAcc", parent=b.root_account, commodity=b.currencies(mnemonic="EUR"), type="ASSET")

    # then create a table with on entry (6.5% on previous account
    tt = Taxtable(name="local taxes", entries=[
        TaxtableEntry(type="percentage",
                      amount=Decimal("6.5"),
                      account=acc),
    ])

    # and finally attach it to a customer
    c2.taxtable = tt

    b.save()

    print(b.taxtables)
