import csv
from pathlib import Path

from piecash import open_book

fields = [
    "DATE",
    "TRANSACTION VALUE",
    "DEBIT/CREDIT INDICATOR",
    "ACCOUNT",
    "ACCOUNT CODE",
    "CONTRA ACCOUNT",
    "CONTRA ACCOUNT CODE",
    "ENTRY TEXT",
]

GNUCASH_BOOK = "../gnucash_books/simple_sample.gnucash"
CSV_EXPORT = "export.csv"
REPORTING_YEAR = 2019

# open the book and the export file
with open_book(GNUCASH_BOOK, readonly=True, open_if_lock=True) as mybook, Path(CSV_EXPORT).open(
    "w", newline=""
) as f:
    # initialise the CSV writer
    csv_writer = csv.DictWriter(f, fieldnames=fields)
    csv_writer.writeheader()

    # iterate on all the transactions in the book
    for transaction in mybook.transactions:
        # filter transactions not in REPORTING_YEAR
        if transaction.post_date.year != REPORTING_YEAR:
            continue

        # handle only transactions with 2 splits
        if len(transaction.splits) != 2:
            print(
                f"skipping transaction {transaction} as it has more"
                f" than 2 splits in the transaction, dunno what to export to CSV"
            )
            continue

        # assign the two splits of the transaction
        split_one, split_two = transaction.splits
        # build the dictionary with the data of the transaction
        data = dict(
            zip(
                fields,
                [
                    transaction.post_date,
                    split_one.value,
                    split_one.is_debit,
                    split_one.account.name,
                    split_one.account.code,
                    split_two.account.name,
                    split_two.account.code,
                    transaction.description,
                ],
            )
        )
        # write the transaction to the CSV
        csv_writer.writerow(data)
