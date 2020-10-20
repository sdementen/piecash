# -*- coding: latin-1 -*-

from pathlib import Path

import pytest

import piecash
from test_helper import book_complex

# dummy line to avoid removing unused symbols
a = book_complex

REFERENCE = Path(__file__).parent / "references"


@pytest.mark.parametrize(
    "options",
    [dict(), dict(locale=True), dict(commodity_notes=True), dict(short_account_names=True)],
)
def test_out_write(book_complex, options):
    ledger_output = piecash.ledger(book_complex, **options)

    file_name = "file_template_full" + "".join(f".{k}_{v}" for k, v in options.items()) + ".ledger"

    # to generate the first time the expected output of the test
    (REFERENCE /  file_name).write_text(ledger_output, encoding="utf-8")

    assert ledger_output == (REFERENCE / file_name).read_text(encoding="utf-8")


def test_short_account_names_raise_error_when_duplicate_account_names(book_complex):
    # no exception
    piecash.ledger(book_complex, short_account_names=True)

    # exception as two accounts have the same short name
    book_complex.accounts[0].name = book_complex.accounts[1].name
    book_complex.flush()
    with pytest.raises(
        ValueError,
        match="You have duplicate short names in your book. "
        "You cannot use the 'short_account_names' option.",
    ):
        piecash.ledger(book_complex, short_account_names=True)
