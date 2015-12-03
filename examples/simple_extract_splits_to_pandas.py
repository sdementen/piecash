from piecash import open_book

# open a book
with open_book("../gnucash_books/simple_sample.gnucash", open_if_lock=True) as mybook:
    # print all splits in account "Asset"
    asset = mybook.accounts(fullname="Asset")
    for split in asset.splits:
        print(split)

    # extract all split information to a pandas DataFrame
    df = mybook.splits_df()

    # print for account "Asset" some information on the splits
    print(df.loc[df["account.fullname"] == "Asset", ["transaction.post_date", "value"]])
