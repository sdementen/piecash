import csv
from pathlib import Path
from piecash import open_book, GnucashException

fields = ["Date", "Number", "Description", "Amount", "Balance", "Account", "Entity"]

GNUCASH_BOOK = "../gnucash_books/simple_csv.gnucash"
CSV_EXPORT = "demo.csv"
REPORTING_YEAR = 2006

# open the book and the export file
with open_book(GNUCASH_BOOK, readonly=True, open_if_lock=True) as book:
    try:
        with Path(CSV_EXPORT).open("w", newline="") as f:
            try:
                # initialise the CSV writer
                csv_writer = csv.DictWriter(f, fieldnames=fields)
                csv_writer.writeheader()

                # iterate on all the transactions in the book
                for transaction in book.transactions:
                    # filter transactions not in REPORTING_YEAR
                    if transaction.post_date.year != REPORTING_YEAR:
                        continue

                    # strip transfer account names for multisplits
                    if len(transaction.splits) == 2:
                        # assign the two splits of the transaction
                        split_one, split_two = transaction.splits
                        transfer_account = split_two.account.fullname
                    else:
                        transfer_account = ""

                    # build the dictionary with the data of the transaction
                    data = dict(
                        zip(
                            fields,
                            [
                                transaction.post_date.strftime("%d/%m/%y"),
                                transaction.num,
                                transaction.notes,
                                split_one.value,
                                split_one.account.get_balance(),
                                transfer_account,
                                transaction.description,
                            ],
                        )
                    )
                    # write the transaction to the CSV
                    csv_writer.writerow(data)

            except PermissionError:
                print("Unexpected error")

    except PermissionError:
        print("File PermissionError:", Path(CSV_EXPORT))
