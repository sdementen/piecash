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

