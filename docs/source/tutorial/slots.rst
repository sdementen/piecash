Working with slots
==================

With regard to slots, GnuCash objects and Frames behave as dictionaries and all values are automatically
converted back and forth to python objects::

    with create_book() as s:
        # retrieve list of slots
        print(s.book.slots)

        # set slots
        s.book["myintkey"] = 3
        s.book["mystrkey"] = "hello"
        s.book["myboolkey"] = True
        s.book["mydatekey"] = datetime.datetime.today().date()
        s.book["mydatetimekey"] = datetime.datetime.today()
        s.book["mynumerickey"] = decimal.Decimal("12.34567")
        s.book["account"] = s.book.root_account

        # iterate over all slots
        for k, v in s.book.iteritems():
            print("slot={v} has key={k} and value={v.value} of type {t}".format(k=k,v=v,t=type(v.value)))

        # delete a slot
        del s.book["myintkey"]
        # delete all slots
        del s.book[:]

        # create a key/value in a slot frames (and create them if they do not exist)
        s.book["options/Accounts/Use trading accounts"]="t"
        # access a slot in frame in whatever notations
        s1=s.book["options/Accounts/Use trading accounts"]
        s2=s.book["options"]["Accounts/Use trading accounts"]
        s3=s.book["options/Accounts"]["Use trading accounts"]
        s4=s.book["options"]["Accounts"]["Use trading accounts"]
        assert s1==s2==s3==s4
