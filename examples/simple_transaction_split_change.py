from piecash import open_book, ledger, Split

# open a book
with open_book(
    "../gnucash_books/simple_sample.gnucash", readonly=True, open_if_lock=True
) as mybook:
    # iterate on all the transactions in the book
    for transaction in mybook.transactions:
        # add some extra text to the transaction description
        transaction.description = (
            transaction.description + " (some extra info added to the description)"
        )
        # iterate over all the splits of the transaction
        # as we will modify the transaction splits in the loop,
        # we need to use list(...) to take a copy of the splits at the start of the loop
        for split in list(transaction.splits):
            # create the new split (here a copy of the each existing split
            # in the transaction with value/quantity divided by 10)
            new_split = Split(
                account=split.account,
                value=split.value / 10,
                quantity=split.quantity / 10,
                memo="my new split",
                transaction=transaction,  # attach the split to the current transaction
            )
    # register the changes (but not save)
    mybook.flush()

    # print the book in ledger format to view the changes
    print(ledger(mybook))

    # save the book
    # this will raise an error as readonly=True (change to readonly=False to successfully save the book)
    mybook.save()
