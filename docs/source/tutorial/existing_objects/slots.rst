Working with slots
------------------

With regard to slots, GnuCash objects and Frames behave as dictionaries and all values are automatically
converted back and forth to python objects:

.. ipython:: python

    import datetime, decimal

    book = create_book()

    # retrieve list of slots
    print(book.slots)

    # set slots
    book["myintkey"] = 3
    book["mystrkey"] = "hello"
    book["myboolkey"] = True
    book["mydatekey"] = datetime.datetime.today().date()
    book["mydatetimekey"] = datetime.datetime.today()
    book["mynumerickey"] = decimal.Decimal("12.34567")
    book["account"] = book.root_account

    # iterate over all slots
    for k, v in book.iteritems():
        print("slot={v} has key={k} and value={v.value} of type {t}".format(k=k,v=v,t=type(v.value)))

    # delete a slot
    del book["myintkey"]
    # delete all slots
    del book[:]

    # create a key/value in a slot frames (and create them if they do not exist)
    book["options/Accounts/Use trading accounts"]="t"
    # access a slot in frame in whatever notations
    s1=book["options/Accounts/Use trading accounts"]
    s2=book["options"]["Accounts/Use trading accounts"]
    s3=book["options/Accounts"]["Use trading accounts"]
    s4=book["options"]["Accounts"]["Use trading accounts"]
    assert s1==s2==s3==s4

Slots of type GUID use the name of the slot to do the conversion back and forth between an object and its guid. For
these slots, there is an explicit mapping between slot names and object types.
